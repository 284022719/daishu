"""用 /repo/files 拿到候选仓库的真实文件表（之前猜文件名太笨）。

已确认接口： GET https://modelscope.cn/api/v1/models/{owner}/{name}/repo/files?Revision=master
返回 Data.Files[]，含 Name / Path / Size / Type。
"""
import requests

H = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
CANDS = [
    'NickYuan/4Guofeng4XL_v1125D',
    'dajiahaoaaa/CG_gu_feng',
    'longgehao/CG_gu_feng',
    'mixLine/Guofeng3',
    'zhouwenbin1994/Guofeng',
    'mu101606/MERJIC_GuoFeng',
    'digiplay/Landscape_PhotoReal_v1',
    'Remade-AI/Fantasy-Landscapes',
    'AI-ModelScope/stable-diffusion-xl-base-1.0',
]

EXT = ('.safetensors', '.ckpt', '.pt', '.bin')
for full in CANDS:
    try:
        r = requests.get('https://modelscope.cn/api/v1/models/%s/repo/files' % full,
                         params={'Revision': 'master'}, headers=H, timeout=30)
        if r.status_code != 200:
            print('  -- %-42s HTTP %s' % (full, r.status_code))
            continue
        d = r.json().get('Data') or {}
        files = d.get('Files') or []
        mods = [f for f in files if str(f.get('Path', '')).lower().endswith(EXT)]
        print('=== %s  (总 %d 文件, 模型 %d) ===' % (full, len(files), len(mods)))
        for f in mods:
            sz = f.get('Size') or 0
            print('    %-58s %7.2f GB' % (f.get('Path'), sz / 1073741824))
        if not mods:
            for f in files[:8]:
                print('    (其它) %-50s %s' % (f.get('Path'), f.get('Type')))
    except Exception as e:
        print('  -- %-42s FAIL %s' % (full, str(e)[:70]))
    print()
