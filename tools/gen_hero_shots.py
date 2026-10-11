"""找出"最能代表本作的一张素材" —— 不是换画风，是换**画面本身**。

前 7 张失败的原因（复盘）：全是"空的店铺内景"，换了 7 种画法。
但 README 写的核心是 ——
   "每天来三位委托人……他们不识字，你说他们写。"
**缺少"委托人在对面、你替他把话写成字"这个动作，就没抓住"代书"二字。**

所以这一轮固定画风（用手上表现最好的水彩方向），改出**三个候选构图**：

  ① 过肩/俯视：书案在你我之间，纸摊在案上，委托人的手在对面 —— "视点即代言"
  ② 代书摊正面：市井摊位，幌子、桌案、委托人坐在对面
  ③ 近景特写：毛笔悬在纸上，旁边是委托人的手

硬约束（沿用已验证的）：
- **无文字**（ART_PLAN §一）。纸上一律要求 blank/empty；
  若模型硬要写字，最终接入时可以用 UI 面板压住那片区域 —— 但先要求它别写。
- **中部低细节**（UI 面板 alpha 0.78 半透明）
- **不出现挂轴/卷轴**（上一轮实测：挂着的纸必然被配文字）
- 16:9
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
OUTDIR = r'D:\dsh\tmp\hero'
W, H, STEPS = 1152, 648, 32
MODEL = 'waiIllustriousSDXL_v170'

# 画风段：沿用第一轮里唯一"无字且构图完整"的那条（水彩童书插画），
# 它的好处是：低对比、暖色、纸纹 —— 适合当 UI 底图
STYLE = ('soft watercolor and gouache illustration, warm rice-paper tone, '
         'muted earth palette, gentle washes, subtle paper texture, hand painted, '
         'painterly but calm, low contrast')

NEGATIVE = (
    'text, letters, characters, words, writing, handwriting, calligraphy, script, '
    'inscription, chinese characters, kanji, hanzi, seal, stamp, wax seal, signature, '
    'watermark, logo, brand, poster, newspaper, hanging scroll, scroll, '
    'crowd, many people, blurry, noise, jpeg artifacts, low quality, '
    'purple fringing, chromatic aberration, cluttered, busy, modern, western, '
    'photorealistic, 3d render'
)

# 三个构图（+ 一个纯场景对照）—— 场景描述各自写足明代实体，避免上轮"漂离明代"的问题
SHOTS = [
    ('hero1_overdesk', '过肩俯视：书案在你我之间',
     'view from above and slightly behind a Chinese scribe, looking down at a low wooden writing '
     'desk, a blank sheet of rice paper on the desk with a writing brush and an inkstone beside it, '
     'across the desk the hands of an illiterate customer rest on the desk edge, '
     'Ming dynasty market street softly blurred in the background, '
     'large plain empty area in the middle of the composition, no people face, no text'),
    ('hero2_stall', '代书摊正面：市井摊位',
     'a small Ming dynasty calligrapher stall on a market street, a low wooden table with blank '
     'rice paper, a writing brush and an inkstone, a wooden stool on the other side of the table, '
     'cloth awning overhead, narrow lane with tiled roofs behind, morning light, '
     'plain empty area in the middle, no text, no people'),
    ('hero3_brushpaper', '近景：笔悬纸上',
     'close view of a Chinese writing desk, a writing brush held just above a completely blank '
     'sheet of rice paper, an inkstone and a brush rest at the side, the edge of a customer '
     'sleeve at one corner of the frame, '
     'soft plain background in the middle, no text, no people'),
    ('hero4_street', '对照：市井街景（不含摊位）',
     'a quiet Ming dynasty market lane in the early morning, tiled roofs and wooden shopfronts, '
     'a distant stone bridge, mist, warm muted palette, '
     'large plain low-detail sky area in the middle, no text, no people'),
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
    logf = open(os.path.join(OUTDIR, 'sd_hero.log'), 'w', encoding='utf-8', errors='replace')
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


def gen(out, prompt, seed, n=2):
    payload = {'prompt': prompt, 'negative_prompt': NEGATIVE, 'width': W, 'height': H,
               'steps': STEPS, 'cfg_scale': 7.0, 'seed': seed, 'batch_size': n,
               'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
               'send_images': True, 'save_images': False}
    t0 = time.time()
    res = post('/sdapi/v1/txt2img', payload)
    imgs = res.get('images', [])
    base, ext = os.path.splitext(out)
    for i, b64 in enumerate(imgs):
        p = out if len(imgs) == 1 else '%s_%d%s' % (base, i + 1, ext)
        with open(p, 'wb') as f:
            f.write(base64.b64decode(b64))
        log('[out] %s %8d B (%.0fs)' % (os.path.basename(p), os.path.getsize(p), time.time() - t0))


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    proc = None
    if not api_up():
        proc = start_server()
        if not wait_ready():
            log('[srv] FAIL，看 sd_hero.log')
            if proc:
                proc.terminate()
            return 1
    else:
        log('[srv] 复用')
    try:
        set_model(MODEL)
        for i, (name, label, scene) in enumerate(SHOTS):
            log('[gen] %s  —— %s' % (name, label))
            gen(os.path.join(OUTDIR, name + '.png'), '%s, %s' % (STYLE, scene), seed=5150 + i * 111, n=2)
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
