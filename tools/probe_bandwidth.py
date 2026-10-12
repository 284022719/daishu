"""带宽基线测试：区分"普遍慢"还是"海外 CDN 慢"。

为什么必须先做这个：模型下载实测 0.14~0.25 MB/s（HF 与 Civitai 都一样）。
若这是**本机普遍带宽**，那换站/换工具/换模型全都白搭，只能改走外部出图；
若只是**跨境链路慢**，那走国内站或镜像就有救。
判据就是拿几个不同性质的主机各测 3MB 比一比。
"""
import time

import requests

HEADERS = {'User-Agent': 'Mozilla/5.0'}
TESTS = [
    ('GitHub Releases（海外）', 'https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe'),
    ('PyPI 文件（海外 CDN）', 'https://files.pythonhosted.org/packages/source/s/six/six-1.16.0.tar.gz'),
    ('npm registry（海外）', 'https://registry.npmjs.org/typescript/-/typescript-5.4.5.tgz'),
    ('国内 CDN 探针（阿里）', 'https://registry.npmmirror.com/typescript/-/typescript-5.4.5.tgz'),
    ('HuggingFace（海外）', 'https://huggingface.co/xiaolxl/GuFeng/resolve/main/README.md'),
]
LIMIT = 3 * 1024 * 1024

for name, url in TESTS:
    try:
        t0 = time.time()
        got = 0
        with requests.get(url, headers=HEADERS, stream=True, timeout=(15, 30), allow_redirects=True) as r:
            if r.status_code != 200:
                print('  %-26s HTTP %s' % (name, r.status_code))
                continue
            for chunk in r.iter_content(1 << 16):
                got += len(chunk)
                if got >= LIMIT:
                    break
        dt = time.time() - t0
        print('  %-26s %5.2f MB / %6.1fs = %6.2f MB/s' % (name, got / 1048576, dt, got / 1048576 / max(dt, 1e-9)))
    except Exception as e:
        print('  %-26s FAIL %s' % (name, str(e).replace('\n', ' ')[:80]))

print()
print('判读：若"国内 CDN"明显快于其他 → 瓶颈是跨境链路，走国内源可解；')
print('      若全都 ~0.2 MB/s → 是本机带宽/链路整体受限，换站无用。')
