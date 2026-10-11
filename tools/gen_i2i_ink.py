"""img2img 换画风：拿现有 main_bg.png 当构图骨架，用墨水 LoRA 重绘成水墨风。

为什么改走 img2img（txt2img 已连续失败多轮）：
- txt2img 的失败模式是**语义失控**：出人物、出书法字、出印章、出产品摄影 ——
  因为本机底模（动漫/武侠）在"空无一人的明代内景"这个语义上根本没有对应语料
- img2img 把**构图/语义交给已有的图**（main_bg.png 本来就是对的：
  书案 + 笔筒 + 砚台 + 算盘 + 空桌面，且无明显文字），只让模型改**渲染风格**
- 更关键：**可以调 denoising strength** —— 低一点就更像原图（结构稳）、
  高一点风格改得更彻底。这是个连续可调的旋钮，比换提示词靠谱

保留原图的构图 = 顺带保住"中部低细节、UI 面板可读"这个已经验证过的特性。
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
OUTDIR = r'D:\dsh\tmp'
SRC = r'D:\个人项目\daishu\assets\images\backgrounds\main_bg.png'

NEGATIVE = (
    'text, letters, characters, watermark, signature, logo, brand, '
    'calligraphy, handwriting, writing, inscription, chinese characters, kanji, '
    'typed text, captions, labels, posters, newspaper, stamp, seal, wax seal, '
    'person, people, human, figure, portrait, face, hands, '
    'photorealistic, photograph, product shot, 3d render, mockup, '
    'modern style, anime, high saturation, blurry, noise, purple fringing'
)

PROMPT = (
    'traditional Chinese ink wash painting (shuimo), xuan paper texture, '
    'Ming dynasty letter-writing desk seen from above, writing brush, inkstone, '
    'blank paper, soft ink brushstrokes, muted warm earth tones, subtle color wash, '
    'low contrast, plain flat areas, no text, no watermark'
)

# 两组 LoRA × 三档重绘强度：低档更保结构，高档风格更彻底
CASES = [
    ('ink-landscape-sdxl_v2', 0.0),   # 0 = 不装 LoRA，看纯底模能改到什么程度（对照）
    ('ink-landscape-sdxl_v2', 0.45),
    ('ink-landscape-sdxl_v2', 0.65),
    ('chinese-ink-painting_v1', 0.45),
    ('chinese-ink-painting_v1', 0.65),
    ('chinese-ink-painting_v1', 0.80),
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
    # 代理要同时满足两个需求（实测踩过两次）：
    #  ① 外网下载/取模型 -> 不能带代理（本地代理对 huggingface CONNECT 返回 403）
    #  ② gradio 启动自检 localhost -> 需要 NO_PROXY 让本机地址直连
    for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy'):
        env.pop(k, None)
    for k in ('NO_PROXY', 'no_proxy'):
        env[k] = '127.0.0.1,localhost,::1'
    env.update({
        'PYTHON': PY, 'VENV_DIR': '-', 'SKIP_VENV': '1', 'PYTHONIOENCODING': 'utf-8',
        'COMMANDLINE_ARGS': '--api --listen --port 7860 --medvram --xformers --skip-version-check',
    })
    logf = open(os.path.join(OUTDIR, 'sd_i2i_server.log'), 'w', encoding='utf-8', errors='replace')
    p = subprocess.Popen([PY, 'launch.py'], cwd=LAUNCHER, env=env,
                         stdout=logf, stderr=subprocess.STDOUT)
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


def main():
    proc = None
    if not api_up():
        proc = start_server()
        if not wait_ready():
            log('[srv] FAIL 未就绪，看 sd_i2i_server.log')
            if proc:
                proc.terminate()
            return 1
    else:
        log('[srv] 复用')

    with open(SRC, 'rb') as f:
        src_b64 = base64.b64encode(f.read()).decode('ascii')
    log('[src] %s  （当作构图骨架，只改画风）' % os.path.basename(SRC))

    try:
        set_model('waiIllustriousSDXL_v170')
        for lora, strength in CASES:
            if lora and strength == 0.0:
                continue
            prompt = PROMPT
            tag = 'none'
            if lora:
                tag = lora.replace('.safetensors', '')
                prompt = '%s <lora:%s:0.85>' % (PROMPT, lora)
            name = 'i2i_%s_d%02d.png' % (tag, int(strength * 100))
            payload = {
                'init_images': [src_b64],
                'prompt': prompt,
                'negative_prompt': NEGATIVE,
                'denoising_strength': strength,
                'steps': 28, 'cfg_scale': 7.0, 'seed': 20261012,
                'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
                'width': 1152, 'height': 648,
                'send_images': True, 'save_images': False,
            }
            log('[i2i] %-34s denoise=%.2f' % (name, strength))
            t0 = time.time()
            res = post('/sdapi/v1/img2img', payload)
            log('[i2i] %.1fs' % (time.time() - t0))
            out = os.path.join(OUTDIR, name)
            imgs = res.get('images', [])
            if imgs:
                with open(out, 'wb') as f:
                    f.write(base64.b64decode(imgs[0]))
                log('[out] %s %d B' % (out, os.path.getsize(out)))
            else:
                log('[out] FAIL 无图')
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
