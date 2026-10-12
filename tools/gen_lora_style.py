"""用 SDXL 风格 LoRA 出图 —— 这是"风格控制"的真正解法。

为什么这条路与前几轮不同：
  之前靠"底模 + 提示词"求插画风，实测底模**不服从风格词**（写 flat illustration 仍出照片级）。
  LoRA 是**训练出来的风格权重**，直接改 UNet 的行为，不依赖提示词服从度。

做法（保证可比性）：
  - 同一场景段（干净的河岸黎明，无幌子/招牌 ⇒ 从源头避开"被写字"）
  - 同一 seed
  - 同一 SDXL 底模
  - **只换 LoRA** ⇒ 差异就是风格差异
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
OUT = r'D:\dsh\tmp\lora_style'
os.makedirs(OUT, exist_ok=True)

SCENE = ('wide view of a Ming dynasty riverside town at dawn seen from a distance across calm '
         'water, low stone embankment, a few distant tiled rooftops and a simple stone arch '
         'bridge, very large pale open sky filling the upper half, soft mist over the water '
         'in the lower half, no buildings in the foreground, no shop signs, no cloth banners, '
         'no characters, no text, no people, muted warm palette')

CASES = [
    (None, 'none'),
    ('sdxl_vector-illustration', 'vector'),
    ('sdxl_flat-cartoon', 'flatcartoon'),
    ('sdxl_line-art', 'lineart'),
    ('sdxl_watercolor', 'watercolor'),
    ('sdxl_chinese-ink', 'chineseink'),
]

NEGATIVE = ('text, letters, characters, words, writing, handwriting, calligraphy, script, '
            'inscription, chinese characters, kanji, hanzi, seal, stamp, wax seal, signature, '
            'watermark, logo, brand, shop sign, signboard, hanging scroll, banner, flag, plaque, '
            'poster, newspaper, person, people, human, face, portrait, crowd, '
            'photograph, photorealistic, realistic photograph, dslr, depth of field, '
            'noise, jpeg artifacts, blurry, low quality, dark, gloomy, cluttered')


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
        get_json('/sdapi/v1/sd-models', 60)      # 预热，避免字典改size
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
    try:
        # 用 Illustrious-XL（本机 SDXL，之前 txt2img 正常，无 NaN）
        if not switch_model('Illustrious-XL-v2.0.safetensors'):
            log('[abort] 底模未确认')
            return 1
        for lora, tag in CASES:
            prompt = SCENE
            if lora:
                prompt = '%s <lora:%s:0.85>' % (SCENE, lora)
            payload = {'prompt': prompt, 'negative_prompt': NEGATIVE,
                       'width': 1152, 'height': 648, 'steps': 28, 'cfg_scale': 6.5,
                       'seed': 30001, 'batch_size': 1,
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
                log('[out] %-14s %d B (%.0fs)' % (tag, os.path.getsize(p), time.time() - t0))
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
