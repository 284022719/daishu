"""第二轮概念图：补三种画风。

第一轮（concept_styles.py）的教训：**画面里只要出现"挂着的纸/卷轴"，就必然被配上文字**
（B 木刻的挂轴、D 矢量的挂轴都写了字）。而水墨 LoRA 那几轮更严重（连桌上平放的纸也写字）。

所以这一轮的三段提示词里**刻意不出现挂轴/卷轴/字画**，只留墙面、窗、书案 ——
用"减少纸上表面的种类"来压制文字。这是从失败里反推出来的约束，不是拍脑袋。
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

# 与第一轮同场景，但**去掉一切挂着的纸**（那是文字的来源）
SCENE = (
    'a Ming dynasty Chinese letter-writing shop interior, empty room with no people, '
    'a wooden writing desk with a brush rest, writing brushes, an inkstone and a stack of '
    'blank paper, a plain wooden shelf and an empty lattice window, bare plaster wall, '
    'deliberately large plain low-detail area in the middle of the frame, '
    'no people, no text, no watermark, no signature'
)

NEGATIVE = (
    'text, letters, characters, words, writing, handwriting, calligraphy, script, '
    'inscription, chinese characters, kanji, hanzi, seal, stamp, wax seal, signature, '
    'watermark, logo, brand, poster, newspaper, hanging scroll, scroll, hanging paper, '
    'person, people, human, figure, portrait, face, hands, crowd, '
    'blurry, noise, jpeg artifacts, low quality, purple fringing, chromatic aberration, '
    'cluttered, busy, close-up, macro'
)

STYLES = [
    ('E 平涂绘本', 'flat storybook illustration, soft gouache, simple rounded shapes, '
                   'warm muted palette, subtle paper grain', 'waiIllustriousSDXL_v170'),
    ('F 赛璐璐动画', 'cel shaded animation background, clean line art, flat shading, '
                     'muted retro palette, anime movie background', 'waiIllustriousSDXL_v170'),
    ('G 低多边形厚涂', 'stylized painterly concept art, chunky simplified brush shapes, '
                       'desaturated warm palette, matte finish', 'autismmixSDXL_autismmixConfetti'),
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
    for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy'):
        env.pop(k, None)
    for k in ('NO_PROXY', 'no_proxy'):
        env[k] = '127.0.0.1,localhost,::1'
    env.update({'PYTHON': PY, 'VENV_DIR': '-', 'SKIP_VENV': '1', 'PYTHONIOENCODING': 'utf-8',
                'COMMANDLINE_ARGS': '--api --listen --port 7860 --medvram --xformers --skip-version-check'})
    logf = open(os.path.join(OUTDIR, 'sd_concept2.log'), 'w', encoding='utf-8', errors='replace')
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
        log('[out] %s %6d B (%.0fs)' % (os.path.basename(p), os.path.getsize(p), dt))


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    proc = None
    if not api_up():
        proc = start_server()
        if not wait_ready():
            log('[srv] FAIL，看 sd_concept2.log')
            if proc:
                proc.terminate()
            return 1
    else:
        log('[srv] 复用')
    try:
        for idx, (label, style, model) in enumerate(STYLES, 5):
            set_model(model)
            log('[gen] %s (底模 %s)' % (label, model))
            gen(os.path.join(OUTDIR, 'style%d.png' % idx), '%s, %s' % (style, SCENE), n=1)
    finally:
        if proc:
            log('[srv] 停止 PID %d' % proc.pid)
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except Exception:
                proc.kill()
    log('[done]')
    return 0


if __name__ == '__main__':
    sys.exit(main())
