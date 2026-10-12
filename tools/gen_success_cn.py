"""重出 success 结局背景：去掉紫粉色调，统一为暖金（与标题图同源一致）。

为什么重出（总览图暴露的残留不一致）：
  标题 `main.png`  暖度 +88（暖金）
  `gameover`       暖度 −27（冷蓝雨，忧郁剧情）
  **`success`       紫粉色** —— 既不暖也不冷，是全套里唯一的异色。
  根因：success 与旧标题图都是 `Illustrious-XL` 出的（该底模偏紫粉），属同一问题。

  success 的剧情是"科举中第"，**暖金/夕照是正确方向**（也该与标题图呼应）。

沿用已验证配方：`waiIllustriousSDXL_v170` + 暖色提示词。
判据：暖度应向 +85 量级靠；文字区（全屏 VBox 居中）细节要低。
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
OUT = r'D:\dsh\tmp\success2'
os.makedirs(OUT, exist_ok=True)

SCENE = (
    'a grand traditional Chinese Ming dynasty ceremonial gate hall seen from a distance at '
    'golden hour, dark grey tiled roofs with gently upturned eaves, tall red wooden columns, '
    'whitewashed walls, an open stone-paved courtyard in the foreground, '
    'very large open warm sky filling the upper half, '
    'flat 2d illustration, clean flat colour shapes, '
    'dominant warm golden amber and cream palette, glowing sunset light, '
    'minimal shading, low contrast, triumphant hopeful mood, '
    'no people, no signs, no banners, no text')
NEGATIVE = (
    'pink sky, purple, magenta, violet, mauve, lilac, pastel pink, '
    'torii, japanese shrine, pagoda, '
    'european architecture, half-timbered house, romanesque arch, gothic, victorian, '
    'pointed roof, chimney, arched window, '
    'text, letters, characters, words, writing, calligraphy, chinese characters, kanji, '
    'seal, stamp, signature, watermark, logo, shop sign, signboard, hanging scroll, plaque, '
    'banner, flag, person, people, human, face, portrait, crowd, '
    'photograph, photorealistic, realistic photograph, dslr, depth of field, '
    'cool blue tones, grey sky, teal, cold colour cast, overcast, '
    'high saturation, neon, noise, jpeg artifacts, blurry, low quality, '
    'dark gloomy, cluttered, busy detail, abstract, colour blocks')
SEEDS = [221001, 221002, 221003]


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
    for _ in range(160):
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
    try:
        if not switch_model('waiIllustriousSDXL_v170.safetensors'):
            log('[abort] 底模未确认')
            return 1
        for seed in SEEDS:
            payload = {'prompt': SCENE, 'negative_prompt': NEGATIVE,
                       'width': 1152, 'height': 648, 'steps': 28, 'cfg_scale': 6.0,
                       'seed': seed, 'batch_size': 1,
                       'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
                       'send_images': True, 'save_images': False}
            t0 = time.time()
            try:
                res = post('/sdapi/v1/txt2img', payload)
            except Exception as e:
                log('[s%d] 失败 %s' % (seed, str(e)[:110]))
                continue
            for b64 in res.get('images', []):
                p = os.path.join(OUT, 'succ_s%d.png' % seed)
                with open(p, 'wb') as f:
                    f.write(base64.b64decode(b64))
                log('[out] %-18s %d B (%.0fs)' % (os.path.basename(p), os.path.getsize(p), time.time() - t0))
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
