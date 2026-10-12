"""对 img2img 产出的自动判据（修正版）。

**上一版的 bug（已修）**：判据区域用了固定绝对坐标 (982,951,1283,1488)，
那是按参照物 main_bg.png（2730x1535）算的；而 img2img 输出是 1152x648，
于是 crop 出界、PIL 用黑色填充 → "纸面墨色 100%"，把**每一张都误判成"纸上有字"**。
（连参照物自己都是 1.4%，只有其它图 100% —— 这个反常就是 bug 的信号。）

修正：**按每张图的实际尺寸取相对区域**。

判据三项：
 1. 结构差异（分块平均色差）：越大说明构图被改得越多
 2. 纸面墨色占比：与参照物对比，判断纸是否仍空白、有没有被画上字
 3. 整体画风距离（相邻差比值）
"""
import os
import sys

from PIL import Image

SRC = r'D:\个人项目\daishu\assets\images\backgrounds\main_bg.png'
DIR = r'D:\dsh\tmp\restyle'
# 相对区域（信纸 / 纸面）：x 36%~47%，y 62%~97%
RB = (0.36, 0.62, 0.47, 0.97)


def box_for(img, rb=RB):
    w, h = img.size
    return (int(w * rb[0]), int(h * rb[1]), int(w * rb[2]), int(h * rb[3]))


def block_diff(a, b, grid=12):
    if a.size != b.size:
        b = b.resize(a.size, Image.LANCZOS)
    pa = a.resize((grid, grid), Image.BOX).load()
    pb = b.resize((grid, grid), Image.BOX).load()
    tot = 0
    for y in range(grid):
        for x in range(grid):
            ra, ga, ba = pa[x, y]
            rb_, gb, bb = pb[x, y]
            tot += abs(ra - rb_) + abs(ga - gb) + abs(ba - bb)
    return tot / (grid * grid * 3)


def ink_ratio(img, rb=RB):
    crop = img.crop(box_for(img, rb))
    px = crop.load()
    w, h = crop.size
    n = 0
    dark = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
            sat = max(r, g, b) - min(r, g, b)
            n += 1
            if lum < 120 and sat < 60:
                dark += 1
    return dark / max(1, n)


def main():
    ref = Image.open(SRC).convert('RGB')
    base_ink = ink_ratio(ref) * 100
    print('参照物 %s %s  纸面墨色基准 %.1f%%' % (os.path.basename(SRC), ref.size, base_ink))
    print()
    print('%-18s %-10s %-12s %s' % ('文件', '结构差异', '纸面墨色', '判定'))
    print('-' * 60)
    rows = []
    for f in sorted(os.listdir(DIR)):
        if not f.endswith('.png') or f.startswith(('restyle', 'crop_')):
            continue
        img = Image.open(os.path.join(DIR, f)).convert('RGB')
        bd = block_diff(ref, img)
        ink = ink_ratio(img) * 100
        flags = []
        if bd > 26:
            flags.append('结构崩')
        if ink > base_ink * 3 + 6:          # 明显高于参照物 = 纸上多了深色痕迹
            flags.append('纸面多墨')
        rows.append((f, bd, ink, ' / '.join(flags) if flags else 'OK'))
    for f, bd, ink, v in sorted(rows, key=lambda r: r[1]):
        print('%-18s %-10.1f %-11.1f%% %s' % (f, bd, ink, v))
    print()
    print('判读：结构差异小 = 保住构图；纸面墨色接近基准 %.1f%% = 纸仍空白。' % base_ink)


if __name__ == '__main__':
    main()
