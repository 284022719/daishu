"""把标题底图从"水墨"真正转成"平涂插画"（与 main_bg 成套）。

为什么要再加一档强度：
  d0.40 是"保构图"档 —— 实测它**保存了水墨构图**，所以画风其实没真变（仍是水墨）。
  要让标题与主界面成套，需要**更高强度**去真正改变渲染风格。
  但强度高了会破坏构图（0.55 已见桌面结构糊掉），所以要**同时量两个指标**：
    ① 画风是否靠近 main_bg（style 比值）
    ② 标题安全区（横向33.5~66.5% × 纵向3.4~32.4%）的细节量是否够低
       —— 书法字压上去要能读清，参照：main.png 该区域亮度相邻差 1.76

输出 0.55 / 0.70 / 0.85 三档，用判据挑，而不是目视拍板。
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
OUT = r'D:\dsh\tmp\title_flat'
SRC = r'D:\个人项目\daishu\assets\images\backgrounds\main.png'
os.makedirs(OUT, exist_ok=True)

PROMPT = ('flat illustration, clean flat colour shapes, warm brown beige and soft green palette, '
          'Ming dynasty riverside market town at dawn, wooden shopfronts, cloth awnings, '
          'a stone arch bridge in the distance, calm pale sky occupying the upper centre, '
          'gentle warm light, minimal shading, storybook background art, '
          'no text, no writing, no watermark, no people in the foreground')
NEGATIVE = ('text, letters, characters, words, writing, handwriting, calligraphy, script, '
            'inscription, chinese characters, kanji, hanzi, seal, stamp, wax seal, signature, '
            'watermark, logo, brand, poster, newspaper, hanging scroll, shop sign, '
            'person in foreground, portrait, large face, '
            'ink wash, watercolour wash, splatter, photorealistic, photograph, 3d render, '
            'blurry, noise, jpeg artifacts, low quality, purple fringing, dark, gloomy, clutter')
DS = [0.55, 0.70, 0.85]


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
        get_json('/sdapi/v1/sd-models', 60)
    except Exception:
        pass
    post('/sdapi/v1/options', {'sd_model_checkpoint': fname}, timeout=900)
    for _ in range(120):
        try:
            cur = get_json('/sdapi/v1/options', 30).get('sd_model_checkpoint', '')
        except Exception:
            cur = ''
        if fname in cur:
            log('[model] ✅ %s' % cur)
            return True
        time.sleep(3)
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
        src_b64 = base64.b64encode(f.read()).decode('ascii')
    try:
        if not switch_model('3Guofeng3_v34.safetensors'):
            log('[abort] 底模未确认')
            return 1
        for d in DS:
            payload = {'init_images': [src_b64], 'prompt': PROMPT, 'negative_prompt': NEGATIVE,
                       'denoising_strength': d, 'steps': 30, 'cfg_scale': 7.0, 'seed': 707070,
                       'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
                       'width': 1152, 'height': 648, 'send_images': True, 'save_images': False}
            t0 = time.time()
            try:
                res = post('/sdapi/v1/img2img', payload)
            except Exception as e:
                log('[i2i] d=%.2f 失败 %s' % (d, str(e)[:110]))
                continue
            for b64 in res.get('images', []):
                p = os.path.join(OUT, 'flat_d%02d.png' % int(d * 100))
                with open(p, 'wb') as f:
                    f.write(base64.b64decode(b64))
                log('[out] %s  %d B  (%.0fs)' % (os.path.basename(p), os.path.getsize(p), time.time() - t0))
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
