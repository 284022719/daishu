"""直接移除幌子上的文字（不用 AI，用幌子自身布色覆盖）。

为什么放弃 inpainting：实测那样做**把图弄坏了** ——
  让模型"生成干净布面"，它就加皱褶；深色幌子上还生成了**英文涂鸦**。
  而原图上的字其实只占该区域很小一部分，**根本不需要重绘整块**。

正确做法（可精确控制、可复现、零画质损失）：
  1. 取幌子区域的**中位色**（避开字迹像素：字是深色，中位色自然落在布面上）
  2. 用该色 + 极轻微的纵向明暗变化填满区域
  3. 用**羽化边缘**融合，避免补丁边界可见
  ⇒ 结果与"布面上本来没写字"几乎一致，且不引入任何新纹理。

判据：区域内"暗像素占比"（字是深色）应显著下降，同时**总高频细节不应上升**
（这是上一版 inpainting 失败的地方：细节反而从 0.4% 涨到 5.9%）。
"""
import os
import statistics
import sys

from PIL import Image, ImageDraw, ImageFilter

OUT = r'D:\dsh\tmp\textfix'
os.makedirs(OUT, exist_ok=True)

TARGETS = [
    ('main', r'D:\个人项目\daishu\assets\images\backgrounds\main.png',
     [(0.222, 0.058, 0.318, 0.290),
      (0.283, 0.330, 0.365, 0.545),
      (0.745, 0.083, 0.845, 0.300),
      (0.790, 0.330, 0.880, 0.560)]),
    ('main_bg', r'D:\个人项目\daishu\assets\images\backgrounds\main_bg.png',
     [(0.560, 0.055, 0.660, 0.230),
      (0.185, 0.150, 0.280, 0.330)]),
]


def dark_ratio(img, boxes, thr=110):
    g = img.convert('L')
    w, h = g.size
    px = g.load()
    n = dark = 0
    for (x0, y0, x1, y1) in boxes:
        for y in range(int(h * y0) + 1, int(h * y1), 2):
            for x in range(int(w * x0), int(w * x1), 2):
                n += 1
                if px[x, y] < thr:
                    dark += 1
    return dark / max(1, n)


def edge_ratio(img, boxes):
    """区域内高频细节占比（整块图，不是只边缘）。"""
    g = img.convert('L')
    w, h = g.size
    px = g.load()
    n = e = 0
    for (x0, y0, x1, y1) in boxes:
        for y in range(int(h * y0) + 1, int(h * y1), 2):
            for x in range(int(w * x0) + 1, int(w * x1), 2):
                n += 1
                if abs(px[x, y] - px[x - 1, y]) > 40 or abs(px[x, y] - px[x, y - 1]) > 40:
                    e += 1
    return e / max(1, n)


def fabric_color(img, box):
    """取区域内**中位色**（字是深色少数派，中位色自然落在布面上）。"""
    w, h = img.size
    x0, y0, x1, y1 = (int(w * box[0]), int(h * box[1]), int(w * box[2]), int(h * box[3]))
    crop = img.crop((x0, y0, x1, y1))
    px = list(crop.getdata())
    r = statistics.median(p[0] for p in px)
    g = statistics.median(p[1] for p in px)
    b = statistics.median(p[2] for p in px)
    return (int(r), int(g), int(b))


def fix(tag, path, boxes, feather=10):
    img = Image.open(path).convert('RGB')
    W, H = img.size
    before_dark = dark_ratio(img, boxes)
    before_edge = edge_ratio(img, boxes)

    # 在**单独的层**上画好再羽化贴回，避免逐块羽化导致边界重叠
    patch = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(patch)
    colors = []
    for (x0, y0, x1, y1) in boxes:
        col = fabric_color(img, (x0, y0, x1, y1))
        colors.append(col)
        # 轻微纵向明暗（布面受光），幅度很小以免引入新细节
        px0, py0, px1, py1 = int(W * x0), int(H * y0), int(W * x1), int(H * y1)
        for y in range(py0, py1):
            t = (y - py0) / max(1, (py1 - py0))
            k = 1.0 - 0.06 * t
            d.line([(px0, y), (px1, y)], fill=(int(col[0] * k), int(col[1] * k), int(col[2] * k)))

    # 只把"补丁区"作为融合掩膜：先画实心矩形，再羽化
    m = Image.new('L', (W, H), 0)
    md = ImageDraw.Draw(m)
    for (x0, y0, x1, y1) in boxes:
        md.rectangle([int(W * x0), int(H * y0), int(W * x1), int(H * y1)], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(feather))

    out = Image.composite(patch, img, m)
    after_dark = dark_ratio(out, boxes)
    after_edge = edge_ratio(out, boxes)
    p = os.path.join(OUT, '%s_textfix.png' % tag)
    out.save(p)
    print('  [%s] 尺寸 %s' % (tag, (W, H)))
    print('       取色: %s' % ['#%02x%02x%02x' % c for c in colors])
    print('       暗像素占比 %.4f → %.4f   （字少了就该降）' % (before_dark, after_dark))
    print('       高频细节   %.4f → %.4f   （**不应上升**，上升就是像 inpainting 那样加纹理了）'
          % (before_edge, after_edge))
    print('       -> %s' % p)
    return p


def main():
    for tag, path, boxes in TARGETS:
        fix(tag, path, boxes)
    print()
    print('判读：暗像素下降 = 字被盖掉；高频细节不升 = 没有引入新纹理（这是上一版 inpainting 的失败点）。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
