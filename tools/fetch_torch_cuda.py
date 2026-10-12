"""给 ComfyUI 的 venv 装 CUDA 版 torch（唯一来源是 pytorch 官方源，约 0.5 MB/s）。

为什么要单独写：官方源 2.33 GB、实测 0.53~0.78 MB/s ⇒ **约 60~75 分钟**，
必须带**断点续传**（venv 之前那次就是挂住白等 30 分钟）。
下载完用本地 wheel 安装（不走 pip 的网络解析，避免再挂）。
"""
import os
import sys
import time

import requests

DEST = r'D:\dsh\tmp\torch_whl'
os.makedirs(DEST, exist_ok=True)
URL = ('https://download.pytorch.org/whl/cu124/'
       'torch-2.4.0%2Bcu124-cp310-cp310-win_amd64.whl')
OUT = os.path.join(DEST, 'torch-2.4.0+cu124-cp310-cp310-win_amd64.whl')
H = {'User-Agent': 'pip/24'}


def main():
    have = os.path.getsize(OUT) if os.path.exists(OUT) else 0
    h = dict(H)
    if have:
        h['Range'] = 'bytes=%d-' % have
    r = requests.get(URL, headers=h, stream=True, timeout=(20, 60), allow_redirects=True)
    if r.status_code not in (200, 206):
        print('HTTP %s' % r.status_code)
        return 1
    total = int(r.headers.get('content-length') or 0) + (have if r.status_code == 206 else 0)
    if r.status_code == 200 and have:
        have, mode = 0, 'wb'
    else:
        mode = 'ab' if have else 'wb'
    print('续传自 %.2f GB / 共 %.2f GB' % (have / 1e9, total / 1e9), flush=True)

    t0 = time.time()
    n = have
    last = 0
    with open(OUT, mode) as f:
        for chunk in r.iter_content(1 << 20):
            if not chunk:
                continue
            f.write(chunk)
            n += len(chunk)
            if time.time() - last >= 30:
                last = time.time()
                sp = (n - have) / 1048576 / max(time.time() - t0, 1e-9)
                eta = (total - n) / 1048576 / max(sp, 1e-9) / 60 if total else 0
                print('  %.2f/%.2f GB  %.2f MB/s  ETA %.0f min' % (
                    n / 1e9, total / 1e9 if total else 0, sp, eta), flush=True)
    print('下载完成 %.2f GB' % (os.path.getsize(OUT) / 1e9), flush=True)
    print('WHEEL=' + OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
