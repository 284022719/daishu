#!/usr/bin/env node
/**
 * md_structure_check.mjs —— Markdown 结构守卫（零依赖）
 *
 * 为什么需要它：**拿"标题行"当 edit 的替换锚点**时，很容易漏写回旧标题 ——
 * 结果旧标题消失、它的正文成了"挂在上一节下面"的孤儿：内容都还在，肉眼扫过去像正常文档。
 * 实测在同一个会话里连踩三次（`docs/PRE_RELEASE_UI_CHECK.md` 的 ⑫/⑬ 两节 + 重复表格行）。
 * 所以任何插入/重排章节之后，用它机械地验一遍，别靠眼睛。
 *
 * 检查项：
 *   1. 标题是否重复
 *   2. 每个标题下面是否**紧跟着正文**（空行不算）—— 防"孤儿正文"
 *   3. 连续两个标题之间是否有空节（既无正文也无子标题）
 *   4. 表格是否成对（`| # | ... |` 表头后面应紧跟 `|---|` 分隔行）
 *   5. 文本行末尾是否有"游离的表格行"（形如 `| x | ... |` 但不在表格块里）
 *   6. 代码围栏 ``` 是否成对
 *
 * 用法：
 *   node tools/md_structure_check.mjs <file.md> [<file2.md> ...]
 *   node tools/md_structure_check.mjs --selftest      # 用合成样本验证本脚本自己有效
 *
 * 退出码：0 = 通过 / 1 = 发现问题 / 2 = 用法错误
 */
import { readFileSync } from 'node:fs';
import { basename } from 'node:path';

function check(text) {
  const lines = text.split(/\r?\n/);
  const problems = [];

  // 1 + 2 + 3：标题
  const heads = [];
  for (let i = 0; i < lines.length; i++) {
    const m = /^(#{1,6})\s+(.*)$/.exec(lines[i]);
    if (m) heads.push({ line: i + 1, level: m[1].length, text: m[2].trim() });
  }
  const seen = new Map();
  const dupReported = new Set();
  for (const h of heads) {
    const key = `${h.level}:${h.text}`;
    if (seen.has(key)) {
      // 同一组重复只报一次（N 个同名标题不要报 N 次）
      if (!dupReported.has(key)) {
        const all = heads.filter((x) => x.level === h.level && x.text === h.text).map((x) => x.line);
        problems.push(`标题重复：「${h.text}」出现在第 ${all.join(' / ')} 行（共 ${all.length} 处）`);
        dupReported.add(key);
      }
    } else seen.set(key, h.line);
  }
  for (let k = 0; k < heads.length; k++) {
    const cur = heads[k];
    const next = heads[k + 1];
    // 下一个标题层级更深 = 当前标题是"章节容器"，它没有直接正文**是正常的**（如文档标题 + 章）
    if (next && next.level > cur.level) continue;
    const end = next ? next.line - 1 : lines.length;
    let body = 0;
    for (let i = cur.line; i < end; i++) {
      const t = lines[i].trim();
      if (t !== '' && !t.startsWith('<!--')) body++;
    }
    if (body === 0) problems.push(`第 ${cur.line} 行「${cur.text}」是空节（标题下没有任何正文，直到下一个标题）`);
  }

  // 4：表格分隔行
  for (let i = 0; i < lines.length; i++) {
    if (/^\|\s*#\s*\|/.test(lines[i])) {
      const nx = (lines[i + 1] ?? '').trim();
      if (!/^\|[\s:-]+\|/.test(nx)) problems.push(`第 ${i + 1} 行是表头，但下一行不是分隔行（实际「${nx}」）`);
    }
  }

  // 5：游离表格行 —— 形如 | 内容 | 但前一行既不是表格也不是空行
  for (let i = 0; i < lines.length; i++) {
    const t = lines[i].trim();
    if (!/^\|.*\|$/.test(t)) continue;
    const prev = (lines[i - 1] ?? '').trim();
    const isSep = /^\|[\s:-]+\|/.test(t);
    if (!isSep && prev !== '' && !/^\|/.test(prev)) {
      problems.push(`第 ${i + 1} 行像是游离的表格行（上一行不是表格）：${t.slice(0, 60)}`);
    }
  }

  // 6：代码围栏
  const fences = lines.filter((l) => /^\s*```/.test(l)).length;
  if (fences % 2 !== 0) problems.push(`代码围栏 \`\`\` 数量为奇数（${fences}）—— 有未闭合的代码块`);

  return { heads: heads.length, problems };
}

function selftest() {
  const bad = [
    '# T', '', '## A', '正文 A', '', '## A', '正文 A2',
    '', '## B', '', '## C', '正文 C', '| ⑬ | 游离 |', '', '```', 'code',
  ].join('\n');
  const good = ['# T', '', '## A', '正文 A', '', '## B', '正文 B', '', '## C', '正文 C'].join('\n');
  const rb = check(bad);
  const rg = check(good);
  console.log('自检 —— 坏样本应报出问题：');
  for (const p of rb.problems) console.log('  · ' + p);
  console.log(`自检 —— 好样本应无问题：${rg.problems.length === 0 ? '是' : '否 → ' + rg.problems.join(' | ')}`);
  const ok = rb.problems.length >= 4 && rg.problems.length === 0;
  console.log(`自检结论：${ok ? 'PASS（本脚本确实能抓到这几类问题）' : 'FAIL（脚本本身不可信）'}`);
  return ok ? 0 : 1;
}

const args = process.argv.slice(2);
if (args.includes('--selftest')) process.exit(selftest());
if (args.length === 0) {
  console.error('用法: node tools/md_structure_check.mjs <file.md> [...]  或 --selftest');
  process.exit(2);
}

let failed = false;
for (const f of args) {
  const { heads, problems } = check(readFileSync(f, 'utf8'));
  console.log(`=== ${basename(f)} —— ${heads} 个标题 ===`);
  if (problems.length === 0) console.log('  ✅ 结构检查通过');
  else {
    failed = true;
    for (const p of problems) console.log('  ⚠️ ' + p);
  }
}
process.exit(failed ? 1 : 0);
