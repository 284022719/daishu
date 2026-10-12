"""重出失败的两张 NPC 肖像（兄弟 / 朋友），用更强的"单一人像"约束。

上一轮 5 张里 3 张成功（父母/子女/夫妻），2 张失败：
  `兄弟` -> 出了 **9 个重复的狐狸头**（模型把它当图案生成）
  `朋友` -> 出了 **一件挂着的衣服**（没有人物）

修法：① 提示词强调 `ONE single ... head-and-shoulders illustration`、明确 `shoulders visible`；
② 负面加 `multiple characters / repeated faces / pattern / grid / wallpaper /
clothing on a hanger / mannequin / empty clothes / fox / cat / animals`；
③ 换 seed。
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
OUT = r'D:\dsh\tmp\avatars_fix'
os.makedirs(OUT, exist_ok=True)

STYLE = ('flat 2d illustration, clean flat colour shapes, minimal shading, '
         'warm rice-paper beige background, warm earthy brown and ochre palette, '
         'simple bold shapes readable at small size, centred bust portrait')

SHOTS = [
    ('兄弟',
     'head-and-shoulders illustration of ONE SINGLE Ming dynasty Chinese young man, '
     'plain cloth headband, simple brown work jacket, friendly face, shoulders visible'),
    ('朋友',
     'head-and-shoulders illustration of ONE SINGLE Ming dynasty Chinese travelling peddler, '
     'simple cloth cap, weathered friendly face, plain brown jacket, shoulders visible'),
]
NEGATIVE = (
    'multiple characters, two people, repeated faces, pattern, wallpaper, grid, tiling, '
    'clothing on a hanger, mannequin, empty clothes, objects only, still life, furniture, '
    'fox, cat, animal, furry, cute animal, '
    'text, letters, characters, words, writing, calligraphy, chinese characters, kanji, '
    'seal, stamp, signature, watermark, logo, sign, banner, '
    'full body, hands, crowd, multiple heads, '
    'photograph, photorealistic, realistic photograph, dslr, 3d render, '
    'complex detail, busy background, scenery, landscape, '
    'dark, gloomy, high saturation, neon, noise, jpeg artifacts, blurry, low quality')
SEEDS = [771001, 991001]


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
        for rel, desc in SHOTS:
            for seed in SEEDS:
                payload = {'prompt': '%s, %s' % (desc, STYLE), 'negative_prompt': NEGATIVE,
                           'width': 512, 'height': 512, 'steps': 28, 'cfg_scale': 6.0,
                           'seed': seed, 'batch_size': 1,
                           'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
                           'send_images': True, 'save_images': False}
                t0 = time.time()
                try:
                    res = post('/sdapi/v1/txt2img', payload)
                except Exception as e:
                    log('[%s s%d] 失败 %s' % (rel, seed, str(e)[:100]))
                    continue
                for b64 in res.get('images', []):
                    p = os.path.join(OUT, '%s_s%d.png' % (rel, seed))
                    with open(p, 'wb') as f:
                        f.write(base64.b64decode(b64))
                    log('[out] %-22s %d B (%.0fs)' % (os.path.basename(p), os.path.getsize(p), time.time() - t0))
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
