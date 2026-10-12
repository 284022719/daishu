"""筛出**能配本机 SD1.5/SDXL 底模**的风格模型（排除需要 FLUX/Qwen 的）。

为什么这步关键：
  上面搜出来一大堆 LoRA，但多数是 **FLUX** 或 **Qwen** 的 —— 本机没有那些底模，下了也用不了。
  必须看清每个候选的**基座要求**（文件名/README/标签里通常写了 flux / qwen / sdxl / sd15）。

本机可用基座：SD1.5（3Guofeng3_v34、国风武侠、v1-5）与 SDXL（4Guofeng4XL、Illustrious 等）。
策略：优先找 **SDXL 风格 LoRA**（配 SDXL 底模），因为 SDXL 画质更好且本机有 6.46GB 底模。
"""
import re
import sys

import requests

H = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
     'Content-Type': 'application/json'}
SEARCH = 'https://modelscope.cn/api/v1/dolphin/models'
EXT = ('.safetensors', '.ckpt')

QUERIES = ['flat illustration sdxl', 'illustration sdxl', 'gouache sdxl', 'chinese style sdxl',
           'line art sdxl', 'watercolor sdxl', 'storybook sdxl']

rows = []
for q in QUERIES:
    try:
        r = requests.put(SEARCH, json={'Name': q, 'PageSize': 12, 'PageNumber': 1,
                                       'SortBy': 'DownloadsCount'}, headers=H, timeout=30)
        if r.status_code != 200:
            continue
        ms = ((r.json().get('Data') or {}).get('Model') or {}).get('Models') or []
        for m in ms:
            full = '%s/%s' % (m.get('Path') or m.get('Owner') or '?', m.get('Name'))
            rows.append((full, m.get('Downloads')))
    except Exception:
        pass

# 去重
seen = {}
for full, dl in rows:
    seen.setdefault(full, dl)

BASE_BAD = ('flux', 'qwen', 'kontext', 'z-image', 'zimage', 'sdxl-turbo', 'pony-diffusion-v6')
BASE_SDXL = ('sdxl', 'xl')
BASE_SD15 = ('sd1.5', 'sd15', 'sd-1-5', 'v1-5')

print('=== 逐个查基座类型 ===')
ok = []
for full, dl in seen.items():
    low = full.lower()
    try:
        r = requests.get('https://modelscope.cn/api/v1/models/%s/repo/files' % full,
                         params={'Revision': 'master'}, headers=H, timeout=25)
        if r.status_code != 200:
            continue
        files = (r.json().get('Data') or {}).get('Files') or []
        mods = [f for f in files if str(f.get('Path', '')).lower().endswith(EXT)]
        if not mods:
            continue
        names = ' '.join(str(f.get('Path', '')).lower() for f in files) + ' ' + low
        # 判基座：名字/文件里是否明确写了 flux / qwen
        if any(b in names for b in BASE_BAD):
            kind = 'FLUX/Qwen（本机不可用）'
        elif any(b in names for b in BASE_SDXL):
            kind = 'SDXL（本机可用）'
        elif any(b in names for b in BASE_SD15):
            kind = 'SD1.5（本机可用）'
        else:
            kind = '未知'
        biggest = max(mods, key=lambda f: f.get('Size') or 0)
        sz = (biggest.get('Size') or 0) / 1073741824
        print('  %-14s %-54s %-30s %5.2f GB  下载 %s'
              % (kind, full[:54], str(biggest.get('Path'))[:30], sz, dl))
        if '可用' in kind:
            ok.append((full, biggest.get('Path'), sz, kind))
    except Exception:
        pass

print()
print('=== 可用的 %d 个（建议下载试）===' % len(ok))
for full, path, sz, kind in ok:
    print('  %-56s %-34s %5.2f GB  %s' % (full, path, sz, kind))
