#!/usr/bin/env python3
"""Build the private blind-labelling page for the human check (COLLAB-006, 2026-11-05).

Inputs, and the only inputs: sample_games.txt, labels_human.csv (must still be blank) and the rendered
first frames ../frames/<game>.png. It never opens manual_labels.csv, levels.csv, features.json or the
paper, so the page cannot carry an AI label or a label statistic. Definitions are copied from
INSTRUCTIONS.md. The page stores what the annotator clicks; the frozen kappa.py still does the scoring.

Two builds. The default is the claude.ai Artifact page, which stores rows in the artifact database.
--offline (added 2026-11-05 for two annotators) is one self-contained file: no network, no login, answers
stay in that browser's localStorage until the annotator downloads labels_<name>.csv. The extra CSV columns
(annotator, exposure, at) do not affect kappa.py, which reads game, level and label by name.

Usage: python3 -I build_label_page.py <out.html> [--offline]
"""
import base64
import csv
import io
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CELL, GAP, HEADER = 256, 8, 14  # layout written by ../render_levels.py: 64 x 4 px frames with a 14 px caption


def crop_levels(game):
    img = Image.open(os.path.join(HERE, "..", "frames", f"{game}.png")).convert("RGB")
    n, rest = divmod(img.width, CELL + GAP)
    assert rest == 0 and img.height == CELL + HEADER, (game, img.size)
    out = {}
    for i in range(n):
        x = i * (CELL + GAP)
        buf = io.BytesIO()
        img.crop((x, 0, x + CELL, CELL + HEADER)).save(buf, "PNG", optimize=True)
        out[i + 1] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    return n, out


def main(out_path, offline=False):
    games = [g.strip() for g in open(os.path.join(HERE, "sample_games.txt")) if g.strip() and not g.startswith("#")]
    rows = list(csv.DictReader(open(os.path.join(HERE, "labels_human.csv"))))
    assert len(rows) == 44 and all(not r["label"].strip() for r in rows), "labels_human.csv is no longer blank"
    items = [{"game": r["game"], "level": int(r["level"])} for r in rows]
    frames = {}
    for g in games:
        n, cells = crop_levels(g)
        assert {i["level"] for i in items if i["game"] == g} == set(range(2, n + 1)), g
        frames[g] = cells
    page = TEMPLATE
    for token, value in (OFFLINE_PARTS if offline else ONLINE_PARTS).items():
        page = page.replace(token, value)
    page = page.replace("__DATA__", json.dumps({"games": games, "items": items, "frames": frames}, separators=(",", ":")))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    print(out_path, f"{len(page.encode()) / 1024:.0f} KiB", len(games), "games", len(items), "levels", "offline" if offline else "artifact")


ONLINE_PARTS = {
    "__OFFLINE__": "false",
    "__DOC_OPEN__": "",
    "__HEAD_EXTRA__": '<meta name="claude:viewport-fit-sides" content="cover">\n'
                      '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&display=swap">\n',
    "__HOW__": """<li>键盘也行：S、V、N 选标签，左右方向键翻关。</li>
      <li>拿不准就选最接近的一个，再勾“不确定”。</li>
      <li>每次点选都会保存，换设备写同一个名字可以接着标。</li>
      <li>标完之前不要打开论文稿、Writeup、封面和结果文件。</li>""",
    "__FINISH__": "44 关都标完了。回到对话说一声，Claude 会把结果写回去并算一致性。",
}

OFFLINE_PARTS = {
    "__OFFLINE__": "true",
    "__DOC_OPEN__": '<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
                    '<meta name="viewport" content="width=device-width,initial-scale=1">\n',
    "__HEAD_EXTRA__": "",
    "__HOW__": """<li>这个文件不联网，也不上传。你的答案只存在这个浏览器里，标完下载 CSV 交出来。</li>
      <li>键盘也行：S、V、N 选标签，左右方向键翻关。写完备注按回车，就能接着用键盘。</li>
      <li>拿不准就选最接近的一个，再勾“不确定”。</li>
      <li>关掉再开，写同一个名字就能接着标。换浏览器或换电脑接不上；不要用无痕窗口，也不要在聊天软件的预览里标。</li>
      <li>两人各标各的。两份都交齐之前，不要讨论具体关卡，也不要先对标准。</li>
      <li>标完之前不要看论文稿、Writeup、封面、结果文件和私有仓库里的其他内容，不要查这些游戏的机制资料，也不要去玩这几局。</li>""",
    "__FINISH__": """<p>44 关都标完了。回答下面一题，点“下载 CSV”，把文件交给组织这次标注的人。两份都交齐之前，不要打开对方的文件。</p>
      <label class="exp" for="exposure">标完之前，你有没有看过 AI 的标签、标签统计或论文稿？照实选，论文会如实写。
        <select id="exposure"><option value="">请选择</option><option value="none">没看过</option><option value="partial">看过一部分</option></select>
      </label>
      <input type="text" id="exposureText" autocomplete="off" placeholder="看过什么，大概什么时候" hidden>""",
}

TEMPLATE = r"""__DOC_OPEN__<title>关卡盲标</title>
__HEAD_EXTRA__<style>
/* Layout: two first frames side by side are the instrument; the three label buttons sit beside them. */
:root {
  --bg: #eef0ec; --surface: #fbfbf9; --ink: #16181d; --muted: #565c66; --line: #cdd1ca;
  --accent: #1456c8; --on-accent: #ffffff; --warn: #a33a12;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
  --sans: -apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #111316; --surface: #1a1d21; --ink: #e8eaed; --muted: #a0a7b2; --line: #30353c;
  --accent: #79a9ff; --on-accent: #0c1420; --warn: #f0a07a; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #111316; --surface: #1a1d21; --ink: #e8eaed; --muted: #a0a7b2; --line: #30353c;
  --accent: #79a9ff; --on-accent: #0c1420; --warn: #f0a07a; color-scheme: dark }
* { box-sizing: border-box }
body { margin: 0; background: var(--bg); color: var(--ink); font-family: var(--sans); font-size: 14px; line-height: 1.5 }
.wrap { max-width: 1240px; margin: 0 auto; padding-block: 16px 32px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: flex; flex-direction: column; gap: 14px }
header { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 12px 24px }
header > div:first-child { flex: 1 1 280px; min-width: 0 }
h1 { margin: 0; font-size: 22px; font-weight: 600; text-wrap: balance }
header p { margin: 2px 0 0; color: var(--muted) }
.who { display: flex; flex-direction: column; gap: 3px; color: var(--muted); font-size: 12px }
input[type=text] { font: inherit; color: var(--ink); background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: 6px 9px; min-width: 0; width: 100% }
.count { font-family: var(--mono); font-weight: 600; font-size: 20px; font-variant-numeric: tabular-nums; white-space: nowrap }
.status { color: var(--muted); font-size: 12px; min-height: 18px }
.status.bad { color: var(--warn) }
.map { display: flex; flex-wrap: wrap; gap: 6px 16px }
.map .g { display: flex; align-items: center; gap: 3px }
.map .g b { font-family: var(--mono); font-weight: 500; font-size: 12px; color: var(--muted); margin-right: 3px }
.dot { width: 22px; height: 22px; padding: 0; border: 1px solid var(--line); border-radius: 4px; background: var(--surface); color: var(--ink); font-family: var(--mono); font-size: 11px; cursor: pointer }
.dot.done { background: var(--ink); color: var(--bg); border-color: var(--ink) }
.dot.cur { outline: 2px solid var(--accent); outline-offset: 1px }
main { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 18px; align-items: start }
@media (max-width: 900px) { main { grid-template-columns: minmax(0, 1fr) } }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 10px }
figure { margin: 0; min-width: 0 }
figcaption { font-size: 12px; color: var(--muted); margin-bottom: 4px }
figcaption b { font-family: var(--mono); color: var(--ink); font-weight: 600 }
.cur-frame figcaption b { color: var(--accent) }
.pair img { display: block; width: 100%; height: auto; image-rendering: pixelated; background: #fff; border-radius: 2px }
.cur-frame img { outline: 3px solid var(--accent) }
.strip-title { margin: 14px 0 6px; font-size: 12px; color: var(--muted) }
.strip { display: flex; flex-wrap: wrap; gap: 6px }
.tile { padding: 0; border: 2px solid transparent; border-radius: 3px; background: none; cursor: pointer; line-height: 0 }
.tile img { width: 104px; max-width: 100%; height: auto; image-rendering: pixelated; display: block; background: #fff }
.tile.on { border-color: var(--ink) }
.panel { display: flex; flex-direction: column; gap: 12px; min-width: 0 }
.choices { display: flex; flex-direction: column; gap: 8px }
.choice { display: grid; grid-template-columns: 40px minmax(0, 1fr); gap: 10px; align-items: center; text-align: left; font: inherit; color: var(--ink); background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 10px 12px; cursor: pointer }
.choice:hover { border-color: var(--accent) }
.choice .k { font-family: var(--mono); font-weight: 600; font-size: 28px; line-height: 1; text-align: center }
.choice .d { font-size: 13px; line-height: 1.45 }
.choice[aria-pressed="true"] { background: var(--accent); color: var(--on-accent); border-color: var(--accent) }
.note { display: flex; flex-direction: column; gap: 6px }
.note label { font-size: 12px; color: var(--muted) }
.note .row { display: flex; align-items: center; gap: 10px }
.note .row input[type=text] { flex: 1 1 auto }
.unsure { display: flex; align-items: center; gap: 5px; white-space: nowrap; color: var(--ink) !important; font-size: 13px !important }
.navrow { display: flex; gap: 8px }
.btn { flex: 1 1 0; font: inherit; color: var(--ink); background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: 7px 10px; cursor: pointer }
.btn:disabled { color: var(--muted); cursor: default; opacity: .6 }
.how { color: var(--muted); font-size: 13px; margin: 0; padding-left: 18px }
.how li + li { margin-top: 3px }
.finish { border: 1px solid var(--accent); border-radius: 8px; padding: 10px 12px; display: flex; flex-direction: column; gap: 8px }
.finish[hidden] { display: none }
.finish p { margin: 0 }
.exp { display: flex; flex-direction: column; gap: 6px; font-size: 13px }
select { font: inherit; color: var(--ink); background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: 6px 9px }
textarea { font-family: var(--mono); font-size: 12px; width: 100%; height: 150px; color: var(--ink); background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: 8px }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }
</style>

<div class="wrap">
<header>
  <div>
    <h1>关卡盲标</h1>
    <p>只看每关的第一帧，和同一局前面所有关比，不用玩。共 7 局 44 关。</p>
  </div>
  <label class="who" for="annotator">标注人（写上名字再开始）
    <input type="text" id="annotator" autocomplete="off" placeholder="你的名字">
  </label>
  <div>
    <div class="count"><span id="doneCount">0</span> / 44</div>
    <div class="status" id="status" role="status"></div>
  </div>
</header>
<nav class="map" id="map" aria-label="关卡进度"></nav>
<main>
  <section>
    <div class="pair">
      <figure><figcaption id="capRef"></figcaption><img id="imgRef" alt=""></figure>
      <figure class="cur-frame"><figcaption id="capCur"></figcaption><img id="imgCur" alt=""></figure>
    </div>
    <p class="strip-title">同一局前面的关，点一张放到左边对照：</p>
    <div class="strip" id="strip"></div>
  </section>
  <section class="panel">
    <div class="choices" role="group" aria-label="选一个标签">
      <button class="choice" id="pickS" type="button" data-label="S" aria-pressed="false"><span class="k">S</span><span class="d">没有前面没出现过的元素类型，只是布局、数量、大小或参数（颜色、钥匙形状等）变了</span></button>
      <button class="choice" id="pickV" type="button" data-label="V" aria-pressed="false"><span class="k">V</span><span class="d">已知元素以新的配置出现，可能改变用法，例如镜像轴从竖直变成水平、两条链交叉、调色板多了颜色</span></button>
      <button class="choice" id="pickN" type="button" data-label="N" aria-pressed="false"><span class="k">N</span><span class="d">出现了新的元素类型或新的全局条件，例如新物体、新的界面元素、迷雾</span></button>
    </div>
    <div class="note">
      <label for="note">备注，可以不写。先写备注再点标签，点完会跳到下一关。</label>
      <div class="row">
        <input type="text" id="note" autocomplete="off" placeholder="半句理由">
        <label class="unsure" for="unsure"><input type="checkbox" id="unsure">不确定</label>
      </div>
    </div>
    <div class="navrow">
      <button class="btn" id="prev" type="button">← 上一关</button>
      <button class="btn" id="next" type="button">下一关 →</button>
    </div>
    <div class="finish" id="finish" hidden>__FINISH__</div>
    <ul class="how">
      __HOW__
    </ul>
    <div class="navrow">
      <button class="btn" id="dlCsv" type="button" hidden>下载 CSV</button>
      <button class="btn" id="copyCsv" type="button">复制结果 CSV</button>
    </div>
    <textarea id="csvOut" readonly hidden aria-label="结果 CSV"></textarea>
  </section>
</main>
</div>

<script id="pageData" type="application/json">__DATA__</script>
<script>
(function () {
  const OFFLINE = __OFFLINE__;
  const DATA = JSON.parse(document.getElementById('pageData').textContent);
  const ITEMS = DATA.items, FRAMES = DATA.frames;
  const $ = (id) => document.getElementById(id);
  const key = (it) => it.game + '|' + it.level;
  let idx = 0, ref = 1, name = '', slug = '', labels = {}, db = null, unsub = null;
  const chains = {}, failed = new Set();

  function store(fn) { try { return fn(window.localStorage); } catch (e) { return null; } }
  const STORAGE_OK = store((ls) => { ls.setItem('__probe', '1'); const ok = ls.getItem('__probe') === '1'; ls.removeItem('__probe'); return ok; }) === true;
  function idleStatus() {
    if (OFFLINE && !STORAGE_OK) setStatus('这个浏览器不让存。关页面之前一定要点“下载 CSV”。', true);
    else setStatus('');
  }
  function loadExposure() {
    if (!$('exposure')) return;
    let v = {};
    try { v = JSON.parse(store((ls) => ls.getItem('exposure:' + slug)) || '{}'); } catch (e) { v = {}; }
    $('exposure').value = v.answer || '';
    $('exposureText').value = v.text || '';
    $('exposureText').hidden = $('exposure').value !== 'partial';
  }
  function saveExposure() {
    store((ls) => ls.setItem('exposure:' + slug, JSON.stringify({ answer: $('exposure').value, text: $('exposureText').value })));
    $('exposureText').hidden = $('exposure').value !== 'partial';
  }
  function exposureValue() {
    if (!$('exposure')) return '';
    return $('exposure').value === 'partial' ? 'partial: ' + $('exposureText').value.trim() : $('exposure').value;
  }
  function csvText() {
    const q = (s) => /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    return ['game,level,label,note,annotator,exposure,at'].concat(ITEMS.map((it) => {
      const v = labels[key(it)] || { label: '', note: '' };
      return [it.game, it.level, v.label, q(v.note || ''), q(name), q(exposureValue()), v.at || ''].join(',');
    })).join('\n') + '\n';
  }
  function slugOf(s) {
    return Array.from(s.trim().toLowerCase()).map((c) => /[a-z0-9_-]/.test(c) ? c : 'u' + c.codePointAt(0).toString(16)).join('').slice(0, 60);
  }
  function saveLocal() { store((ls) => ls.setItem('labels:' + slug, JSON.stringify(labels))); }
  function loadLocal() {
    const raw = store((ls) => ls.getItem('labels:' + slug));
    try { labels = raw ? JSON.parse(raw) : {}; } catch (e) { labels = {}; }
  }
  function setStatus(text, bad) { const el = $('status'); el.textContent = text; el.classList.toggle('bad', !!bad); }

  function firstOpen() { const i = ITEMS.findIndex((it) => !labels[key(it)]); return i < 0 ? ITEMS.length - 1 : i; }
  function doneCount() { return ITEMS.filter((it) => labels[key(it)]).length; }

  function renderMap() {
    const map = $('map');
    map.textContent = '';
    DATA.games.forEach((g) => {
      const wrap = document.createElement('div');
      wrap.className = 'g';
      const b = document.createElement('b');
      b.textContent = g;
      wrap.appendChild(b);
      ITEMS.forEach((it, i) => {
        if (it.game !== g) return;
        const d = document.createElement('button');
        const v = labels[key(it)];
        d.type = 'button';
        d.className = 'dot' + (v ? ' done' : '') + (i === idx ? ' cur' : '');
        d.textContent = v ? v.label : '';
        d.title = g + ' 第 ' + it.level + ' 关';
        d.setAttribute('aria-label', d.title + (v ? '，已标 ' + v.label : '，未标'));
        d.addEventListener('click', () => go(i));
        wrap.appendChild(d);
      });
      map.appendChild(wrap);
    });
  }

  function renderLevel() {
    const it = ITEMS[idx], cells = FRAMES[it.game];
    $('capCur').innerHTML = '';
    const capCur = document.createElement('b');
    capCur.textContent = it.game + ' L' + it.level;
    $('capCur').append(capCur, ' 要标的这一关');
    $('imgCur').src = cells[it.level];
    $('imgCur').alt = it.game + ' 第 ' + it.level + ' 关的第一帧';
    if (ref >= it.level) ref = it.level - 1;
    $('capRef').innerHTML = '';
    const capRef = document.createElement('b');
    capRef.textContent = it.game + ' L' + ref;
    $('capRef').append(capRef, ' 用来对照');
    $('imgRef').src = cells[ref];
    $('imgRef').alt = it.game + ' 第 ' + ref + ' 关的第一帧';
    const strip = $('strip');
    strip.textContent = '';
    for (let l = 1; l < it.level; l++) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'tile' + (l === ref ? ' on' : '');
      b.setAttribute('aria-label', '对照第 ' + l + ' 关');
      const img = document.createElement('img');
      img.src = cells[l];
      img.alt = it.game + ' 第 ' + l + ' 关';
      b.appendChild(img);
      b.addEventListener('click', () => { ref = l; renderLevel(); });
      strip.appendChild(b);
    }
  }

  function renderForm() {
    const v = labels[key(ITEMS[idx])] || {};
    document.querySelectorAll('.choice').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.label === v.label)));
    const note = v.note || '', unsure = note.indexOf('不确定') >= 0;
    if (document.activeElement !== $('note')) $('note').value = note.replace(/^不确定[；;，, ]*/, '');
    $('unsure').checked = unsure;
    $('prev').disabled = idx === 0;
    $('next').disabled = idx === ITEMS.length - 1;
    const n = doneCount();
    $('doneCount').textContent = String(n);
    $('finish').hidden = n !== ITEMS.length;
  }

  function render() { renderMap(); renderLevel(); renderForm(); }
  function go(i) {
    idx = Math.max(0, Math.min(ITEMS.length - 1, i));
    ref = ITEMS[idx].level - 1;
    $('note').value = '';
    $('unsure').checked = false;
    render();
  }
  function currentNote() {
    const t = $('note').value.trim();
    return $('unsure').checked ? ('不确定' + (t ? '；' + t : '')) : t;
  }

  function writeDoc(k) {
    if (!db) return;
    const v = labels[k], parts = k.split('|');
    const body = { annotator: slug, name: name, game: parts[0], level: Number(parts[1]), label: v.label, note: v.note || '', at: new Date().toISOString() };
    chains[k] = (chains[k] || Promise.resolve()).then(() => db.collection('labels').doc(slug + '~' + parts[0] + '~' + parts[1]).set(body))
      .then(() => { failed.delete(k); if (!failed.size) setStatus('已保存'); })
      .catch(() => { failed.add(k); setStatus('有 ' + failed.size + ' 关没存上。这个浏览器里还留着，可以用“复制结果 CSV”发给 Claude。', true); });
  }
  function pick(label) {
    if (!slug) { setStatus('先在右上角写上名字。', true); $('annotator').focus(); return; }
    const it = ITEMS[idx], k = key(it);
    labels[k] = { label: label, note: currentNote(), at: new Date().toISOString() };
    saveLocal();
    Array.from(failed).forEach((f) => { if (f !== k) writeDoc(f); });
    writeDoc(k);
    if (OFFLINE) { if (STORAGE_OK) setStatus('已存在这个浏览器里'); else idleStatus(); }
    else if (!db) setStatus('存储连不上，先存在这个浏览器里。标完用“复制结果 CSV”发给 Claude。', true);
    if (idx < ITEMS.length - 1) go(idx + 1); else render();
  }
  let noteTimer = 0;
  function noteChanged() {
    const k = key(ITEMS[idx]);
    if (!labels[k]) return;
    const n = currentNote();
    if (labels[k].note === n) return;
    labels[k].note = n;
    saveLocal();
    clearTimeout(noteTimer);
    noteTimer = setTimeout(() => writeDoc(k), 700);
  }

  function subscribe() {
    if (unsub) { unsub(); unsub = null; }
    if (!db || !slug) return;
    const slow = setTimeout(() => setStatus('存储暂时连不上，标注先存在这个浏览器里。', true), 10000);
    unsub = db.collection('labels').where('annotator', '==', slug).onSnapshot((snap) => {
      if (!snap.metadata.fromCache) clearTimeout(slow);
      let changed = false;
      snap.docs.forEach((d) => {
        const b = d.data(), k = b.game + '|' + b.level, cur = labels[k];
        if (!cur || cur.label !== b.label || cur.note !== b.note) {
          if (!snap.metadata.hasPendingWrites) { labels[k] = { label: b.label, note: b.note || '' }; changed = true; }
        }
      });
      if (changed) { saveLocal(); idx = firstOpen(); ref = ITEMS[idx].level - 1; render(); }
    }, () => { clearTimeout(slow); setStatus('存储断开了，标注先存在这个浏览器里。', true); });
  }
  function setName(v) {
    name = v.trim();
    slug = slugOf(name);
    if (!OFFLINE) store((ls) => ls.setItem('annotator', name));
    loadLocal();
    loadExposure();
    idx = firstOpen();
    ref = ITEMS[idx].level - 1;
    render();
    subscribe();
    if (slug) idleStatus();
  }

  document.querySelectorAll('.choice').forEach((b) => b.addEventListener('click', () => pick(b.dataset.label)));
  $('prev').addEventListener('click', () => go(idx - 1));
  $('next').addEventListener('click', () => go(idx + 1));
  $('note').addEventListener('input', noteChanged);
  $('unsure').addEventListener('change', noteChanged);
  $('annotator').addEventListener('change', (e) => setName(e.target.value));
  ['annotator', 'note'].forEach((id) => $(id).addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); e.target.blur(); }
  }));
  if ($('exposure')) {
    $('exposure').addEventListener('change', saveExposure);
    $('exposureText').addEventListener('input', saveExposure);
  }
  document.addEventListener('keydown', (e) => {
    const t = e.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT') && t.type !== 'checkbox') return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const c = e.key.toUpperCase();
    if (c === 'S' || c === 'V' || c === 'N') { e.preventDefault(); if (!e.repeat) pick(c); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); go(idx - 1); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); go(idx + 1); }
  });
  $('copyCsv').addEventListener('click', () => {
    if (OFFLINE && doneCount() === ITEMS.length && !$('exposure').value) { setStatus('先回答最后一题。', true); $('exposure').focus(); return; }
    const text = csvText();
    const out = $('csvOut');
    out.value = text;
    out.hidden = false;
    out.select();
    const done = () => setStatus(OFFLINE ? '已复制。' : '已复制，粘贴到对话里就行。');
    const fail = () => setStatus('浏览器没让复制，文字已选中，手动复制即可。');
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fail); else fail();
  });
  if (OFFLINE) {
    $('dlCsv').hidden = false;
    $('dlCsv').addEventListener('click', () => {
      if (!slug) { setStatus('先在右上角写上名字。', true); $('annotator').focus(); return; }
      const n = doneCount(), all = n === ITEMS.length;
      if (all && !$('exposure').value) { setStatus('先回答最后一题。', true); $('exposure').focus(); return; }
      const safe = name.replace(/[^\p{L}\p{N}_-]+/gu, '_') || 'anon';
      const file = all ? 'labels_' + safe + '.csv' : 'labels_' + safe + '_partial_' + n + 'of' + ITEMS.length + '.csv';
      const url = URL.createObjectURL(new Blob([csvText()], { type: 'text/csv;charset=utf-8' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = file;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
      setStatus(all ? '已下载 ' + file : '还差 ' + (ITEMS.length - n) + ' 关。这份只是备份，不是最终文件。');
    });
  }

  const saved = OFFLINE ? '' : (store((ls) => ls.getItem('annotator')) || '');
  $('annotator').value = saved;
  name = saved.trim();
  slug = slugOf(name);
  if (slug) { loadLocal(); loadExposure(); }
  idx = firstOpen();
  ref = ITEMS[idx].level - 1;
  render();
  if (OFFLINE) idleStatus();
  const use = !OFFLINE && window.claude && window.claude.use ? window.claude.use('db') : Promise.resolve(null);
  use.then((d) => { db = d; if (!d && !OFFLINE) setStatus('存储连不上，标注会存在这个浏览器里。', true); subscribe(); }, () => { if (!OFFLINE) setStatus('存储连不上，标注会存在这个浏览器里。', true); });
})();
</script>
"""

if __name__ == "__main__":
    main(sys.argv[1], offline="--offline" in sys.argv[2:])
