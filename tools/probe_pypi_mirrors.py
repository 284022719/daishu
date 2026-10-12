"""正确地测 PyPI 镜像的**文件下载**速度（不是只测索引页）。

上次的 bug：镜像索引里 wheel 链接是相对路径 `../../packages/...`，
我手工拼 URL 拼错了，得到 "Invalid URL"。必须用 urljoin 解析。
"""
import re
import time
from urllib.parse import urljoin

import requests

H = {'User-Agent': 'pip/24'}
MIRRORS = [
    ('aliyun', 'https://mirrors.aliyun.com/pypi/simple/pydantic/'),
    ('tsinghua', 'https://pypi.tuna.tsinghua.edu.cn/simple/pydantic/'),
    ('ustc', 'https://mirrors.ustc.edu.cn/pypi/simple/pydantic/'),
    ('tencent', 'https://mirrors.cloud.tencent.com/pypi/simple/pydantic/'),
    ('pypi.org', 'https://pypi.org/simple/pydantic/'),
]

for name, idx in MIRRORS:
    try:
        t0 = time.time()
        r = requests.get(idx, headers=H, timeout=(10, 25))
        if r.status_code != 200:
            print('  %-10s 索引 HTTP %s' % (name, r.status_code))
            continue
        # 找一个 wheel 链接，正确解析相对路径
        m = re.search(r'href="([^"]+pydantic-2\.[0-9.]+-py3-none-any\.whl[^"]*)"', r.text)
        if not m:
            print('  %-10s 索引 OK(%.2fs) 但没找到 2.x wheel 链接' % (name, time.time() - t0))
            continue
        wheel = urljoin(idx, m.group(1))
        t1 = time.time()
        rr = requests.get(wheel, headers=H, timeout=(10, 25), stream=True)
        got = 0
        for c in rr.iter_content(1 << 16):
            got += len(c)
            if got >= 500 * 1024:
                break
        dt = time.time() - t1
        print('  %-10s 索引 %.2fs | 文件 HTTP %s  %d B / %.2fs = %.2f MB/s' % (
            name, t0 and (time.time() - t0 - dt), rr.status_code, got, dt,
            got / 1048576 / max(dt, 1e-9)))
    except Exception as e:
        print('  %-10s FAIL %s' % (name, str(e).replace('\n', ' ')[:80]))
