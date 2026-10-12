"""下载 SDXL 风格 LoRA（本机唯一能补上"风格控制"的东西）。

为什么这是关键一步：
  前几轮反复卡在"底模不服从风格词"（提示词写 flat illustration 仍出照片级写实）。
  **LoRA 是训练出来的风格权重**，不受提示词服从度影响 —— 这才是正解。

选型（都标 SDXL，能配本机 6.46GB 的 SDXL 底模）：
  vector-illustration      矢量扁平插画（最像"干净的 UI 底图"）
  flat_cartoon_illustration 平涂漫画插画
  line-art                 线稿
  watercolor_style_sdxl     水彩
另下一个 ChineseInkStyle 备用（万一回头要水墨）。
"""
import os
import sys
import time

import requests

DEST = r'D:\绘世启动器\models\Lora'
os.makedirs(DEST, exist_ok=True)
H = {'User-Agent': 'Mozilla/5.0'}
REPO = 'https://modelscope.cn/api/v1/models/%s/repo?Revision=master&FilePath=%s'
HEAD = 'https://modelscope.cn/api/v1/models/%s/repo/files?Revision=master'

TARGETS = [
    # (repo, 文件名, 本地保存名, 说明)
    ('SDXL-LoRA/taki0112-lora-trained-xl_vector-illustrations_split',
     'pytorch_lora_weights.safetensors', 'sdxl_vector-illustration.safetensors', '矢量插画'),
    ('SDXL-LoRA/Changg-model_flat_cartoon_illustration_obj_dog',
     'pytorch_lora_weights.safetensors', 'sdxl_flat-cartoon.safetensors', '平涂漫画'),
    ('SDXL-LoRA/taki0112-lora-trained-xl_line-art',
     'pytorch_lora_weights.safetensors', 'sdxl_line-art.safetensors', '线稿'),
    ('ostris/watercolor_style_lora_sdxl',
     'watercolor_v1_sdxl.safetensors', 'sdxl_watercolor.safetensors', '水彩'),
    ('sd_lora/zyd232_ChineseInkStyle_SDXL_v1_0',
     'zyd232_ChineseInkStyle_SDXL_v1_0.safetensors', 'sdxl_chinese-ink.safetensors', '中国水墨'),
]


def fetch(repo, fname, local, note):
    out = os.path.join(DEST, local)
    if os.path.exists(out) and os.path.getsize(out) > 100 * 1024:
        print('  [skip] %-34s 已存在 %.1f MB' % (local, os.path.getsize(out) / 1048576))
        return True
    url = REPO % (repo, fname)
    try:
        t0 = time.time()
        with requests.get(url, headers=H, stream=True, timeout=(20, 60), allow_redirects=True) as r:
            if r.status_code != 200:
                print('  [fail] %-34s HTTP %s' % (local, r.status_code))
                return False
            total = int(r.headers.get('content-length') or 0)
            n = 0
            with open(out, 'wb') as f:
                for c in r.iter_content(1 << 20):
                    if not c:
                        continue
                    f.write(c)
                    n += len(c)
        dt = time.time() - t0
        ok = (not total) or n == total
        print('  [%s] %-34s %6.1f MB  %.1fs  %s  (%s)'
              % ('ok ' if ok else 'BAD', local, n / 1048576, dt, note,
                 '字节一致' if ok else '字节不符 %d/%d' % (n, total)))
        return ok
    except Exception as e:
        print('  [fail] %-34s %s' % (local, str(e).replace('\n', ' ')[:100]))
        if os.path.exists(out):
            os.remove(out)
        return False


ok = 0
for repo, fname, local, note in TARGETS:
    if fetch(repo, fname, local, note):
        ok += 1
print()
print('=== %d/%d 成功 ===' % (ok, len(TARGETS)))
print('=== models/Lora 现状 ===')
for f in sorted(os.listdir(DEST)):
    if f.endswith('.safetensors'):
        print('  %-46s %7.1f MB' % (f, os.path.getsize(os.path.join(DEST, f)) / 1048576))
sys.exit(0 if ok else 1)
