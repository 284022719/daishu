"""从 modelscope（国内源，实测 7.2 MB/s）下载国风底模。

为什么这次能行：
  代理开着时所有流量被压到 0.11 MB/s（且 HF/GitHub 直连 403）；
  **代理关闭后** —— 海外直连不通，但**国内源 7.2 MB/s**，比之前快 65 倍。
  所以走 modelscope（阿里），下载 6.46 GB 约 15 分钟。

已确认的 modelscope 接口形态：
  文件表: GET /api/v1/models/{owner}/{name}/repo/files?Revision=master
  下载:   GET /api/v1/models/{owner}/{name}/repo?Revision=master&FilePath={file}
"""
import os
import sys
import time

import requests

H = {'User-Agent': 'Mozilla/5.0'}
DEST = r'D:\绘世启动器\models\Stable-diffusion'
os.makedirs(DEST, exist_ok=True)

TARGETS = [
    # (repo, 文件名)  —— 6.46GB SDXL 国风，与本机 SDXL 底模同架构
    ('NickYuan/4Guofeng4XL_v1125D', '4Guofeng4XL_v1125D.safetensors'),
    # 2.14GB SD1.5 国风，做备选（更快出图）
    ('mixLine/Guofeng3', '3Guofeng3_v34.safetensors'),
]

URL = 'https://modelscope.cn/api/v1/models/%s/repo?Revision=master&FilePath=%s'


def fetch(repo, fname):
    out = os.path.join(DEST, fname)
    have = os.path.getsize(out) if os.path.exists(out) else 0
    url = URL % (repo, fname)

    h = dict(H)
    if have:
        h['Range'] = 'bytes=%d-' % have
    r = requests.get(url, headers=h, stream=True, timeout=(20, 60), allow_redirects=True)
    if r.status_code not in (200, 206):
        print('  [%s] HTTP %s' % (fname, r.status_code))
        return False
    ct = r.headers.get('content-type', '')
    if 'text/html' in ct or 'json' in ct:
        print('  [%s] ❌ 拿到非模型内容（%s）' % (fname, ct))
        return False

    total = int(r.headers.get('content-length') or 0) + (have if r.status_code == 206 else 0)
    if r.status_code == 200 and have:
        have = 0
        mode = 'wb'
    else:
        mode = 'ab' if have else 'wb'
    print('  [%s] 开始（已有 %.2f GB / 共 %.2f GB）' % (fname, have / 1e9, total / 1e9 if total else 0))

    t0 = time.time()
    n = have
    last = 0
    with open(out, mode) as f:
        for chunk in r.iter_content(1 << 20):
            if not chunk:
                continue
            f.write(chunk)
            n += len(chunk)
            if time.time() - last >= 15:
                last = time.time()
                el = time.time() - t0
                sp = (n - have) / 1048576 / max(el, 1e-9)
                eta = (total - n) / 1048576 / max(sp, 1e-9) / 60 if total else 0
                print('       %.2f/%.2f GB  %.2f MB/s  ETA %.1f min' % (
                    n / 1e9, total / 1e9 if total else 0, sp, eta), flush=True)
    ok = (not total) or (n == total)
    print('  [%s] %s  %.2f GB' % (fname, '✅ 完成' if ok else '⚠️ 字节不符', os.path.getsize(out) / 1e9))
    return ok


for repo, fname in TARGETS:
    print('=== %s ===' % repo)
    try:
        fetch(repo, fname)
    except Exception as e:
        print('  FAIL %s' % str(e).replace('\n', ' ')[:140])
    print()

print('=== models/Stable-diffusion 现状 ===')
for f in sorted(os.listdir(DEST)):
    if f.endswith(('.safetensors', '.ckpt')):
        print('  %-48s %6.2f GB' % (f, os.path.getsize(os.path.join(DEST, f)) / 1073741824))
