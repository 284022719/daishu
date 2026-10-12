"""带断点续传与进度落盘的下载器（网络只有 0.17 MB/s，必须能续、能看进度）。

为什么要续传：实测这台机器到 HF/Civitai 的大文件速率稳定在 **0.17 MB/s**
（分三段各量 10MB：0.16 / 0.18 / 0.16），4 GB ≈ 7 小时。
这种量级一旦中断从头再来不可接受。

进度写进同目录的 .partial.json，便于外部随时查看。
"""
import json
import os
import sys
import time

import requests

DEST = r'D:\绘世启动器\models\Stable-diffusion'
HEADERS = {'User-Agent': 'Mozilla/5.0'}

TARGETS = [
    ('oukaGufeng_s1.safetensors',
     'https://civitai.com/api/download/models/102214'),
    ('GuFeng2.safetensors',
     'https://huggingface.co/xiaolxl/GuFeng/resolve/main/GuFeng2.safetensors'),
]


def fetch(name, url):
    out = os.path.join(DEST, name)
    prog = out + '.partial.json'
    have = os.path.getsize(out) if os.path.exists(out) else 0

    h = dict(HEADERS)
    if have:
        h['Range'] = 'bytes=%d-' % have
    try:
        r = requests.get(url, headers=h, stream=True, timeout=(20, 60), allow_redirects=True)
    except Exception as e:
        print('  [%s] 连接失败 %s' % (name, str(e)[:100]))
        return False

    ct = r.headers.get('content-type', '')
    if r.status_code == 200 and 'text/html' in ct:
        print('  [%s] ❌ 拿到的是 HTML（需登录），放弃' % name)
        r.close()
        return False
    if r.status_code not in (200, 206):
        print('  [%s] ❌ HTTP %s' % (name, r.status_code))
        r.close()
        return False

    total = int(r.headers.get('content-length') or 0) + (have if r.status_code == 206 else 0)
    mode = 'ab' if r.status_code == 206 else 'wb'
    if r.status_code == 200 and have:
        have = 0                      # 服务端不支持续传，从头写
    print('  [%s] 续传自 %d B / 共 %s' % (name, have, ('%.2f GB' % (total / 1073741824)) if total else '?'))

    t0 = time.time()
    n = have
    last_report = 0
    with open(out, mode) as f:
        for chunk in r.iter_content(1 << 20):
            if not chunk:
                continue
            f.write(chunk)
            n += len(chunk)
            if time.time() - last_report >= 20:
                last_report = time.time()
                el = time.time() - t0
                sp = (n - have) / 1048576 / max(el, 1e-9)
                eta = (total - n) / 1048576 / max(sp, 1e-9) / 60 if total else 0
                state = {'file': name, 'have': n, 'total': total,
                         'speed_MBps': round(sp, 3), 'eta_min': round(eta, 1),
                         'ts': time.strftime('%H:%M:%S')}
                try:
                    with open(prog, 'w', encoding='utf-8') as pf:
                        json.dump(state, pf, ensure_ascii=False)
                except Exception:
                    pass
                print('       %.2f/%.2f GB  %.2f MB/s  ETA %.0f min' % (
                    n / 1073741824, total / 1073741824 if total else 0, sp, eta), flush=True)
    if os.path.exists(prog):
        os.remove(prog)
    print('  [%s] ✅ 完成 %.2f GB' % (name, os.path.getsize(out) / 1073741824))
    return True


for name, url in TARGETS:
    print('=== %s ===' % name)
    ok = fetch(name, url)
    if not ok:
        print('  （跳过，继续下一个）')
    print()
print('done')
