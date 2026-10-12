"""找一个"既中式、又插画"的底模 —— 本机缺这一类。

上一轮的结论：`3Guofeng3`（国风）出照片、`Illustrious-XL`（动漫插画）出欧式建筑。
但本机还有 **3 个没试过**的 SDXL 动漫/插画底模：
  `waiIllustriousSDXL_v170`（国内社区常用的动漫插画向）
  `autismmixSDXL_autismmixConfetti`（动漫向）
  `国风武侠Chinese style`（国风，SD1.5）

做法：**同一句提示词、同一 seed，只换底模** ⇒ 差异就是底模的差异。
提示词用上一轮验证最有效的"中式建筑标记"版本。
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
OUT = r'D:\dsh\tmp\wai_warm'
os.makedirs(OUT, exist_ok=True)

SCENE = (
    'traditional Chinese Ming dynasty street at early morning, '
    'wooden lattice windows with vertical grids, whitewashed plaster walls, '
    'dark grey tiled hip roofs with gently upturned eaves, exposed dark wooden columns and beams, '
    'a stone arch bridge over a narrow canal, willow tree, '
    'wide open pale warm sky filling the upper half, empty stone paving in the lower half, '
    'flat 2d illustration, clean flat colour shapes, warm golden hour lighting, '
    'dominant warm brown, amber, ochre and cream palette, sunlit, '
    'minimal shading, low contrast, calm, no people, no signs, no banners, no text')
NEGATIVE = (
    'text, letters, characters, words, writing, calligraphy, chinese characters, kanji, '
    'seal, stamp, signature, watermark, logo, shop sign, signboard, hanging scroll, plaque, '
    'banner, flag, person, people, human, face, portrait, crowd, '
    'photograph, photorealistic, realistic photograph, dslr, depth of field, '
    'european architecture, romanesque arch, gothic, half-timbered house, western town, '
    'arched window, victorian, medieval europe, '
    'cool blue tones, grey sky, teal, cold colour cast, overcast, dusk blue, high saturation, neon, noise, jpeg artifacts, blurry, low quality, '
    'dark, gloomy, cluttered, busy detail, abstract, colour blocks')

MODELS = ['waiIllustriousSDXL_v170.safetensors']
SEED = 432001


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
    for _ in range(160):
        try:
            cur = get_json('/sdapi/v1/options', 30).get('sd_model_checkpoint', '')
        except Exception:
            cur = ''
        if fname in cur:
            log('[model] ✅ %s' % cur)
            return True
        time.sleep(3)
    log('[model] ⚠️ 切换未确认，当前=%s' % cur)
    return False


def main():
    proc = None
    if not api_up():
        proc = start_server()
        if not wait_ready():
            if proc:
                proc.terminate()
            return 1
    try:
        for m in MODELS:
            tag = m.split('.')[0][:18]
            if not switch_model(m):
                log('[skip] %s' % m)
                continue
            # SD1.5 底模用 512x288（它的原生分辨率），SDXL 用 1152x648
            w, h = (768, 432) if 'ckpt' in m else (1152, 648)
            payload = {'prompt': SCENE, 'negative_prompt': NEGATIVE,
                       'width': w, 'height': h, 'steps': 28, 'cfg_scale': 6.0,
                       'seed': SEED, 'batch_size': 1,
                       'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
                       'send_images': True, 'save_images': False}
            t0 = time.time()
            try:
                res = post('/sdapi/v1/txt2img', payload)
            except Exception as e:
                log('[%s] 失败 %s' % (tag, str(e)[:110]))
                continue
            for b64 in res.get('images', []):
                p = os.path.join(OUT, '%s.png' % tag)
                with open(p, 'wb') as f:
                    f.write(base64.b64decode(b64))
                log('[out] %-20s %dx%d  %d B (%.0fs)' % (os.path.basename(p), w, h, os.path.getsize(p), time.time() - t0))
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
