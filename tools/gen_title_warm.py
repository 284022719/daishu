"""标题底图成套：用**插画向底模**把 main.png 从水墨转成暖色平涂（与 main_bg 成套）。

为什么这次才可能成：
  前几轮我拿**写实向**底模（3Guofeng3_v34，SD1.5）做 img2img —— 实测**画风根本没变**
  （d0.40 保住了水墨构图 ⇒ 还是水墨）。上一轮确认了"**画风由底模决定**"
  （同一句 flat illustration：3Guofeng3 出照片、Illustrious-XL 出平涂）。
  ⇒ 本轮换成 **Illustrious-XL** 做 img2img。

成套的量化判据（不是感觉）：
  main.png     平均色 #918b73  暖度 +30   ← 偏灰冷，这就是"跳"的原因
  main_bg.png  平均色 #ac7d57  暖度 +85   ← 主界面，要往它靠
  letter.png   平均色 #f9dea0  暖度 +89
  ⇒ 目标：暖度显著上升、靠向 +85 量级。

标题页硬约束（title_screen.tscn，stretch_mode=0 会被拉伸）：
  必须 **16:9**；标题「代书」占 **y 3.4%~32.4%**、三个按钮占 **正中 y 36%~64%**
  ⇒ 这两块要低细节，否则字压上去看不清。
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request

LAUNCHER = r'D:\绘世启动器'
PY = os.path.join(LAUNCHER, '.ext', 'python.exe')
API = 'http://127.0.0.1:7860'
OUT = r'D:\dsh\tmp\title_warm'
SRC = r'D:\个人项目\daishu\assets\images\backgrounds\main.png'
os.makedirs(OUT, exist_ok=True)

# 风格段：往 main_bg（暖棕米色平涂）靠
STYLE = ('flat 2d illustration, clean flat colour shapes, warm brown and beige muted palette, '
         'like a warm storybook background, soft afternoon light, minimal shading, low contrast, '
         'the centre and upper part of the image stays calm and simple')
NEGATIVE = ('text, letters, characters, words, writing, handwriting, calligraphy, script, '
            'inscription, chinese characters, kanji, hanzi, seal, stamp, wax seal, signature, '
            'watermark, logo, brand, shop sign, signboard, signs, hanging scroll, plaque, '
            'banner, flag, lantern with writing, poster, newspaper, '
            'person, people, human, face, portrait, crowd, '
            'grey, greyish, desaturated grey, cold tones, blue tint, green tint, '
            'ink wash, watercolour wash, splatter, photorealistic, photograph, 3d render, '
            'blurry, noise, jpeg artifacts, low quality, dark, gloomy, cluttered, busy detail')
DS = [0.55, 0.70, 0.85]
SEED = 5150


def log(m):
    print(m, flush=True)


def get_json(path, timeout=60):
    with urllib.request.urlopen(API + path, timeout=timeout) as r:
        b = r.read().decode('utf-8')
    return json.loads(b) if b.strip() else {}


def post(path, payload, timeout=1800):
    req = urllib.request.Request(API + path, data=json.dumps(payload).encode('utf-8'),
                                headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read().decode('utf-8')
    return json.loads(b) if b.strip() else {}


def api_up():
    try:
        urllib.request.urlopen(API + '/sdapi/v1/options', timeout=8).read()
        return True
    except Exception:
        return False


def start_server():
    env = dict(os.environ)
    for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy'):
        env.pop(k, None)
    for k in ('NO_PROXY', 'no_proxy'):
        env[k] = '127.0.0.1,localhost,::1'
    env.update({'PYTHON': PY, 'VENV_DIR': '-', 'SKIP_VENV': '1', 'PYTHONIOENCODING': 'utf-8',
                'COMMANDLINE_ARGS': '--api --listen --port 7860 --medvram --xformers --no-half-vae --skip-version-check'})
    lf = open(os.path.join(OUT, 'server.log'), 'w', encoding='utf-8', errors='replace')
    p = subprocess.Popen([PY, 'launch.py'], cwd=LAUNCHER, env=env, stdout=lf, stderr=subprocess.STDOUT)
    log('[srv] 启动 PID %d' % p.pid)
    return p


def wait_ready(limit=600):
    t0 = time.time()
    while time.time() - t0 < limit:
        if api_up():
            log('[srv] 就绪 %.0fs' % (time.time() - t0))
            return True
        time.sleep(5)
    return False


def switch_model(fname):
    try:
        get_json('/sdapi/v1/sd-models', 60)      # 预热，避免 dictionary changed size
    except Exception:
        pass
    post('/sdapi/v1/options', {'sd_model_checkpoint': fname}, timeout=900)
    for _ in range(150):
        try:
            cur = get_json('/sdapi/v1/options', 30).get('sd_model_checkpoint', '')
        except Exception:
            cur = ''
        if fname in cur:
            log('[model] ✅ %s' % cur)
            return True
        time.sleep(3)
    log('[model] ⚠️ %s' % cur)
    return False


def main():
    proc = None
    if not api_up():
        proc = start_server()
        if not wait_ready():
            if proc:
                proc.terminate()
            return 1
    with open(SRC, 'rb') as f:
        src = base64.b64encode(f.read()).decode('ascii')
    log('[src] %s（水墨；往暖色平涂转）' % os.path.basename(SRC))
    try:
        if not switch_model('Illustrious-XL-v2.0.safetensors'):
            log('[abort] 底模未确认')
            return 1
        for d in DS:
            payload = {'init_images': [src], 'prompt': STYLE, 'negative_prompt': NEGATIVE,
                       'denoising_strength': d, 'steps': 30, 'cfg_scale': 6.5, 'seed': SEED,
                       'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
                       'width': 1152, 'height': 648, 'send_images': True, 'save_images': False}
            t0 = time.time()
            try:
                res = post('/sdapi/v1/img2img', payload)
            except Exception as e:
                log('[i2i] d=%.2f 失败 %s' % (d, str(e)[:120]))
                continue
            for b64 in res.get('images', []):
                p = os.path.join(OUT, 'title_d%02d.png' % int(d * 100))
                with open(p, 'wb') as f:
                    f.write(base64.b64decode(b64))
                log('[out] %-16s %d B (%.0fs)' % (os.path.basename(p), os.path.getsize(p), time.time() - t0))
    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except Exception:
                proc.kill()
    log('[done]')
    return 0


if __name__ == '__main__':
    sys.exit(main())
