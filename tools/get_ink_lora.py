"""下载水墨风格 LoRA 并校验（小文件，值得直接试）。

为什么走 LoRA 而不是换底模：
- 本机已有 3 个 SDXL 底模，缺的只是"水墨风格"
- 水墨 LoRA 只 0.16~0.85 GB，而换底模要 6.5 GB（本机 4.2 MB/s → 26 分钟）
- LoRA 可以叠加、可调权重、不满意就删

注意：LoRA 只改**风格**，不改底模"爱画人"的倾向 ——
所以"空无一人"仍要靠负面提示词/构图约束，这点要如实预期。
"""
import os
import sys
import time

import requests

DEST = r'D:\绘世启动器\models\Lora'
os.makedirs(DEST, exist_ok=True)

HEADERS = {'User-Agent': 'Mozilla/5.0'}
CANDIDATES = [
    # (显示名, Civitai modelVersionId, 目标文件名)
    ('国画水墨山水 SDXL v2 (0.16GB)', 149480, 'ink-landscape-sdxl_v2.safetensors'),
    ('造物云 中国水墨画 V1 (0.85GB)', 171579, 'chinese-ink-painting_v1.safetensors'),
]

def download(name, vid, fname):
    url = 'https://civitai.com/api/download/models/%d' % vid
    out = os.path.join(DEST, fname)
    if os.path.exists(out) and os.path.getsize(out) > 1024 * 1024:
        print('  [skip] %s 已存在 %.1f MB' % (fname, os.path.getsize(out) / 1048576))
        return True
    print('  [get ] %s' % name)
    try:
        t0 = time.time()
        with requests.get(url, headers=HEADERS, stream=True, timeout=120, allow_redirects=True) as r:
            if r.status_code != 200:
                print('        HTTP %s（该版本可能要登录或已下架）' % r.status_code)
                return False
            total = int(r.headers.get('content-length') or 0)
            n = 0
            with open(out, 'wb') as f:
                for chunk in r.iter_content(1 << 20):
                    if not chunk:
                        continue
                    f.write(chunk)
                    n += len(chunk)
        dt = time.time() - t0
        mb = n / 1048576
        print('        OK  %.1f MB / %.1fs = %.2f MB/s  -> %s' % (mb, dt, mb / max(dt, 1e-9), out))
        if total and n != total:
            print('        ⚠️ 字节数不符：预期 %d 实得 %d' % (total, n))
            return False
        return True
    except Exception as e:
        print('        FAIL %s' % str(e).replace('\n', ' ')[:140])
        if os.path.exists(out):
            os.remove(out)
        return False


ok = 0
for name, vid, fname in CANDIDATES:
    if download(name, vid, fname):
        ok += 1
print()
print('=== 结果：%d/%d 成功 ===' % (ok, len(CANDIDATES)))
for f in sorted(os.listdir(DEST)):
    p = os.path.join(DEST, f)
    if f.endswith('.safetensors'):
        print('  %-46s %8.2f MB' % (f, os.path.getsize(p) / 1048576))
sys.exit(0 if ok else 1)
