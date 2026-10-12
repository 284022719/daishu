"""把 img2img 改画风配方套到**标题底图 main.png**（与 main_bg 成套）。

为什么做这个：`main.png` 现在是**水墨风**，改成同一画风后，标题页与主界面才"成套"。
做法与 ART_RESTYLE_RECIPE.md 一致：以 main.png 为构图底、低重绘强度只改风格。

title_screen.tscn 的硬约束（必须保住）：
  - TextureRect **没设 stretch_mode**（默认 0=STRETCH_SCALE）⇒ **宽高比必须仍是 16:9**，否则变形
  - 标题「代书」占画面 **横向 33.5~66.5% × 纵向 3.4~32.4%** ⇒ 该区域必须保持干净
本脚本改完后会**实测宽高比**与**上半部细节量**，确认这两条没被破坏。
"""
import base64
import os
import subprocess
import sys
import time
import urllib.request
import json

LAUNCHER = r'D:\绘世启动器'
PY = os.path.join(LAUNCHER, '.ext', 'python.exe')
API = 'http://127.0.0.1:7860'
OUT = r'D:\dsh\tmp\restyle_title'
SRC = r'D:\个人项目\daishu\assets\images\backgrounds\main.png'
os.makedirs(OUT, exist_ok=True)

STYLES = [
    ('line',   'delicate ink line drawing with light warm watercolour washes, fine outlines, '
               'pale beige paper tone, understated colour'),
    ('gouache', 'gouache painting, soft matte brush texture, warm muted earth palette, '
                'gentle shading, storybook illustration'),
    ('flat',   'flat vector illustration, clean flat colour shapes, thin dark outlines, '
               'limited warm brown and beige palette, minimal shading'),
]
NEGATIVE = (
    'text, letters, characters, words, writing, handwriting, calligraphy, script, '
    'inscription, chinese characters, kanji, hanzi, seal, stamp, wax seal, signature, '
    'watermark, logo, brand, poster, newspaper, hanging scroll, '
    'person in foreground, portrait, face, hands, '
    'photorealistic, photograph, 3d render, blurry, noise, jpeg artifacts, low quality, '
    'purple fringing, chromatic aberration, dark, gloomy, busy clutter'
)
D = 0.40


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
        get_json('/sdapi/v1/sd-models', 60)     # 预热，避免 dictionary changed size
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
    log('[model] ⚠️ 超时 %s' % cur)
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
    log('[src] %s（构图底）' % os.path.basename(SRC))
    try:
        if not switch_model('3Guofeng3_v34.safetensors'):
            log('[abort] 底模未确认')
            return 1
        for tag, style in STYLES:
            payload = {'init_images': [src_b64], 'prompt': style, 'negative_prompt': NEGATIVE,
                       'denoising_strength': D, 'steps': 30, 'cfg_scale': 7.0, 'seed': 606060,
                       'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
                       'width': 1152, 'height': 648, 'send_images': True, 'save_images': False}
            t0 = time.time()
            try:
                res = post('/sdapi/v1/img2img', payload)
            except Exception as e:
                log('[i2i] %-8s 失败 %s' % (tag, str(e)[:110]))
                continue
            for b64 in res.get('images', []):
                p = os.path.join(OUT, 'title_%s.png' % tag)
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
