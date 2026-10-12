"""用 inpainting 抹掉底图上的文字（这是"禁文字"硬规矩的治本做法）。

背景：实测发现 **main.png 本身带文字** —— 市井幌子上有「茶」「米」「布」。
这也解释了为什么 img2img 改画风后文字还在：**低重绘强度会忠实保留原图内容**。

做法：给文字区域做 **mask**（白=重绘区），走 WebUI 的 `/sdapi/v1/img2img`
（它原生支持 mask 字段，见 modules/api/api.py:499-501,515），
用"干净的同色布面"作提示词把字抹掉，**其余区域不重绘**。

关键参数：
  mask_blur      —— 边缘羽化，避免补丁边界可见
  inpainting_fill=1 (original) —— 用原图铺底，只重绘 mask 区
  denoising_strength 要高（0.75+），否则抹不掉字

抹完自动校验：统计文字区域内的"墨色/高对比笔画"像素占比，应显著下降。
"""
import base64
import io
import json
import os
import subprocess
import sys
import time
import urllib.request

from PIL import Image, ImageDraw, ImageFilter

LAUNCHER = r'D:\绘世启动器'
PY = os.path.join(LAUNCHER, '.ext', 'python.exe')
API = 'http://127.0.0.1:7860'
OUT = r'D:\dsh\tmp\inpaint'
os.makedirs(OUT, exist_ok=True)

# 要处理的图 + 文字区域（相对坐标 x0,y0,x1,y1）
# 依据：目视 main.png / main_bg.png 上幌子的位置
TARGETS = [
    ('main', r'D:\个人项目\daishu\assets\images\backgrounds\main.png',
     [(0.222, 0.058, 0.318, 0.290),      # 左「茶」幌
      (0.283, 0.330, 0.365, 0.545),      # 左「米」幌
      (0.745, 0.083, 0.845, 0.300),      # 右「布」幌
      (0.790, 0.330, 0.880, 0.560)]),    # 右下「布/市」幌
    ('main_bg', r'D:\个人项目\daishu\assets\images\backgrounds\main_bg.png',
     [(0.560, 0.055, 0.660, 0.230),      # 上部「布」幌
      (0.185, 0.150, 0.280, 0.330)]),    # 左「茶」幌
]

PROMPT = ('plain empty cloth shop banner, blank fabric surface, soft folds, '
          'warm beige fabric, matching surrounding illustration style, no text, '
          'no characters, no writing, no pattern')
NEGATIVE = ('text, letters, characters, words, writing, calligraphy, chinese characters, '
            'kanji, hanzi, seal, stamp, signature, logo, watermark, pattern, symbol, '
            'noise, blurry, jpeg artifacts')


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
    for _ in range(120):
        try:
            cur = get_json('/sdapi/v1/options', 30).get('sd_model_checkpoint', '')
        except Exception:
            cur = ''
        if fname in cur:
            log('[model] ✅ %s' % cur)
            return True
        time.sleep(3)
    return False


def make_mask(size, boxes, blur=8):
    """白 = 要重绘的区域。boxes 是相对坐标。"""
    w, h = size
    m = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(m)
    for (x0, y0, x1, y1) in boxes:
        d.rectangle([int(w * x0), int(h * y0), int(w * x1), int(h * y1)], fill=255)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    return m


def stroke_ratio(img, boxes):
    """文字区域内"高对比笔画"占比：相邻像素亮度跳变大 = 像字。"""
    g = img.convert('L')
    w, h = g.size
    px = g.load()
    tot = 0
    edge = 0
    for (x0, y0, x1, y1) in boxes:
        for y in range(int(h * y0) + 1, int(h * y1), 2):
            for x in range(int(w * x0) + 1, int(w * x1), 2):
                tot += 1
                if abs(px[x, y] - px[x - 1, y]) > 40 or abs(px[x, y] - px[x, y - 1]) > 40:
                    edge += 1
    return edge / max(1, tot)


def main():
    proc = None
    if not api_up():
        proc = start_server()
        if not wait_ready():
            if proc:
                proc.terminate()
            return 1
    try:
        if not switch_model('3Guofeng3_v34.safetensors'):
            log('[abort] 底模未确认')
            return 1
        for tag, path, boxes in TARGETS:
            img = Image.open(path).convert('RGB')
            log('[%s] 尺寸 %s  文字区 %d 处  原笔画占比 %.3f'
                % (tag, img.size, len(boxes), stroke_ratio(img, boxes)))
            w, h = img.size
            # 送进 SD 的底图缩到 1152x648（16:9，与原图同比例），抹完再放大回原尺寸
            work = img.resize((1152, 648), Image.LANCZOS)
            mask = make_mask((1152, 648), boxes)
            work.save(os.path.join(OUT, '%s_work.png' % tag))
            mask.save(os.path.join(OUT, '%s_mask.png' % tag))
            payload = {
                'init_images': [base64.b64encode(open(os.path.join(OUT, '%s_work.png' % tag), 'rb').read()).decode()],
                'mask': base64.b64encode(open(os.path.join(OUT, '%s_mask.png' % tag), 'rb').read()).decode(),
                'prompt': PROMPT,
                'negative_prompt': NEGATIVE,
                'denoising_strength': 0.80,
                'inpainting_fill': 1,          # original：只改 mask 区
                'inpaint_full_res': True,
                'inpaint_full_res_padding': 32,
                'mask_blur': 8,
                'steps': 30, 'cfg_scale': 7.0, 'seed': 1234,
                'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
                'width': 1152, 'height': 648,
                'send_images': True, 'save_images': False,
            }
            t0 = time.time()
            try:
                res = post('/sdapi/v1/img2img', payload)
            except Exception as e:
                log('[%s] inpainting 失败 %s' % (tag, str(e)[:120]))
                continue
            imgs = res.get('images', [])
            if not imgs:
                log('[%s] 无返回图' % tag)
                continue
            out = Image.open(io.BytesIO(base64.b64decode(imgs[0]))).convert('RGB')
            r2 = stroke_ratio(out, boxes)
            log('[%s] ✅ 抹后笔画占比 %.3f  （原 %.3f）  %.0fs'
                % (tag, r2, stroke_ratio(img, boxes), time.time() - t0))
            # 放大回原尺寸（保持与原文件同尺寸，避免影响锚点/引用）
            final = out.resize((w, h), Image.LANCZOS)
            p = os.path.join(OUT, '%s_clean.png' % tag)
            final.save(p)
            log('[out] %s  %s' % (p, final.size))
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
