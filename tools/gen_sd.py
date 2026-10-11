"""用 SD WebUI 的 API 出图（txt2img），base64 解码后落盘。

用法：
  python gen.py --out <输出路径.png> [--model <底模名>] [--width 1344] [--height 756]
                [--steps 28] [--cfg 7] [--seed -1] [--prompt-file <文件>] [--n 1]

设计取舍：
- 不依赖 requests（用标准库 urllib），少一个环境依赖
- 提示词从文件读，避免命令行转义把中文/引号弄坏（踩过一次：引号被 shell 吃掉）
- 每张图的 seed 都打进文件名与日志，便于复现
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.request

API = 'http://127.0.0.1:7860'

# 与 data/art_prompts_round2.json 的 negative_prompt 一致（原文，不改写）
NEGATIVE = (
    'text, letters, characters, watermark, signature, logo, brand, copyright, photorealistic, '
    '3d render, smooth gradients, modern style, anime, high saturation, blurry, noise, '
    'grid lines not aligned'
)

# 正文：提示词库 title_bg 第 1 条 + 安全区约束（标题占画面上中 33.5~66.5% x 3.4~32.4%）
POSITIVE = (
    '16-bit pixel art, morning street in a Ming dynasty town, a poor scholar with a small '
    'writing stall in the foreground, distant city gate and roofs, warm rice-paper sky, '
    'muted earth tones, composition leaves the upper-center empty (plain sky) for a title, '
    'NO text'
)


def post(path, payload, timeout=900):
    req = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--model', default='')
    ap.add_argument('--width', type=int, default=1344)
    ap.add_argument('--height', type=int, default=756)
    ap.add_argument('--steps', type=int, default=28)
    ap.add_argument('--cfg', type=float, default=7.0)
    ap.add_argument('--seed', type=int, default=-1)
    ap.add_argument('--prompt-file', default='')
    ap.add_argument('--n', type=int, default=1)
    a = ap.parse_args()

    positive = POSITIVE
    if a.prompt_file:
        with open(a.prompt_file, 'r', encoding='utf-8') as f:
            positive = f.read().strip()

    if a.model:
        print('[model] 切换底模 -> %s' % a.model, flush=True)
        post('/sdapi/v1/options', {'sd_model_checkpoint': a.model}, timeout=600)
        # 切换后要等它真正加载完
        for i in range(60):
            try:
                opts = post('/sdapi/v1/options', {}, timeout=60)
                if opts.get('sd_model_checkpoint', '').startswith(a.model.split('.')[0]):
                    break
            except Exception:
                pass
            time.sleep(2)

    payload = {
        'prompt': positive,
        'negative_prompt': NEGATIVE,
        'width': a.width,
        'height': a.height,
        'steps': a.steps,
        'cfg_scale': a.cfg,
        'seed': a.seed,
        'batch_size': a.n,
        'sampler_name': 'DPM++ 2M',
        'scheduler': 'Karras',
        'send_images': True,
        'save_images': False,
    }

    print('[gen] %dx%d steps=%d cfg=%s seed=%s n=%d' % (a.width, a.height, a.steps, a.cfg, a.seed, a.n), flush=True)
    t0 = time.time()
    res = post('/sdapi/v1/txt2img', payload)
    dt = time.time() - t0
    imgs = res.get('images', [])
    print('[gen] 完成，耗时 %.1f 秒，返回 %d 张' % (dt, len(imgs)), flush=True)
    if not imgs:
        print('[gen] FAIL 没有返回图像', flush=True)
        return 1

    info = {}
    try:
        info = json.loads(res.get('info', '{}'))
    except Exception:
        pass
    print('[info] seed=%s' % info.get('seed'), flush=True)

    base, ext = os.path.splitext(a.out)
    for i, b64 in enumerate(imgs):
        out = a.out if len(imgs) == 1 else '%s_%02d%s' % (base, i + 1, ext)
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, 'wb') as f:
            f.write(base64.b64decode(b64))
        print('[out] %s  %d bytes' % (out, os.path.getsize(out)), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
