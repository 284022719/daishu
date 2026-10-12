"""在 modelscope 上搜"本身就是插画/平涂/矢量风格"的底模 —— 换风格的正解。

为什么换思路：
  前几轮一直在"用通用底模 + 提示词"去求插画风，实测**底模不服从风格词**
  （提示词写 flat illustration / no photographic texture 仍出照片级写实）。
  正确的做法是**换一个训练语料本身就是插画/平涂的底模** —— 风格由权重决定，不由提示词决定。

modelscope 接口形态（已实测）：
  搜索 PUT /api/v1/dolphin/models  body {Name, PageSize, PageNumber}
  文件表 GET /api/v1/models/{owner}/{name}/repo/files?Revision=master
  下载   GET /api/v1/models/{owner}/{name}/repo?Revision=master&FilePath={file}
"""
import sys

import requests

H = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
     'Content-Type': 'application/json'}
SEARCH = 'https://modelscope.cn/api/v1/dolphin/models'
EXT = ('.safetensors', '.ckpt')

# 关键词瞄准"插画/平涂/矢量/绘本"这类风格向底模
QUERIES = ['flat illustration', 'illustration', 'vector', 'storybook', 'picture book',
           'comic style', 'cel shading', 'anime background', 'background art', 'watercolor']

seen = {}
for q in QUERIES:
    try:
        r = requests.put(SEARCH, json={'Name': q, 'PageSize': 12, 'PageNumber': 1,
                                       'SortBy': 'DownloadsCount'}, headers=H, timeout=30)
        if r.status_code != 200:
            print('  [%-16s] HTTP %s' % (q, r.status_code))
            continue
        d = (r.json().get('Data') or {}).get('Model') or {}
        ms = d.get('Models') or []
        print('  [%-16s] 命中 %-3s 总 %-5s' % (q, len(ms), d.get('TotalCount')))
        for m in ms:
            full = '%s/%s' % (m.get('Path') or m.get('Owner') or '?', m.get('Name'))
            if full not in seen:
                seen[full] = m.get('Downloads')
                print('        %-52s 下载 %s' % (full, m.get('Downloads')))
    except Exception as e:
        print('  [%-16s] FAIL %s' % (q, str(e)[:70]))

print()
print('=== 对候选逐个查"是否真是模型文件" ===')
# 只看名字里带 sd / stable / xl 的，避免一堆非生图模型
CANDS = [k for k in seen if any(t in k.lower() for t in ['sd', 'stable', 'xl', 'diffusion',
                                                          'illustration', 'anime', 'flat'])]
print('候选 %d 个，抽查前 18 个：' % len(CANDS))
for full in CANDS[:18]:
    try:
        r = requests.get('https://modelscope.cn/api/v1/models/%s/repo/files' % full,
                         params={'Revision': 'master'}, headers=H, timeout=25)
        if r.status_code != 200:
            continue
        files = (r.json().get('Data') or {}).get('Files') or []
        mods = [f for f in files if str(f.get('Path', '')).lower().endswith(EXT)]
        if mods:
            biggest = max(mods, key=lambda f: f.get('Size') or 0)
            sz = (biggest.get('Size') or 0) / 1073741824
            print('  ✅ %-52s %-40s %5.2f GB' % (full, biggest.get('Path'), sz))
    except Exception:
        pass
