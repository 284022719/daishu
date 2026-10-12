"""用 Illustrious-XL（本机本身就出平涂插画风的底模）+ 暖色提示词，出游戏背景。

本轮关键发现（推翻了前面的方向）：
  我一直在"**加 LoRA / 换风格词**"求平涂插画风，但实测 **Illustrious-XL 不加任何 LoRA
  就已经出低饱和平涂插画**（大色块、线稿感）。
  而前面用的底模是**写实向**的（国风武侠、3Guofeng3 SD1.5）—— 所以怎么调提示词都像照片。
  ⇒ **正解是换回插画向底模**，不是继续加约束。

同时保留已确认的硬约束：
  - 16:9（标题页 stretch_mode=0 会拉伸变形）
  - 上中 + 正中要低细节（标题区 y3.4~32.4%、按钮区 y36~64%）
  - 不出现幌子/招牌/挂幡（这类元素必然被写字，违反禁文字）
  - 暖色低饱和（本作色板：宣纸 #fce4b4 / 木构 #9c5424 / 墨 #3c3c2c）
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
OUT = r'D:\dsh\tmp\illi2'
os.makedirs(OUT, exist_ok=True)

# 三段都刻意避开幌子/招牌/卷轴；强调暖色低饱和与"大片平坦区域"
SHOTS = [
    ('lane',
     'a quiet Ming dynasty stone lane at dawn, tiled roofs and plain warm beige plaster walls '
     'along both sides, a simple dark wooden door, bare branches at the upper right, '
     'mostly empty soft cream and pale warm beige sky filling the upper half, '
     'warm brown ochre and muted sand palette, no green, flat illustration, clean colour shapes, '
     'no text, no signs, no banners, no people'),
]
SEEDS = [3003, 4004]

NEGATIVE = ('text, letters, characters, words, writing, handwriting, calligraphy, script, '
            'inscription, chinese characters, kanji, hanzi, seal, stamp, wax seal, signature, '
            'watermark, logo, brand, shop sign, signboard, sign board, hanging scroll, '
            'banner, flag, plaque, poster, newspaper, lantern with writing, '
            'person, people, human, face, portrait, crowd, market stall, busy street, '
            'photograph, photorealistic, realistic photograph, dslr, depth of field, '
            'high saturation, neon, pink sky, cyan, green sky, teal sky, green tint, sage green, mint, noise, jpeg artifacts, blurry, low quality, '
            'dark, gloomy, cluttered, busy detail')


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
    try:
        if not switch_model('Illustrious-XL-v2.0.safetensors'):
            log('[abort] 底模未确认')
            return 1
        for tag, scene in SHOTS:
            for seed in SEEDS:
                payload = {'prompt': scene, 'negative_prompt': NEGATIVE,
                           'width': 1152, 'height': 648, 'steps': 28, 'cfg_scale': 6.0,
                           'seed': seed, 'batch_size': 1,
                           'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
                           'send_images': True, 'save_images': False}
                t0 = time.time()
                try:
                    res = post('/sdapi/v1/txt2img', payload)
                except Exception as e:
                    log('[%s s%d] 失败 %s' % (tag, seed, str(e)[:100]))
                    continue
                for b64 in res.get('images', []):
                    p = os.path.join(OUT, '%s_s%d.png' % (tag, seed))
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
