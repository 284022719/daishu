#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────────────
// 代书 (Daishu) 美术素材检查器 —— 零依赖
//
// 对应 docs/ART_PLAN.md 的三条硬性流程：
//   §二  "所有新素材生成后必须做色板量化对比，偏离锚点 >30% 的重做"
//   §四  "任何带网格/结构的底图，接入前必须：① 像素级检测结构位置（禁止用目测/
//         视觉模型估测）② 代码锚点按检测分数设置 ③ 截图后再次像素验证"
//   §一  "任何素材不得含文字/水印/品牌标识"
//
// 只依赖 node 内置的 zlib —— 自带 PNG 解码与编码，**不需要 npm install**。
//
// 用法：
//   node tools/art_check.mjs info      <img>
//   node tools/art_check.mjs palette   <img> [--top N] [--json]
//   node tools/art_check.mjs grid      <img> [--expect 12] [--expect-lines N]
//                                            [--axis v|h] [--thresh X]
//                                            [--group px] [--raw] [--json]
//   node tools/art_check.mjs watermark <img> [--scan|--crop] [--inset N]
//                                            [--edges bottom,right] [--out f]
//   node tools/art_check.mjs crop      <img> --box x0,y0,x1,y1 --out f   （取局部，供肉眼/vision 复核）
//
// 退出码：0 = 通过 / 1 = 未通过（grid 条数不符、palette 偏离锚点）/ 2 = 用法或解码错误
// ─────────────────────────────────────────────────────────────────────────────

import { readFileSync, writeFileSync } from 'node:fs';
import { inflateSync, deflateSync } from 'node:zlib';
import { basename } from 'node:path';

// ═════════════════════════════════════════════════════════════════════════════
// PNG 解码（colorType 0/2/3/4/6，depth 1/2/4/8/16，仅非交错）
// ═════════════════════════════════════════════════════════════════════════════

const CHANNELS = { 0: 1, 2: 3, 3: 1, 4: 2, 6: 4 };

function decodePNG(buf) {
  if (buf.length < 8 || buf.readUInt32BE(0) !== 0x89504e47) {
    throw new Error('不是 PNG 文件（magic 不符）');
  }
  let off = 8;
  let ihdr = null, plte = null, trns = null;
  const idat = [];
  while (off + 8 <= buf.length) {
    const len = buf.readUInt32BE(off);
    const type = buf.toString('ascii', off + 4, off + 8);
    const data = buf.subarray(off + 8, off + 8 + len);
    if (type === 'IHDR') {
      ihdr = {
        width: data.readUInt32BE(0), height: data.readUInt32BE(4),
        depth: data[8], colorType: data[9],
        compression: data[10], filter: data[11], interlace: data[12],
      };
    } else if (type === 'PLTE') plte = Buffer.from(data);
    else if (type === 'tRNS') trns = Buffer.from(data);
    else if (type === 'IDAT') idat.push(Buffer.from(data));
    else if (type === 'IEND') break;
    off += 12 + len;
  }
  if (!ihdr) throw new Error('PNG 缺少 IHDR');
  if (ihdr.interlace !== 0) throw new Error('不支持交错(interlaced) PNG，请先转存为非交错');
  if (!CHANNELS[ihdr.colorType]) throw new Error(`不支持的 colorType=${ihdr.colorType}`);
  if (![1, 2, 4, 8, 16].includes(ihdr.depth)) throw new Error(`不支持的 bitDepth=${ihdr.depth}`);

  const { width: W, height: H, depth, colorType } = ihdr;
  const ch = CHANNELS[colorType];
  const bpp = Math.max(1, (ch * depth) >> 3);          // 滤波用的字节步长
  const stride = Math.ceil((W * ch * depth) / 8);      // 每行未滤波字节数
  const raw = inflateSync(Buffer.concat(idat));
  if (raw.length < (stride + 1) * H) {
    throw new Error(`IDAT 数据不完整（期望 ${(stride + 1) * H} 字节，实得 ${raw.length}）`);
  }

  // ── 反滤波（PNG spec §9）
  const img = Buffer.alloc(stride * H);
  for (let y = 0; y < H; y++) {
    const ft = raw[y * (stride + 1)];
    const src = raw.subarray(y * (stride + 1) + 1, y * (stride + 1) + 1 + stride);
    const dst = img.subarray(y * stride, (y + 1) * stride);
    const prev = y > 0 ? img.subarray((y - 1) * stride, y * stride) : null;
    for (let i = 0; i < stride; i++) {
      const a = i >= bpp ? dst[i - bpp] : 0;
      const b = prev ? prev[i] : 0;
      const c = prev && i >= bpp ? prev[i - bpp] : 0;
      let v = src[i];
      if (ft === 1) v += a;
      else if (ft === 2) v += b;
      else if (ft === 3) v += (a + b) >> 1;
      else if (ft === 4) {
        const p = a + b - c;
        const pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
        v += (pa <= pb && pa <= pc) ? a : (pb <= pc ? b : c);
      } else if (ft !== 0) throw new Error(`未知滤波类型 ${ft} @ row ${y}`);
      dst[i] = v & 0xff;
    }
  }

  // ── 展开成 RGBA8
  const rgba = Buffer.alloc(W * H * 4);
  const maxV = (1 << depth) - 1;
  const sample = (rowBase, idx) => {          // 取第 idx 个样本
    if (depth === 8) return img[rowBase + idx];
    if (depth === 16) return img[rowBase + idx * 2];      // 取高字节
    const per = 8 / depth;
    const byte = img[rowBase + ((idx / per) | 0)];
    const shift = 8 - depth - (idx % per) * depth;
    return (byte >> shift) & maxV;
  };

  for (let y = 0; y < H; y++) {
    const rb = y * stride;
    for (let x = 0; x < W; x++) {
      const o = (y * W + x) * 4;
      let r, g, b, a = 255;
      switch (colorType) {
        case 0: { const v = sample(rb, x); const s = depth === 8 || depth === 16 ? v : Math.round(v * 255 / maxV); r = g = b = s; break; }
        case 4: { const v = sample(rb, x * 2); const s = depth === 8 || depth === 16 ? v : Math.round(v * 255 / maxV); r = g = b = s; a = sample(rb, x * 2 + 1); break; }
        case 2: r = sample(rb, x * 3); g = sample(rb, x * 3 + 1); b = sample(rb, x * 3 + 2); break;
        case 6: r = sample(rb, x * 4); g = sample(rb, x * 4 + 1); b = sample(rb, x * 4 + 2); a = sample(rb, x * 4 + 3); break;
        case 3: {
          const i = sample(rb, x);
          if (!plte || (i * 3 + 2) >= plte.length) throw new Error(`调色板索引越界 ${i}`);
          r = plte[i * 3]; g = plte[i * 3 + 1]; b = plte[i * 3 + 2];
          if (trns && i < trns.length) a = trns[i];
          break;
        }
      }
      rgba[o] = r; rgba[o + 1] = g; rgba[o + 2] = b; rgba[o + 3] = a;
    }
  }
  return { width: W, height: H, data: rgba, colorType, depth };
}

// ═════════════════════════════════════════════════════════════════════════════
// PNG 编码（RGBA8 → 每行 filter 0）
// ═════════════════════════════════════════════════════════════════════════════

const CRC_TABLE = (() => {
  const t = new Int32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
    t[n] = c;
  }
  return t;
})();

function crc32(buf) {
  let c = -1;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ -1) >>> 0;
}

function chunk(type, data) {
  const out = Buffer.alloc(12 + data.length);
  out.writeUInt32BE(data.length, 0);
  out.write(type, 4, 'ascii');
  data.copy(out, 8);
  out.writeUInt32BE(crc32(out.subarray(4, 8 + data.length)), 8 + data.length);
  return out;
}

function encodePNG(rgba, W, H) {
  const stride = W * 4;
  const raw = Buffer.alloc((stride + 1) * H);
  for (let y = 0; y < H; y++) {
    raw[y * (stride + 1)] = 0;
    rgba.copy(raw, y * (stride + 1) + 1, y * stride, (y + 1) * stride);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(W, 0); ihdr.writeUInt32BE(H, 4);
  ihdr[8] = 8; ihdr[9] = 6; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw, { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

// ═════════════════════════════════════════════════════════════════════════════
// 通用工具
// ═════════════════════════════════════════════════════════════════════════════

const hex = (r, g, b) => '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('');
const luma = (r, g, b) => 0.2126 * r + 0.7152 * g + 0.0722 * b;
// 相位计时（--debug 时打印），慢命令靠它定位热点
const T0 = process.hrtime.bigint();
const mark = (label) => { if (DEBUG) console.log(`    [t] ${label}: ${Number(process.hrtime.bigint() - T0) / 1e6}ms`); };
let DEBUG = false;
const median = (arr) => { const s = [...arr].sort((a, b) => a - b); return s.length % 2 ? s[(s.length - 1) / 2] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2; };
const mean = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;
const std = (arr) => { const m = mean(arr); return Math.sqrt(mean(arr.map(v => (v - m) ** 2))); };
const pct = (v, n = 1) => (v * 100).toFixed(n) + '%';

// ART_PLAN §二 风格锚点色板
const ANCHORS = {
  '宣纸/信纸': ['#fce4b4', '#fce49c', '#fccc84'],
  '木构/家具': ['#9c5424', '#b46c3c', '#845424'],
  '墨/字': ['#3c3c2c', '#a43c2c'],
  '户外/远景': ['#846c54', '#6c846c', '#54543c'],
};

function parseHex(h) {
  const s = h.replace('#', '');
  return [parseInt(s.slice(0, 2), 16), parseInt(s.slice(2, 4), 16), parseInt(s.slice(4, 6), 16)];
}

// 色距归一化到 0..1（RGB 欧氏距离 / √(3·255²)）
function colorDist(a, b) {
  return Math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) / 441.673;
}

const ALL_ANCHORS = Object.values(ANCHORS).flat().map(parseHex);

function usage() {
  const t = readFileSync(new URL(import.meta.url), 'utf8');
  console.log(t.split('\n').filter(l => l.startsWith('//')).map(l => l.replace(/^\/\/ ?/, '')).join('\n'));
}

function args(argv) {                       // 极简 flag 解析
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const k = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith('--')) out[k] = true;
      else { out[k] = next; i++; }
    } else out._.push(a);
  }
  return out;
}

function loadImage(p) {
  const img = decodePNG(readFileSync(p));
  img.name = basename(p);
  return img;
}

// ═════════════════════════════════════════════════════════════════════════════
// info
// ═════════════════════════════════════════════════════════════════════════════

function cmdInfo(img) {
  const { width: W, height: H, data } = img;
  let transparent = 0, sum = 0;
  const colors = new Set();
  for (let i = 0; i < W * H; i++) {
    const o = i * 4;
    if (data[o + 3] < 255) transparent++;
    sum += luma(data[o], data[o + 1], data[o + 2]);
    if (colors.size < 5000) colors.add((data[o] << 16) | (data[o + 1] << 8) | data[o + 2]);
  }
  const n = W * H;
  console.log(`文件      ${img.name}`);
  console.log(`尺寸      ${W} × ${H}  (${(W / H).toFixed(3)} 宽高比)`);
  console.log(`色彩类型  colorType=${img.colorType} depth=${img.depth}`);
  console.log(`平均亮度  ${(sum / n).toFixed(1)} / 255`);
  console.log(`透明像素  ${transparent} (${pct(transparent / n)})`);
  console.log(`颜色种数  ${colors.size >= 5000 ? '≥5000（采样截断）' : colors.size}`);
  return 0;
}

// ═════════════════════════════════════════════════════════════════════════════
// palette —— 色板量化 + 锚点比对（ART_PLAN §二）
// ═════════════════════════════════════════════════════════════════════════════

function cmdPalette(img, opt) {
  const topN = Number(opt.top ?? 8);
  const { width: W, height: H, data } = img;
  const buckets = new Map();
  let counted = 0;
  for (let i = 0; i < W * H; i++) {
    const o = i * 4;
    if (data[o + 3] < 8) continue;                       // 忽略全透明
    const key = ((data[o] >> 3) << 10) | ((data[o + 1] >> 3) << 5) | (data[o + 2] >> 3);
    let e = buckets.get(key);
    if (!e) { e = { n: 0, r: 0, g: 0, b: 0 }; buckets.set(key, e); }
    e.n++; e.r += data[o]; e.g += data[o + 1]; e.b += data[o + 2];
    counted++;
  }
  const list = [...buckets.values()]
    .map(e => ({ n: e.n, rgb: [Math.round(e.r / e.n), Math.round(e.g / e.n), Math.round(e.b / e.n)] }))
    .sort((a, b) => b.n - a.n)
    .slice(0, topN)
    .map(e => ({ ...e, share: e.n / counted }));

  const rows = list.map((e, i) => {
    let best = Infinity, bestAnchor = null, bestGroup = null;
    for (const [group, hexes] of Object.entries(ANCHORS)) {
      for (const h of hexes) {
        const d = colorDist(e.rgb, parseHex(h));
        if (d < best) { best = d; bestAnchor = h; bestGroup = group; }
      }
    }
    return { i: i + 1, hex: hex(...e.rgb), share: e.share, dist: best, anchor: bestAnchor, group: bestGroup };
  });

  const offenders = rows.filter(r => r.dist > 0.30);

  if (opt.json) {
    console.log(JSON.stringify({
      file: img.name, size: [W, H], countedPixels: counted,
      dominant: rows.map(r => ({ hex: r.hex, share: +r.share.toFixed(4), nearestAnchor: r.anchor, group: r.group, dist: +r.dist.toFixed(4) })),
      offenders: offenders.map(r => r.hex), pass: offenders.length === 0,
    }, null, 2));
    return offenders.length ? 1 : 0;
  }

  console.log(`=== 色板量化 ${img.name} (${W}×${H}, 有效像素 ${counted}) ===`);
  console.log(`风格锚点 = ART_PLAN §二；色距 = RGB 欧氏距离 / √(3·255²)，>0.30 判为偏离\n`);
  console.log('  #  主色       占比     最近锚点   分组        色距');
  for (const r of rows) {
    const flag = r.dist > 0.30 ? '  ⚠️ 偏离' : '';
    console.log(`${String(r.i).padStart(3)}  ${r.hex}  ${pct(r.share).padStart(6)}   ${r.anchor}  ${r.group.padEnd(10)}  ${r.dist.toFixed(3)}${flag}`);
  }
  const cum = rows.reduce((a, r) => a + r.share, 0);
  console.log(`\n前 ${rows.length} 色覆盖 ${pct(cum)}`);
  if (offenders.length) {
    console.log(`\n⚠️ ${offenders.length} 个主色偏离锚点 >30%：${offenders.map(r => r.hex).join(', ')}`);
    console.log('   按 ART_PLAN §二，这些色应重做或做色板校正。');
    return 1;
  }
  console.log('\n✅ 全部主色落在锚点 30% 容差内。');
  return 0;
}

// ═════════════════════════════════════════════════════════════════════════════
// grid —— 竖线/横线像素检测（ART_PLAN §四，禁止目测）
// ═════════════════════════════════════════════════════════════════════════════

function lineProfile(img, axis) {
  const { width: W, height: H, data } = img;
  const vertical = axis === 'v';
  const n = vertical ? W : H;                 // 扫描方向上的位置数
  const m = vertical ? H : W;                 // 每条线的采样点数
  const pad = Math.floor(m * 0.05);           // 两端各留 5%，避开边框/卷边

  const prof = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    let s = 0;
    for (let j = pad; j < m - pad; j++) {
      const o = vertical ? (j * W + i) * 4 : (i * W + j) * 4;
      s += luma(data[o], data[o + 1], data[o + 2]);
    }
    prof[i] = s / (m - 2 * pad);
  }
  return { prof, n, sampleFrom: pad, sampleTo: m - pad, name: vertical ? '竖线' : '横线' };
}

// 线 = 局部显著偏离基线的细条；极性自动判定（纸深线 / 深底亮线）
function detectLines(prof, n, opt) {
  const win = Math.max(3, Math.round(n / 60));
  const dev = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const lo = Math.max(0, i - win), hi = Math.min(n, i + win + 1);
    dev[i] = prof[i] - median(Array.from(prof.subarray(lo, hi)));
  }
  const mad = median(Array.from(dev, Math.abs)) || 1e-6;
  const auto = Math.min(30, Math.max(2, 4 * mad));

  const run = (sign, thresh) => {
    const hits = [];
    for (let i = 0; i < n; i++) if (sign * dev[i] > thresh && sign * dev[i] === Math.max(...[i - 1, i, i + 1].filter(k => k >= 0 && k < n).map(k => sign * dev[k]))) hits.push(i);
    // 合并相邻命中（同一条线的多列）
    const clusters = [];
    for (const i of hits) {
      const last = clusters[clusters.length - 1];
      if (last && i - last.x2 <= 2) { last.x2 = i; last.members.push(i); }
      else clusters.push({ x1: i, x2: i, members: [i] });
    }
    return clusters.map(c => {
      const wsum = c.members.reduce((a, x) => a + Math.max(0, sign * dev[x]), 0) || 1;
      const center = c.members.reduce((a, x) => a + x * Math.max(0, sign * dev[x]), 0) / wsum;
      const contrast = mean(c.members.map(x => Math.abs(dev[x])));
      return { x: +center.toFixed(2), width: c.x2 - c.x1 + 1, contrast };
    });
  };

  const explicit = opt.thresh !== undefined ? Number(opt.thresh) : null;
  const dark = run(-1, explicit ?? auto);     // 深色线（纸面栏线）
  const light = run(1, explicit ?? auto);     // 亮色线（深底分隔）

  // 极性选择：给了 --expect 就选更接近期望的；否则选对比更强的一组
  let chosen = dark, polarity = '暗线（底浅线深）';
  const expect = opt.expect !== undefined ? Number(opt.expect) : null;
  if (expect !== null) {
    if (Math.abs(light.length - expect) < Math.abs(dark.length - expect)) { chosen = light; polarity = '亮线（底深线浅）'; }
  } else if (light.length && (!dark.length || mean(light.map(l => l.contrast)) > mean(dark.map(l => l.contrast)))) {
    chosen = light; polarity = '亮线（底深线浅）';
  }
  return { lines: chosen, polarity, threshold: explicit ?? auto, mad, auto };
}

// 一"道"栏界常由多条细线构成（如双线制信纸：两道相隔 16px 的细线 = 一道栏界）。
// 用栏距(pitch)做尺度：间距 < 0.5×pitch 的线归为同一道栏界。
function groupSeparators(lines, opt) {
  if (lines.length < 2) {
    return { separators: lines.map(l => ({ center: l.x, members: [l.x], count: 1, span: l.width, contrast: l.contrast })), pitch: 0, groupThresh: 0 };
  }
  const gaps = lines.slice(1).map((l, i) => l.x - lines[i].x);
  const med = median(gaps);
  const big = gaps.filter(g => g >= med);
  const pitch = big.length >= 2 ? mean(big) : med;
  const groupThresh = opt.group !== undefined ? Number(opt.group) : Math.max(3, pitch * 0.5);

  const groups = [];
  let cur = [lines[0]];
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].x - lines[i - 1].x < groupThresh) cur.push(lines[i]);
    else { groups.push(cur); cur = [lines[i]]; }
  }
  groups.push(cur);

  const separators = groups.map(g => {
    const wsum = g.reduce((a, m) => a + m.contrast, 0) || 1;
    const xs = g.map(m => m.x);
    return {
      center: g.reduce((a, m) => a + m.x * m.contrast, 0) / wsum,
      members: xs,
      count: xs.length,
      span: Math.max(...xs) - Math.min(...xs),
      contrast: mean(g.map(m => m.contrast)),
    };
  });
  return { separators, pitch, groupThresh };
}

function cmdGrid(img, opt) {
  const axis = (opt.axis ?? 'v').toLowerCase() === 'h' ? 'h' : 'v';
  const { prof, n, sampleFrom, sampleTo, name } = lineProfile(img, axis);
  const { lines, polarity, threshold } = detectLines(prof, n, opt);
  const { separators, pitch, groupThresh } = groupSeparators(lines, opt);
  const span = axis === 'v' ? img.width : img.height;
  const columns = Math.max(0, separators.length - 1);
  const centers = separators.slice(1).map((s, i) => (s.center + separators[i].center) / 2);
  const sGaps = separators.slice(1).map((s, i) => s.center - separators[i].center);
  const gMean = sGaps.length ? mean(sGaps) : 0;
  const gStd = sGaps.length > 1 ? std(sGaps) : 0;

  const expectCols = opt.expect !== undefined ? Number(opt.expect) : null;
  const expectLines = opt['expect-lines'] !== undefined ? Number(opt['expect-lines']) : null;
  const pass = (expectCols === null || columns === expectCols) && (expectLines === null || separators.length === expectLines);
  const hasExpect = expectCols !== null || expectLines !== null;

  const anchors = separators.map(s => +(s.center / span).toFixed(5));
  const columnRatios = centers.map(c => +(c / span).toFixed(5));

  if (opt.json) {
    console.log(JSON.stringify({
      file: img.name, axis, polarity, threshold: +threshold.toFixed(2), scanSpan: span,
      sampledBand: [sampleFrom, sampleTo],
      rawLines: lines.length, separators: separators.length, columns,
      expected: { columns: expectCols, separators: expectLines }, pass: hasExpect ? pass : null,
      pitch: +pitch.toFixed(2), groupThreshold: +groupThresh.toFixed(2),
      spacing: { mean: +gMean.toFixed(2), std: +gStd.toFixed(2) },
      anchors, columnCenters: columnRatios,
      separatorList: separators.map((s, i) => ({
        i: i + 1, center: +s.center.toFixed(2), ratio: anchors[i],
        members: s.members, width: s.count, contrast: +s.contrast.toFixed(2),
        gap: i ? +(s.center - separators[i - 1].center).toFixed(2) : null,
      })),
    }, null, 2));
    return hasExpect && !pass ? 1 : 0;
  }

  console.log(`=== ${name}检测 ${img.name} (${img.width}×${img.height}) ===`);
  console.log(`极性 ${polarity}   阈值 ${threshold.toFixed(2)}   采样带 ${sampleFrom}..${sampleTo}`);
  console.log(`原始命中 ${lines.length} 条细线 → 归并为 ${separators.length} 道栏界（栏距 ${pitch.toFixed(1)}px，归并阈 ${groupThresh.toFixed(1)}px）\n`);

  if (opt.raw) {
    console.log('  原始细线：');
    lines.forEach((l, i) => console.log(`    ${String(i + 1).padStart(3)}  x=${String(l.x).padStart(8)}  宽${l.width}  ΔL ${l.contrast.toFixed(2)}`));
    console.log('');
  }

  if (!separators.length) { console.log('未检测到线条。图可能无线条，或需要 --thresh 调低阈值。'); return hasExpect && !pass ? 1 : 0; }

  console.log('  #  栏界中心(px)  比例      含细线  成员位置               ΔL     与前一道间隔');
  separators.forEach((s, i) => {
    const mem = s.members.length > 4 ? `${s.members.slice(0, 3).join(',')}…(${s.members.length})` : s.members.join(',');
    console.log(`${String(i + 1).padStart(3)}  ${s.center.toFixed(1).padStart(11)}  ${anchors[i].toFixed(5).padStart(8)}  ${String(s.count).padStart(5)}   ${mem.padEnd(20)}  ${s.contrast.toFixed(2).padStart(5)}   ${i ? (s.center - separators[i - 1].center).toFixed(1).padStart(9) : '        —'}`);
  });

  console.log(`\n栏界 ${separators.length} 道 → **栏数 ${columns}** | 平均栏距 ${gMean.toFixed(2)}px | σ=${gStd.toFixed(2)}${gMean ? ` (CV ${(gStd / gMean * 100).toFixed(1)}%)` : ''}`);
  console.log(`\nanchors(比例)       = [${anchors.join(', ')}]`);
  console.log(`columnCenters(比例) = [${columnRatios.join(', ')}]   ← 栏中心，槽位对齐用这个`);

  if (hasExpect) {
    const okCols = expectCols === null || columns === expectCols;
    const okLines = expectLines === null || separators.length === expectLines;
    if (okCols && okLines) {
      console.log(`\n✅ 结构符合期望（${expectCols !== null ? `栏数 ${expectCols}` : ''}${expectCols !== null && expectLines !== null ? '，' : ''}${expectLines !== null ? `栏界 ${expectLines}` : ''}）—— anchors 可直接写入场景锚点。`);
    } else {
      if (!okCols) console.log(`\n⚠️ 栏数 ${columns} ≠ 期望 ${expectCols}。`);
      if (!okLines) console.log(`\n⚠️ 栏界 ${separators.length} ≠ 期望 ${expectLines}。`);
      console.log('   按 ART_PLAN §四：要么重生成底图，要么接受实际结构并把实测值记进锚点表。');
    }
  }
  console.log('\n下一步（ART_PLAN §四 ③）：写入锚点 → 截图 → 再跑一次本命令做像素验证。');
  return hasExpect && !pass ? 1 : 0;
}

// ═════════════════════════════════════════════════════════════════════════════
// watermark —— 水印区排查 / 裁除（ART_PLAN §一 硬规则）
// ═════════════════════════════════════════════════════════════════════════════

// 文字笔画在局部表现为"细密高频 + 与背景有反差"。用两个稳健指标组合：
//   inkScore  = 低于 (区域均值 - 1.0σ) 的像素占比   （暗笔画覆盖率）
//   edgeScore = 相邻像素亮度差的均值                 （高频密度）
function regionMetrics(img, x0, y0, x1, y1) {
  const { width: W, data } = img;
  const vals = [];
  for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) {
    const o = (y * W + x) * 4;
    vals.push(luma(data[o], data[o + 1], data[o + 2]));
  }
  const m = mean(vals), s = std(vals) || 1e-6;
  const ink = vals.filter(v => v < m - 1.0 * s).length / vals.length;
  let edge = 0, cnt = 0;
  for (let y = y0; y < y1; y++) for (let x = x0; x < x1 - 1; x++) {
    const a = (y * W + x) * 4, b = (y * W + x + 1) * 4;
    const l1 = luma(data[a], data[a + 1], data[a + 2]), l2 = luma(data[b], data[b + 1], data[b + 2]);
    edge += Math.abs(l1 - l2); cnt++;
  }
  return { mean: m, std: s, ink, edge: cnt ? edge / cnt : 0 };
}

// 检测器 B：亮笔画文字。水印（如"豆包AI生成"）是**白色细笔画**盖在任意背景上：
//   ① 局部 top-hat —— 比周围 30px 邻域明显更亮的像素（大块亮物如灯笼/窗户不会通过，
//      因为它们的中心与自身邻域同亮）
//   ② 连通域字形 —— 细笔画连通域（填充率低、高度小）排成一行 = 文字行
// 这比"高频密度"稳健得多：后者会被背景本身的复杂纹理淹没（实测漏检过）。
function integralLuma(img) {
  const { width: W, height: H, data } = img;
  const I = new Float64Array((W + 1) * (H + 1));
  for (let y = 0; y < H; y++) {
    let rowSum = 0;
    for (let x = 0; x < W; x++) {
      const o = (y * W + x) * 4;
      rowSum += luma(data[o], data[o + 1], data[o + 2]);
      I[(y + 1) * (W + 1) + (x + 1)] = I[y * (W + 1) + (x + 1)] + rowSum;
    }
  }
  return I;
}

const boxMean = (I, W, H, x0, y0, x1, y1) => {
  const a = Math.max(0, x0), b = Math.max(0, y0);
  const c = Math.min(W, x1), d = Math.min(H, y1);
  const n = (c - a) * (d - b);
  if (n <= 0) return 0;
  return (I[d * (W + 1) + c] - I[b * (W + 1) + c] - I[d * (W + 1) + a] + I[b * (W + 1) + a]) / n;
};

function brightStrokeMask(img) {
  const { width: W, height: H, data } = img;
  const r = Math.max(6, Math.round(Math.min(W, H) * 0.02));
  const I = integralLuma(img);
  const diff = new Float64Array(W * H);
  let sum = 0, sum2 = 0;
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const o = (y * W + x) * 4;
      const L = luma(data[o], data[o + 1], data[o + 2]);
      const bg = boxMean(I, W, H, x - r, y - r, x + r + 1, y + r + 1);
      const d = L - bg;
      diff[y * W + x] = d;
      sum += d; sum2 += d * d;
    }
  }
  const m = sum / (W * H);
  const sd = Math.sqrt(Math.max(0, sum2 / (W * H) - m * m));
  const thr = Math.min(60, Math.max(14, m + 3 * sd));
  return { diff, thr, radius: r };
}

// 近白低饱和分割：白色水印的像素三通道都高且差异小；而暖色美术底（米/橙/木）蓝通道很低、
// 饱和度高 —— 因此这个判据几乎不受"水印压在高对比纹理上"影响（实测 top-hat 分割会切碎字形）。
function whiteMask(img) {
  const { width: W, height: H, data } = img;
  const mask = new Uint8Array(W * H);
  for (let i = 0; i < W * H; i++) {
    const o = i * 4;
    const r = data[o], g = data[o + 1], b = data[o + 2];
    const mx = Math.max(r, g, b), mn = Math.min(r, g, b);
    if (mn >= 185 && mx - mn <= 45) mask[i] = 1;
  }
  return mask;
}

// 连通域（4 邻域），带 bbox / 填充率 / 平均色（颜色在填充过程中累加，不保存像素表，避免爆内存）
function findComponents(mask, diff, rgba, W, H) {
  const seen = new Uint8Array(W * H);
  const comps = [];
  const stack = new Int32Array(W * H);            // 复用栈，避免反复分配
  for (let y0 = 0; y0 < H; y0++) {
    for (let x0 = 0; x0 < W; x0++) {
      const i0 = y0 * W + x0;
      if (seen[i0] || !mask[i0]) continue;
      let sp = 0;
      stack[sp++] = i0; seen[i0] = 1;
      let n = 0, minX = x0, maxX = x0, minY = y0, maxY = y0, dsum = 0, rsum = 0, gsum = 0, bsum = 0;
      while (sp > 0) {
        const i = stack[--sp]; n++;
        const ix = i % W, iy = (i - ix) / W;
        dsum += diff[i];
        const o = i * 4;
        rsum += rgba[o]; gsum += rgba[o + 1]; bsum += rgba[o + 2];
        if (ix < minX) minX = ix; else if (ix > maxX) maxX = ix;
        if (iy < minY) minY = iy; else if (iy > maxY) maxY = iy;
        if (ix > 0) { const j = i - 1; if (!seen[j] && mask[j]) { seen[j] = 1; stack[sp++] = j; } }
        if (ix < W - 1) { const j = i + 1; if (!seen[j] && mask[j]) { seen[j] = 1; stack[sp++] = j; } }
        if (iy > 0) { const j = i - W; if (!seen[j] && mask[j]) { seen[j] = 1; stack[sp++] = j; } }
        if (iy < H - 1) { const j = i + W; if (!seen[j] && mask[j]) { seen[j] = 1; stack[sp++] = j; } }
      }
      comps.push({ n, x: minX, y: minY, w: maxX - minX + 1, h: maxY - minY + 1, meanDiff: dsum / n, color: [rsum / n, gsum / n, bsum / n] });
    }
  }
  return comps;
}

// 路径②：字形行（glyph-run）—— 水印是**同基线、彼此相邻、尺寸相近的一串近白字形**。
// 单看"宽扁亮带"会误报（图中央的亮边/云highlight也宽而扁），故必须要求"多个相似字形排成一行"。
function asGlyphRun(comps, W, H) {
  const cand = comps.filter(c => {
    if (c.n < 20) return false;
    if (c.h < 4 || c.h > Math.max(10, H * 0.08)) return false;
    if (c.w < 4 || c.w > W * 0.25) return false;
    const fill = c.n / (c.w * c.h);
    if (fill < 0.05 || fill > 0.9) return false;
    if (Math.min(...c.color) < 180) return false;        // 双保险：仍要求偏白
    return true;
  }).sort((a, b) => a.x - b.x);

  const runs = [];
  for (const g of cand) {
    const last = runs[runs.length - 1];
    if (last) {
      const prev = last[last.length - 1];
      const gap = g.x - (prev.x + prev.w);
      const hRef = Math.max(prev.h, g.h);
      const dy = Math.abs((g.y + g.h / 2) - (prev.y + prev.h / 2));
      if (gap < 0.6 * hRef && dy < 0.5 * hRef) { last.push(g); continue; }
    }
    runs.push([g]);
  }

  return runs.filter(r => r.length >= 2).map(gs => {
    const x0 = Math.min(...gs.map(g => g.x)), x1 = Math.max(...gs.map(g => g.x + g.w));
    const y0 = Math.min(...gs.map(g => g.y)), y1 = Math.max(...gs.map(g => g.y + g.h));
    const hs = gs.map(g => g.h);
    const hMed = median(hs);
    return {
      glyphs: gs.length, box: [x0, y0, x1, y1], strokeHeight: hMed, span: x1 - x0, band: y1 - y0,
      heightSpread: hMed ? std(hs) / hMed : 1, weight: gs.reduce((a, g) => a + g.n, 0), mode: 'glyph-run',
      meanDiff: gs.reduce((a, g) => a + g.meanDiff * g.n, 0) / (gs.reduce((a, g) => a + g.n, 0) || 1),
      members: gs.map(g => `${g.x},${g.y} ${g.w}×${g.h}`),
    };
  }).sort((a, b) => b.weight - a.weight);
}

function cmdWatermark(img, opt) {
  const { width: W, height: H, data } = img;
  const bw = Math.max(8, Math.round(W * 0.22));
  const bh = Math.max(8, Math.round(H * 0.14));
  const bands = [
    ['右下角', W - bw, H - bh, W, H],
    ['左下角', 0, H - bh, bw, H],
    ['底部中段', Math.round(W / 2 - bw / 2), H - bh, Math.round(W / 2 + bw / 2), H],
    ['中央(对照)', Math.round(W / 2 - bw / 2), Math.round(H / 2 - bh / 2), Math.round(W / 2 + bw / 2), Math.round(H / 2 + bh / 2)],
  ];
  const metrics = bands.map(([label, x0, y0, x1, y1]) => ({ label, box: [x0, y0, x1, y1], ...regionMetrics(img, x0, y0, x1, y1) }));
  const base = metrics[metrics.length - 1];                  // 中央作对照基线
  mark('A 区域统计');

  // 检测器 B：白色文字 → 近白分割 → 连通域 → 字形行
  const { diff, thr, radius } = brightStrokeMask(img);
  mark('B1 top-hat 局部对比');
  const mask = whiteMask(img);
  mark('B2 近白分割');
  const allComp = findComponents(mask, diff, img.data, W, H);
  mark(`B3 连通域 (${allComp.length} 个)`);
  const runs = asGlyphRun(allComp, W, H).filter(r => r.span >= 1.2 * r.strokeHeight && r.heightSpread < 0.35);
  mark(`B4 字形行 (${runs.length} 条)`);
  // 判定门槛：至少 3 个字形 + 体积/笔画高与图像尺寸相称 + **与局部背景有实质反差**。
  // 最后一条是实测加上的：浅色纸纤维也能凑出"3 个近白小块排成一行"（对比 Δ≈1），
  // 而真水印对比 Δ≥42 —— 用 0.8×阈值 分开，两侧余量都在 2.5 倍以上。
  const minWeight = Math.max(60, W * H * 4e-5);
  const minStroke = Math.max(6, H * 0.004);
  const minDiff = Math.max(15, 0.8 * thr);
  const textLine = runs.find(r => r.glyphs >= 3 && r.weight >= minWeight && r.strokeHeight >= minStroke && r.meanDiff >= minDiff) ?? null;
  const textHit = !!textLine;

  console.log(`=== 水印排查 ${img.name} (${W}×${H}) ===\n`);
  console.log('[A] 区域高频密度（仅供定位参考，不参与判定 —— 实测会被底图自身纹理误报）');
  console.log('  区域        位置(x0,y0,x1,y1)          均值    σ    暗笔画占比  高频密度  相对基线');
  for (const m of metrics) {
    const rel = m.edge / base.edge;
    const flag = (m !== base && rel > 1.25) ? '  ⚠️' : '';
    console.log(`  ${m.label.padEnd(10)}  ${String(m.box.join(',')).padEnd(22)}  ${m.mean.toFixed(1).padStart(5)}  ${m.std.toFixed(1).padStart(5)}  ${pct(m.ink).padStart(8)}  ${m.edge.toFixed(2).padStart(7)}  ${rel.toFixed(2)}×${flag}`);
  }
  const susA = metrics.slice(0, 3).filter(m => m.edge / base.edge > 1.25);

  console.log(`\n[B] 亮笔画文字（局部 top-hat r=${radius}px，阈值 ${thr.toFixed(1)}）—— 针对白色/近白水印`);
  console.log(`    连通域 ${allComp.length} 个 → 近白字形排成的文字行 ${runs.length} 条`);
  if (opt.debug) {
    console.log('    未过滤的候选行（调试）：');
    for (const r of asGlyphRun(allComp, W, H).slice(0, 6)) {
      const ok = r.span >= 1.2 * r.strokeHeight && r.heightSpread < 0.35;
      console.log(`      ${ok ? '✔' : '✗'} 字形 ${r.glyphs}  跨度 ${r.span}  笔画高 ${r.strokeHeight.toFixed(1)}  离散 ${(r.heightSpread * 100).toFixed(0)}%  体积 ${r.weight}  对比Δ ${r.meanDiff.toFixed(1)}  ← ${r.members.join(' | ')}`);
    }
  }
  for (const r of runs.slice(0, opt.debug ? 5 : 1)) {
    const [x0, y0, x1, y1] = r.box;
    console.log(`      ${r === textLine ? '⚠️' : '  '} bbox[${x0},${y0} .. ${x1},${y1}]  ${x1 - x0}×${y1 - y0}  字形 ${r.glyphs} 个  笔画高 ${r.strokeHeight.toFixed(1)}px  高度离散 ${(r.heightSpread * 100).toFixed(0)}%  像素 ${r.weight}`);
    console.log(`         位置：${y0 / H > 0.5 ? '下半部' : '上半部'}·${(x0 + x1) / 2 > W * 0.6 ? '偏右' : (x0 + x1) / 2 < W * 0.4 ? '偏左' : '居中'}`);
  }
  if (opt.debug) {
    const near = allComp.filter(c => c.y + c.h > H * 0.85).sort((a, b) => b.n - a.n).slice(0, 8);
    console.log('    底部 15% 条带内的近白连通域（按体积）：');
    for (const c of near) {
      const [r, g, b] = c.color;
      const fill = c.n / (c.w * c.h);
      console.log(`      n=${String(c.n).padStart(6)}  bbox[${c.x},${c.y} ${c.w}×${c.h}]  填充 ${fill.toFixed(2)}  色 rgb(${r.toFixed(0)},${g.toFixed(0)},${b.toFixed(0)})  Δdiff ${c.meanDiff.toFixed(1)}`);
    }
  }
  if (textHit) {
    const [x0, y0, x1, y1] = textLine.box;
    console.log(`    ⚠️ 判定命中：文字行 bbox [${x0},${y0} .. ${x1},${y1}]`);
    console.log(`       复核：node tools/art_check.mjs crop ${img.name} --box ${Math.max(0, x0 - 40)},${Math.max(0, y0 - 40)},${Math.min(W, x1 + 40)},${Math.min(H, y1 + 40)} --out /tmp/wm_check.png`);
  } else {
    console.log('    ✅ 未检出成行的亮笔画文字');
  }

  const hit = textHit;
  console.log('');
  if (hit) {
    console.log('⚠️ 判定：图上有**文字/水印**（ART_PLAN §一 硬规则：不得含文字/水印）。请裁除或重生成。');
  } else if (susA.length) {
    console.log('✅ 判定：未检出文字/水印。');
    console.log(`   （附注：区域 ${susA.map(m => m.label).join('、')} 的高频密度高于中央对照，但未形成字形行，判为底图纹理。）`);
  } else {
    console.log('✅ 判定：未检出文字/水印。');
    console.log('   （本检测器针对**白色/近白文字**；深色、彩色或极低对比水印仍可能漏检，重要素材请人眼复核。）');
  }
  console.log(`   复核捷径： node tools/art_check.mjs crop ${img.name} --box <可疑区> --out /tmp/check.png  → 用 vision 读该图`);

  if (!opt.crop) {
    console.log('\n（加 --crop 可裁掉边缘区并另存，例：--crop --inset 40 --out clean.png）');
    return hit ? 2 : 0;
  }

  const inset = Number(opt.inset ?? Math.round(Math.min(W, H) * 0.03));
  const edges = String(opt.edges ?? 'bottom,right').split(',').map(s => s.trim());
  const left = edges.includes('left') ? inset : 0;
  const right = edges.includes('right') ? inset : 0;
  const top = edges.includes('top') ? inset : 0;
  const bottom = edges.includes('bottom') ? inset : 0;
  const nw = W - left - right, nh = H - top - bottom;
  if (nw <= 0 || nh <= 0) { console.error(`裁除量过大：${inset}px 会把图裁没（原图 ${W}×${H}）`); return 2; }
  const out = Buffer.alloc(nw * nh * 4);
  for (let y = 0; y < nh; y++) {
    const src = ((y + top) * W + left) * 4;
    data.copy(out, y * nw * 4, src, src + nw * 4);
  }
  const outPath = opt.out ?? img.name.replace(/\.png$/i, `_cropped.png`);
  writeFileSync(outPath, encodePNG(out, nw, nh));
  console.log(`\n已裁除 left=${left} right=${right} top=${top} bottom=${bottom}px → ${nw}×${nh}`);
  console.log(`写出 ${outPath}`);
  console.log('⚠️ 裁除会改变构图与网格位置：带网格的底图裁完必须重跑 grid 并重设锚点。');
  return 0;
}

// ═════════════════════════════════════════════════════════════════════════════
// crop —— 裁任意矩形另存（取局部交给人眼/vision 复核）
// ═════════════════════════════════════════════════════════════════════════════

function cmdCrop(img, opt) {
  const { width: W, height: H, data } = img;
  if (!opt.box) { console.error('crop 需要 --box x0,y0,x1,y1'); return 2; }
  const [x0, y0, x1, y1] = String(opt.box).split(',').map(Number);
  if ([x0, y0, x1, y1].some(v => !Number.isFinite(v))) { console.error('--box 解析失败，应为 x0,y0,x1,y1'); return 2; }
  const cx0 = Math.max(0, Math.min(W, Math.round(x0)));
  const cy0 = Math.max(0, Math.min(H, Math.round(y0)));
  const cx1 = Math.max(cx0 + 1, Math.min(W, Math.round(x1)));
  const cy1 = Math.max(cy0 + 1, Math.min(H, Math.round(y1)));
  const nw = cx1 - cx0, nh = cy1 - cy0;
  const out = Buffer.alloc(nw * nh * 4);
  for (let y = 0; y < nh; y++) {
    const src = ((y + cy0) * W + cx0) * 4;
    data.copy(out, y * nw * 4, src, src + nw * 4);
  }
  const outPath = opt.out ?? img.name.replace(/\.png$/i, `_crop_${cx0}_${cy0}.png`);
  writeFileSync(outPath, encodePNG(out, nw, nh));
  console.log(`裁剪 [${cx0},${cy0} .. ${cx1},${cy1}] → ${nw}×${nh}`);
  console.log(`写出 ${outPath}`);
  return 0;
}

// ═════════════════════════════════════════════════════════════════════════════
// main
// ═════════════════════════════════════════════════════════════════════════════

const argv = process.argv.slice(2);
const cmd = argv[0];
const opt = args(argv.slice(1));
DEBUG = !!opt.debug;

if (!cmd || cmd === 'help' || cmd === '--help' || opt.help) { usage(); process.exit(0); }
if (!opt._.length) { console.error('缺少图片路径。用 `node tools/art_check.mjs` 看用法。'); process.exit(2); }

const COMMANDS = { info: cmdInfo, palette: cmdPalette, grid: cmdGrid, watermark: cmdWatermark, crop: cmdCrop };
if (!COMMANDS[cmd]) { console.error(`未知命令 "${cmd}"。可选：${Object.keys(COMMANDS).join(' / ')}`); process.exit(2); }

let code = 0;
for (const p of opt._) {
  try {
    const img = loadImage(p);
    mark(`载入+解码 ${img.width}×${img.height}`);
    if (opt._.length > 1) console.log(`\n──────── ${p} ────────`);
    code = Math.max(code, COMMANDS[cmd](img, opt) ?? 0);
  } catch (e) {
    console.error(`✗ ${p}: ${e.message}`);
    code = 2;
  }
}
process.exit(code);
