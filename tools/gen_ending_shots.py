"""补 ⑩⑪：success / gameover / prologue 三个背景图（当前三个场景完全没有贴图）。

为什么先做这三个（而不是继续攻 main_bg 的精构）：
  上一轮定位到"txt2img 不服从空间关系" —— 而这三张是**纯氛围图**：
  success=科举中第的暖光、gameover=黄昏雨中的失落、prologue=夜读孤灯。
  它们**不需要精确的前后层次与占位比例** ⇒ 正好绕开那个瓶颈。

文字占位（据 .tscn 实测，背景要让文字读得清）：
  success/gameover: VBoxContainer anchors_preset=15 + offset_top/bottom 80 → 文字在中间带
  prologue:         VBoxContainer 正中 offset -180..180 → 文字在正中带

硬约束沿用已验证的：
  16:9、无文字/幌子/招牌（避免必然被写字）、插画向底模、暖色低饱和。
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
OUT = r'D:\dsh\tmp\ending2'
os.makedirs(OUT, exist_ok=True)

STYLE = ('flat illustration, clean flat colour shapes, soft limited palette, minimal shading, '
         'storybook background art, low contrast, no text, no writing, no signs, no banners, '
         'no people, no faces')

SHOTS = [
    ('gameover2',
     'a narrow Ming dynasty town street at dusk in light rain, low wooden two-storey shopfronts '
     'with closed shutters lining both sides receding into misty distance, wet stone paving '
     'reflecting a few faint warm lanterns, puddles, muted grey blue with warm accents, '
     'melancholic subdued mood, empty street, the buildings clearly readable as shops'),
    ('prologue2',
     'a poor scholars study interior lit by warm afternoon light through a paper lattice window, '
     'a simple wooden desk with a stack of worn books, a brush pot and a blank sheet of paper, '
     'plain warm plaster wall, soft warm beige and brown palette, calm and quiet, '
     'bright enough to be readable, no dark areas'),
]
SEEDS = [8003, 9004]

NEGATIVE = (
    'text, letters, characters, words, writing, handwriting, calligraphy, script, '
    'inscription, chinese characters, kanji, hanzi, seal, stamp, wax seal, signature, '
    'watermark, logo, brand, shop sign, signboard, hanging scroll, plaque, banner, flag, '
    'poster, newspaper, book with writing, '
    'person, people, human, face, portrait, crowd, hands, silhouettes of people, '
    'photograph, photorealistic, realistic photograph, dslr, depth of field, '
    'high saturation, neon, noise, jpeg artifacts, blurry, low quality, cluttered, busy detail')


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
        # 插画向底模（上一轮实测：画风由底模决定）
        if not switch_model('Illustrious-XL-v2.0.safetensors'):
            log('[abort] 底模未确认')
            return 1
        for tag, scene in SHOTS:
            for seed in SEEDS:
                payload = {'prompt': '%s, %s' % (scene, STYLE), 'negative_prompt': NEGATIVE,
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
