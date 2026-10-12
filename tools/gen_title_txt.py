"""标题底图：**从零生成**（不靠 img2img 转风格）。

为什么放弃 img2img：
  实测 title_d85（denoise 0.85）**数值全对但画面崩了** —— 暖度 +84（目标 +85）、
  标题区细节 1.81、暗像素 0.019，可画面只剩几块抽象色块，**场景没了**。
  根因：为了"变暖"必须高重绘强度，而高重绘强度会连带丢掉内容。
  这已经是本项目判据被"数值好看"骗过的**第三个实例**（前两个：三个动漫人物拿最高分、
  暖色版只剩树与色块）—— 见 ART_METHOD_FINDINGS.md §三。

  ⇒ 改用 txt2img：上一轮已实测 **Illustrious-XL 不加任何约束就出平涂插画**，
     所以"画风"交给底模，"题材与构图"交给提示词。这正是它擅长的。

标题页硬约束（title_screen.tscn，stretch_mode=0 会拉伸）：
  必须 16:9；标题「代书」占 y 3.4%~32.4%、按钮占正中 y 36%~64% ⇒ 这两块要低细节。
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
OUT = r'D:\dsh\tmp\title_i2i'
os.makedirs(OUT, exist_ok=True)

SRC = r'D:\个人项目\daishu\assets\images\backgrounds\main.png'
DENOISE = 0.60
STYLE = ('flat 2d illustration, clean flat colour shapes, warm brown beige and ochre palette '
         'with soft muted accents, minimal shading, storybook background art, gentle morning light, '
         'low contrast, calm')

SHOTS = [
    ('cn',
     'traditional Chinese Ming dynasty street at early morning, '
     'wooden lattice windows with vertical grids, whitewashed plaster walls, '
     'dark grey tiled hip roofs with gently upturned eaves, exposed dark wooden columns and beams, '
     'a stone arch bridge over a narrow canal, willow tree, '
     'wide open pale warm sky filling the upper half, empty stone paving in the lower half, '
     'no arched romanesque windows, no european half-timbered houses, '
     'no crowds, no signs, no banners'),
]
SEEDS = [0]

NEGATIVE = ('text, letters, characters, words, writing, handwriting, calligraphy, script, '
            'inscription, chinese characters, kanji, hanzi, seal, stamp, wax seal, signature, '
            'watermark, logo, brand, shop sign, signboard, sign board, hanging scroll, '
            'banner, flag, plaque, poster, newspaper, lantern with writing, '
            'person, people, human, face, portrait, crowd, market stall, busy street, stalls, '
            'photograph, photorealistic, realistic photograph, dslr, depth of field, '
            'high saturation, neon, noise, jpeg artifacts, blurry, low quality, '
            'dark, gloomy, cluttered, busy detail, abstract, colour blocks, '
            'european architecture, romanesque arch, gothic, half-timbered house, western town, '
            'arched window, pencil tower, victorian, medieval europe')


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
    global SRC_B64
    with open(SRC,'rb') as fh:
        SRC_B64 = base64.b64encode(fh.read()).decode('ascii')
    try:
        if not switch_model('Illustrious-XL-v2.0.safetensors'):
            log('[abort] 底模未确认')
            return 1
        for tag, scene in SHOTS:
            for seed in SEEDS:
                payload = {'init_images': [SRC_B64], 'denoising_strength': DENOISE, 'prompt': '%s, %s' % (scene, STYLE), 'negative_prompt': NEGATIVE,
                           'width': 1152, 'height': 648, 'steps': 28, 'cfg_scale': 6.0,
                           'seed': seed, 'batch_size': 1,
                           'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
                           'send_images': True, 'save_images': False}
                t0 = time.time()
                try:
                    res = post('/sdapi/v1/img2img', payload)
                except Exception as e:
                    log('[%s s%d] 失败 %s' % (tag, seed, str(e)[:100]))
                    continue
                for b64 in res.get('images', []):
                    p = os.path.join(OUT, '%s_s%d.png' % (tag, seed))
                    with open(p, 'wb') as f:
                        f.write(base64.b64decode(b64))
                    log('[out] %-20s %d B (%.0fs)' % (os.path.basename(p), os.path.getsize(p), time.time() - t0))
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
