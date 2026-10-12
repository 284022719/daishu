"""用两个新国风底模实测出图 —— 这是真正的"换底模"验证。

之前十几张失败的根因（推断并被反复印证）：本机 5 个底模全是**动漫人物向**，
在"安静的明代室内空场景"上要么出人物、要么出西式房间、要么出噪声。
新下的两个是**国风**底模：
  4Guofeng4XL_v1125D  6.46 GB  SDXL
  3Guofeng3_v34       2.14 GB  SD1.5

注意：WebUI 的模型列表是**启动时枚举**的，新增底模必须**重启服务**才可见。
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
OUT = r'D:\dsh\tmp\newbase'
os.makedirs(OUT, exist_ok=True)

# 沿用已验证的"明代文书铺内景 + 无人 + 无文字 + 中部留白"场景描述
SCENE = (
    'a Ming dynasty Chinese letter-writing shop interior, empty room with no people, '
    'a wooden writing desk with writing brushes, an inkstone and a stack of blank paper, '
    'a plain wooden shelf and an empty lattice window, bare plaster wall, '
    'large plain low-detail area in the middle of the frame, '
    'no people, no text, no watermark, no signature'
)
# 与 concept 轮里表现最好的"水彩童书"同调，保证换的是底模不是画风
STYLE = ('soft watercolor and gouache illustration, warm rice-paper tone, '
         'muted earth palette, gentle washes, subtle paper texture, hand painted, low contrast')
NEGATIVE = (
    'text, letters, characters, words, writing, handwriting, calligraphy, script, '
    'inscription, chinese characters, kanji, hanzi, seal, stamp, wax seal, signature, '
    'watermark, logo, brand, hanging scroll, scroll, poster, newspaper, '
    'person, people, human, figure, portrait, face, hands, crowd, '
    'modern, western, photorealistic, 3d render, blurry, noise, jpeg artifacts, '
    'purple fringing, chromatic aberration, cluttered, busy, close-up, macro'
)

CASES = [
    ('Guofeng4XL', '4Guofeng4XL_v1125D.safetensors', 1152, 648, 28),
    ('Guofeng3',   '3Guofeng3_v34.safetensors',      768, 432, 28),
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
        env[k] = '127.0.0.1,localhost,::1'     # gradio 启动自检需要
    env.update({'PYTHON': PY, 'VENV_DIR': '-', 'SKIP_VENV': '1', 'PYTHONIOENCODING': 'utf-8',
                'COMMANDLINE_ARGS': '--api --listen --port 7860 --medvram --xformers --skip-version-check'})
    lf = open(os.path.join(OUT, 'server.log'), 'w', encoding='utf-8', errors='replace')
    p = subprocess.Popen([PY, 'launch.py'], cwd=LAUNCHER, env=env, stdout=lf, stderr=subprocess.STDOUT)
    log('[srv] 启动 PID %d（为让新底模可见，必须重启）' % p.pid)
    return p


def wait_ready(limit=900):
    t0 = time.time()
    while time.time() - t0 < limit:
        if api_up():
            log('[srv] 就绪 %.0fs' % (time.time() - t0))
            return True
        time.sleep(5)
    return False


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
        models = [m['model_name'] for m in get_json('/sdapi/v1/sd-models', 30)]
        log('[model] 当前可见底模 %d 个:' % len(models))
        for m in models:
            log('        %s' % m)
        for tag, fname, w, h, steps in CASES:
            want = fname.split('.')[0]
            if not any(want[:12] in m for m in models):
                log('[%s] ⚠️ 列表里没有 %s，跳过' % (tag, fname))
                continue
            log('[%s] 切换 + 出图' % tag)
            post('/sdapi/v1/options', {'sd_model_checkpoint': fname}, timeout=900)
            for _ in range(120):
                try:
                    cur = get_json('/sdapi/v1/options', 30).get('sd_model_checkpoint', '')
                    if cur.startswith(want[:12]):
                        break
                except Exception:
                    pass
                time.sleep(3)
            payload = {'prompt': '%s, %s' % (STYLE, SCENE), 'negative_prompt': NEGATIVE,
                       'width': w, 'height': h, 'steps': steps, 'cfg_scale': 7.0,
                       'seed': 880088, 'batch_size': 2,
                       'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
                       'send_images': True, 'save_images': False}
            t0 = time.time()
            res = post('/sdapi/v1/txt2img', payload)
            imgs = res.get('images', [])
            for i, b64 in enumerate(imgs):
                p = os.path.join(OUT, '%s_%d.png' % (tag, i + 1))
                with open(p, 'wb') as f:
                    f.write(base64.b64decode(b64))
                log('[out] %s  %d B  (%.0fs)' % (os.path.basename(p), os.path.getsize(p), time.time() - t0))
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
