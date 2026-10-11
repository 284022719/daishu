"""极简水墨纸本方案：一张"宣纸 + 淡墨 + 底部书案暗示"的底图。

为什么试这个方向（第三轮之后）：
- 主界面 UI 面板是半透明的（alpha 0.78）且占画面中部，底图**越简单越不干扰读字**
- 前面几轮试图出"写实内景"，被本机底模的语料（武侠人物/动漫插画）反复带偏：
  要不出人物、要不结构崩、要不出现紫色伪影
- 这一版的失败模式**最温和**：最差也只是"一片纸"，不会出人物、不会出文字

同时对比两个底模，看哪个的水墨质感更接近 main.png（锚点：相邻差 12.1 / 平均色 #a29a81）。
"""
import base64
import json
import os
import sys
import time
import urllib.request

API = 'http://127.0.0.1:7860'
NEGATIVE = (
    'text, letters, characters, watermark, signature, logo, brand, '
    'calligraphy, handwriting, writing, inscription, chinese characters, kanji, '
    'person, people, human, figure, portrait, face, hands, '
    'photorealistic, 3d render, modern style, anime, high saturation, blurry, noise, '
    'oil painting, thick impasto, purple fringing, chromatic aberration'
)
PROMPT = open(r'D:\dsh\tmp\ink_paper.txt', encoding='utf-8').read().strip()
OUTDIR = r'D:\dsh\tmp'


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


def set_model(name):
    print('[model] -> %s' % name, flush=True)
    post('/sdapi/v1/options', {'sd_model_checkpoint': name}, timeout=900)
    want = name.split('.')[0]
    for _ in range(90):
        try:
            if get_json('/sdapi/v1/options', 30).get('sd_model_checkpoint', '').startswith(want):
                print('[model] 就绪', flush=True)
                return True
        except Exception:
            pass
        time.sleep(3)
    print('[model] WARN 超时', flush=True)
    return False


def gen(out, width, height, steps, seed, n=1):
    payload = {'prompt': PROMPT, 'negative_prompt': NEGATIVE, 'width': width, 'height': height,
               'steps': steps, 'cfg_scale': 7.0, 'seed': seed, 'batch_size': n,
               'sampler_name': 'DPM++ 2M', 'scheduler': 'Karras',
               'send_images': True, 'save_images': False}
    print('[gen] %s %dx%d steps=%d n=%d' % (os.path.basename(out), width, height, steps, n), flush=True)
    t0 = time.time()
    res = post('/sdapi/v1/txt2img', payload)
    print('[gen] %.1fs' % (time.time() - t0), flush=True)
    base, ext = os.path.splitext(out)
    for i, b64 in enumerate(res.get('images', [])):
        p = out if len(res['images']) == 1 else '%s_%02d%s' % (base, i + 1, ext)
        with open(p, 'wb') as f:
            f.write(base64.b64decode(b64))
        print('[out] %s %d B' % (p, os.path.getsize(p)), flush=True)


def main():
    # SDXL 版（画质通常更稳，慢一些）
    if set_model('waiIllustriousSDXL_v170'):
        gen(os.path.join(OUTDIR, 'ink_paper_sdxl.png'), 1152, 648, 28, 424242, n=3)
    # SD1.5 国风版（快）
    if set_model('国风武侠Chinese style'):
        gen(os.path.join(OUTDIR, 'ink_paper_guofeng.png'), 1152, 648, 28, 424242, n=3)
    print('[done]', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
