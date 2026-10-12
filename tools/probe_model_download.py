"""诊断：Civitai 直链为什么 10 分钟 0 字节（HEAD 200 但 GET 挂住）。

要点：**读 chunk 要自己设超时**。requests 的 timeout 是"连接/两包之间"的超时，
对流式下载若服务端长时间不发数据又不关连接，可能一直挂着不报错。
所以这里用 (connect, read) 元组显式设 read 超时，并在前几个包就判定通不通。
"""
import sys
import time

import requests

HEADERS = {'User-Agent': 'Mozilla/5.0'}
CAND = [
    ('Epic Landscapes', 577006),
    ('ouka_gufeng', 102214),
]

for name, vid in CAND:
    url = 'https://civitai.com/api/download/models/%d' % vid
    print('=== %s ===' % name)
    print('  URL %s' % url)
    try:
        t0 = time.time()
        # (connect, read) —— read 超时 30 秒，若 30 秒收不到数据就报错而不是无限等
        with requests.get(url, headers=HEADERS, stream=True, timeout=(15, 30),
                          allow_redirects=True) as r:
            print('  HTTP %s' % r.status_code)
            print('  最终 URL: %s' % (r.url[:120]))
            print('  content-length: %s' % r.headers.get('content-length'))
            print('  content-type: %s' % r.headers.get('content-type'))
            print('  headers: %s' % dict(list(r.headers.items())[:6]))
            got = 0
            t1 = time.time()
            for chunk in r.iter_content(1 << 20):
                got += len(chunk)
                if got >= 3 * 1024 * 1024:      # 收满 3 MB 就够判定
                    break
                if time.time() - t1 > 60:
                    print('  ⚠️ 60 秒内只收到 %d B' % got)
                    break
            dt = time.time() - t1
            print('  首 3MB: 收到 %d B / %.1fs = %.2f MB/s' % (got, dt, got / 1048576 / max(dt, 1e-9)))
            if got == 0:
                # 看看响应体到底是什么（可能是 JSON 错误、付费墙、需要登录）
                print('  收到 0 字节，尝试读取响应体前 300 字节：')
                try:
                    body = r.raw.read(300)
                    print('    %r' % body)
                except Exception as e:
                    print('    读取失败 %s' % e)
    except Exception as e:
        print('  FAIL %s' % str(e).replace('\n', ' ')[:200])
    print()

sys.exit(0)
