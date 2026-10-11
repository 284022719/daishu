"""重试 E/F：上一版出成了灰褐噪声（同批 style1 正常，所以是措辞触发，不是模型坏）。

上一版措辞（失败）：
  E: 'flat storybook illustration, soft gouache, simple rounded shapes, warm muted palette, subtle paper grain'
  F: 'cel shaded animation background, clean line art, flat shading, muted retro palette, anime movie background'

换成更常规、不带"flat / clean line art / movie background"这类强风格词的写法，
并换一个 seed（噪声也可能是该 seed 下采样发散）。
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
W, H, STEPS = 1152, 648, 30

SCENE = (
    'a Ming dynasty Chinese letter-writing shop interior, empty room with no people, '
    'a wooden writing desk with a writing brush, an inkstone and a stack of blank paper, '
    'a plain wooden shelf and an empty lattice window, bare plaster wall, '
    'large plain low-detail area in the middle of the frame, '
    'no people, no text, no watermark, no signature'
)
NEGATIVE = (
    'text, letters, characters, words, writing, handwriting, calligraphy, script, '
    'inscription, chinese characters, kanji, hanzi, seal, stamp, wax seal, signature, '
    'watermark, logo, brand, hanging scroll, scroll, '
    'person, people, human, figure, portrait, face, hands, crowd, '
    'noise, static, grain, gray mud, blurry, jpeg artifacts, low quality, '
    'purple fringing, chromatic aberration, close-up, macro, abstract'
)

CASES = [
    ('style5.png', 'E 平涂绘本',
     'childrens picture book illustration, soft watercolor and gouache, rounded shapes, '
     'warm muted autumn palette, hand painted, storybook art'),
    ('style6.png', 'F 赛璐璐动画',
     'japanese animation background art, cel shading, visible outline, '
     'retro muted color palette, painted background, studio ghibli style'),
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
    logf = open(os.path.join(OUTDIR, 'sd_retry.log'), 'w', encoding='utf-8', errors='replace')
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


def gen(out, prompt, seed):
    payload = {'prompt': prompt, 'negative_prompt': NEGATIVE, 'width': W, 'height': H,
               'steps': STEPS, 'cfg_scale': 7.0, 'seed': seed, 'batch_size': 1,
               'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
               'send_images': True, 'save_images': False}
    t0 = time.time()
    res = post('/sdapi/v1/txt2img', payload)
    imgs = res.get('images', [])
    if imgs:
        with open(out, 'wb') as f:
            f.write(base64.b64decode(imgs[0]))
        log('[out] %s %8d B (%.0fs)' % (os.path.basename(out), os.path.getsize(out), time.time() - t0))
    else:
        log('[out] FAIL')


def main():
    proc = None
    if not api_up():
        proc = start_server()
        if not wait_ready():
            log('[srv] FAIL')
            if proc:
                proc.terminate()
            return 1
    try:
        for fn, label, style in CASES:
            log('[gen] %s' % label)
            gen(os.path.join(OUTDIR, fn), '%s, %s' % (style, SCENE), seed=424242)
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
