"""画风概念图：同一场景 + 同一构图，只换画风，供用户挑选。

设计原则（保证可比性）：
- **场景描述与构图在所有风格里逐字相同**，只有"画风段"不同 —— 否则比出来的是内容差异而非画风差异
- **统一约束**：无人（玩家才是代笔先生）、无文字（ART_PLAN §一 硬规矩）、
  画面中部大片低细节（UI 面板是半透明 alpha 0.78，底下太花会读不清）
- **固定 seed**，便于复现与再调
- 全部使用负面词表压掉"画风跑偏 + 出字 + 出人"

风格清单**刻意避开水墨/国画**（用户已表示不喜欢）：
水彩童书 / 木刻版画 / 厚涂动画 / 极简矢量。
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
OUTDIR = r'D:\dsh\tmp\concept'
SEED = 717717
STEPS = 30
W, H = 1152, 648

# ⚠️ 这段在**所有风格里逐字相同** —— 它负责"画的是什么、怎么摆"
SCENE = (
    'a Ming dynasty Chinese letter-writing shop interior, empty room with no people, '
    'a wooden writing desk with a brush rest, several writing brushes, an inkstone and '
    'a stack of blank paper, a wooden shelf and a lattice window in the background, '
    'deliberately large plain low-detail area in the middle of the frame, '
    'no people, no text, no watermark, no signature'
)

NEGATIVE = (
    'text, letters, characters, words, writing, handwriting, calligraphy, script, '
    'inscription, chinese characters, kanji, hanzi, seal, stamp, wax seal, signature, '
    'watermark, logo, brand, poster, newspaper, '
    'person, people, human, figure, portrait, face, hands, crowd, '
    'blurry, noise, jpeg artifacts, low quality, purple fringing, chromatic aberration, '
    'cluttered, busy'
)

# 每个风格：显示名 -> (风格段, 底模)
STYLES = [
    ('A 水彩童书插画', 'soft watercolor childrens book illustration, gentle washes, '
                       'paper texture, warm muted palette, hand painted', 'waiIllustriousSDXL_v170'),
    ('B 木刻版画', 'japanese woodblock print (ukiyo-e), flat color areas, bold outlines, '
                   'visible carving texture, limited muted palette', 'waiIllustriousSDXL_v170'),
    ('C 厚涂动画场景', 'painted animation background, gouache style, soft cinematic light, '
                       'flat muted palette, clean shapes, studio quality', 'Illustrious-XL-v2.0'),
    ('D 极简矢量扁平', 'minimal flat vector illustration, geometric simplified shapes, '
                       'limited muted color palette, subtle paper texture, editorial style',
     'waiIllustriousSDXL_v170'),
]


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
    # 代理双重需求（实测踩过两次）：下载要去掉外网代理；
    # gradio 启动要有 NO_PROXY 让 localhost 直连，否则报
    # "ValueError: When localhost is not accessible"。
    for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy'):
        env.pop(k, None)
    for k in ('NO_PROXY', 'no_proxy'):
        env[k] = '127.0.0.1,localhost,::1'
    env.update({'PYTHON': PY, 'VENV_DIR': '-', 'SKIP_VENV': '1', 'PYTHONIOENCODING': 'utf-8',
                'COMMANDLINE_ARGS': '--api --listen --port 7860 --medvram --xformers --skip-version-check'})
    logf = open(os.path.join(OUTDIR, 'sd_concept.log'), 'w', encoding='utf-8', errors='replace')
    p = subprocess.Popen([PY, 'launch.py'], cwd=LAUNCHER, env=env, stdout=logf, stderr=subprocess.STDOUT)
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


def set_model(name):
    cur = ''
    try:
        cur = get_json('/sdapi/v1/options', 30).get('sd_model_checkpoint', '')
    except Exception:
        pass
    if cur.startswith(name.split('.')[0]):
        log('[model] 已是 %s' % name)
        return True
    log('[model] -> %s' % name)
    post('/sdapi/v1/options', {'sd_model_checkpoint': name}, timeout=900)
    want = name.split('.')[0]
    for _ in range(90):
        try:
            if get_json('/sdapi/v1/options', 30).get('sd_model_checkpoint', '').startswith(want):
                log('[model] 就绪')
                return True
        except Exception:
            pass
        time.sleep(3)
    return False


def gen(out, prompt, n=1):
    payload = {'prompt': prompt, 'negative_prompt': NEGATIVE, 'width': W, 'height': H,
               'steps': STEPS, 'cfg_scale': 7.0, 'seed': SEED, 'batch_size': n,
               'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
               'send_images': True, 'save_images': False}
    t0 = time.time()
    res = post('/sdapi/v1/txt2img', payload)
    dt = time.time() - t0
    imgs = res.get('images', [])
    base, ext = os.path.splitext(out)
    for i, b64 in enumerate(imgs):
        p = out if len(imgs) == 1 else '%s_%02d%s' % (base, i + 1, ext)
        with open(p, 'wb') as f:
            f.write(base64.b64decode(b64))
        log('[out] %s %6d B  (%.0fs)' % (os.path.basename(p), os.path.getsize(p), dt))


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    proc = None
    if not api_up():
        proc = start_server()
        if not wait_ready():
            log('[srv] FAIL 未就绪，看 sd_concept.log')
            if proc:
                proc.terminate()
            return 1
    else:
        log('[srv] 复用')

    try:
        for i, (label, style, model) in enumerate(STYLES, 1):
            set_model(model)
            prompt = '%s, %s' % (style, SCENE)
            log('[gen] %s  (底模 %s)' % (label, model))
            gen(os.path.join(OUTDIR, 'style%d.png' % i), prompt, n=1)
    finally:
        if proc:
            log('[srv] 停止 PID %d' % proc.pid)
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except Exception:
                proc.kill()
    log('[done] 定稿风格后我再出 2~3 张候选')
    return 0


if __name__ == '__main__':
    sys.exit(main())
