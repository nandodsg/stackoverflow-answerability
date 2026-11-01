"""Builds the hand-labeling page of the quality-label GOLD set (specs/003, "Quality labels").

    python labels/gold_page.py practice     # blind: the 20 practice questions, labeled from scratch
    python labels/gold_page.py scoring --review google/gemini-4-argon,spacexai/grok-4.7   # review two models' labels

The questions are the ids of the dbt view int_label_gold_questions; their original title, tags and body are read once
from int_post_history_scan (~1 GB) and cached in labels/.cache/. The page is written to labels/.cache/ too (it holds
question text, so it is not tracked) and opens in any browser from disk.

The page shows no outcome (no answer count, score or accepted flag; only the year). Images are not loaded: each one
is shown as an [image] placeholder, because the rubric judges from the text alone, as a labeling model does; HTML
tags typed into the body (an <img> in pasted JSX) are shown as text, as a model reads them. Labels autosave in the
browser; "Save CSV" writes labels/gold/gold_labels_<set>.csv (ids and labels, no text, tracked), with the rubric
version on every row.

Review mode (--review A,B) is how the scoring set is labeled: two models from other companies label every question
first (labels/label_questions.py), and the hand labeler reviews. A label both models agree on is filled in and can be
changed; a label they disagree on shows both reasons and waits for the hand labeler's pick. "Save CSV" writes
labels/gold/gold_labels_<set>_reviewed.csv with one `<label>__decision` column per label: `agreed` (kept the models'
shared level), `overrode` (changed it), `picked_<model>` (broke a tie for that model) or `other` (a third level).
"""

from __future__ import annotations

import argparse
import json
import sys

from common import BQ_DATASET, BQ_PROJECT, CACHE, LABELS, read_json, write_json, bq_query
from rubric import load_rubric

TEXT_CACHE = CACHE / "gold_text.json"
SETS = {"practice": 20, "scoring": 100}
MODEL_OUT = LABELS / "output" / "gold"


def load_questions() -> list[dict]:
    if TEXT_CACHE.exists():
        return read_json(TEXT_CACHE)
    sql = f"""
        select
            g.question_id, g.gold_set, g.gold_rank, g.creation_year,
            o.original_tags, o.original_title, o.original_body_text
        from `{BQ_PROJECT}.{BQ_DATASET}.int_label_gold_questions` as g
        join `{BQ_PROJECT}.{BQ_DATASET}.int_post_history_scan` as o
            on o.post_id = g.question_id and o.post_kind = 'question'
            and o.creation_year between 2018 and 2022
        order by g.gold_set, g.gold_rank
    """
    rows = bq_query(sql)
    if len(rows) != sum(SETS.values()):
        sys.exit(f"Expected {sum(SETS.values())} gold questions, got {len(rows)}.")
    write_json(TEXT_CACHE, rows)
    return rows


def review_data(models: list[str], questions: list[dict], gold_set: str, rubric: dict) -> dict:
    """Both models' level and reason per question and label; every question must be labeled on this rubric."""
    out = {"models": [{"id": m, "short": m.split("/")[-1].split("-")[0]} for m in models], "q": {}}
    runs = [read_json(MODEL_OUT / f"{m.replace('/', '_')}_{gold_set}.json") for m in models]
    for m, run in zip(models, runs):
        missing = [q["question_id"] for q in questions if str(q["question_id"]) not in run]
        if missing:
            sys.exit(f"{m} has not labeled {len(missing)} {gold_set} questions (e.g. {missing[0]}); run it first.")
        stale = {d["rubric_version"] for d in run.values()} - {rubric["version"]}
        if stale:
            sys.exit(f"{m} labeled on rubric {', '.join(stale)}, not the current {rubric['version']}.")
    for q in questions:
        qid = str(q["question_id"])
        out["q"][qid] = {l["key"]: [[run[qid]["labels"][l["key"]], run[qid].get("reasons", {}).get(l["key"], "")]
                                    for run in runs] for l in rubric["labels"]}
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("gold_set", choices=sorted(SETS))
    parser.add_argument("--review", help="two model ids, comma-separated, whose labels the hand labeler reviews")
    args = parser.parse_args()
    gold_set = args.gold_set
    questions = [q for q in load_questions() if q["gold_set"] == gold_set]
    rubric = load_rubric()
    models = args.review.split(",") if args.review else []
    if args.review and len(models) != 2:
        sys.exit("--review takes exactly two model ids, comma-separated.")
    data = {
        "set": gold_set,
        "rubric_version": rubric["version"],
        "rubric_text": rubric["text"],
        "review": review_data(models, questions, gold_set, rubric) if models else None,
        "labels": [{k: l[k] for k in ("key", "title", "levels", "section")} for l in rubric["labels"]],
        "questions": [
            {
                "id": q["question_id"],
                "rank": q["gold_rank"],
                "year": q["creation_year"],
                "tags": q["original_tags"].split("|") if q["original_tags"] else [],
                "title": q["original_title"],
                "body": q["original_body_text"],
            }
            for q in questions
        ],
    }
    # "</" inside the embedded JSON would close the <script> tag early.
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out = CACHE / f"gold_{gold_set}{'_review' if models else ''}.html"
    out.write_text(PAGE.replace("__DATA__", payload), encoding="utf-8")
    if models:
        r = data["review"]["q"]
        split = sum(v[0][0] != v[1][0] for q in r.values() for v in q.values())
        print(f"Review of {' and '.join(models)}: {split} of {len(r) * len(rubric['labels'])} labels to tie-break")
    print(f"{len(questions)} {gold_set} questions, rubric version {rubric['version']}")
    print(f"Open: {out}")


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gold labels</title>
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.1.6/dist/purify.min.js"></script>
<style>
:root {
  --bg: #f7f7f5; --panel: #ffffff; --text: #1d1d1b; --muted: #6b6b66; --line: #dddcd6;
  --accent: #2f5bd3; --accent-soft: #e6ecfb; --done: #2e7d4f; --code-bg: #f0efeb; --ph: #8a5a00; --ph-bg: #fff3d6;
  --warn: #c2410c; --warn-soft: #fff1e8; --agree-soft: #edf7f0;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #161615; --panel: #1f1f1d; --text: #e9e8e3; --muted: #9a9993; --line: #34332f;
    --accent: #8aa8ff; --accent-soft: #26304d; --done: #6cc893; --code-bg: #2a2a27; --ph: #ffcf70; --ph-bg: #3a2f14;
    --warn: #fb923c; --warn-soft: #3a2414; --agree-soft: #17291e;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
header { position: sticky; top: 0; z-index: 2; display: flex; gap: 12px; align-items: center; flex-wrap: wrap;
  padding: 10px 16px; background: var(--panel); border-bottom: 1px solid var(--line); }
header h1 { font-size: 15px; margin: 0 8px 0 0; }
header .grow { flex: 1; }
button { font: inherit; color: var(--text); background: var(--panel); border: 1px solid var(--line); border-radius: 6px;
  padding: 4px 10px; cursor: pointer; }
button:hover { border-color: var(--accent); }
button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.muted { color: var(--muted); }
#dots { display: flex; flex-wrap: wrap; gap: 3px; padding: 8px 16px; }
#dots span { width: 14px; height: 14px; border-radius: 3px; border: 1px solid var(--line); cursor: pointer; }
#dots span.part { background: var(--accent-soft); }
#dots span.done { background: var(--done); border-color: var(--done); }
#dots span.cur { outline: 2px solid var(--accent); outline-offset: 1px; }
main { display: grid; grid-template-columns: minmax(0, 1fr) 380px; gap: 16px; padding: 0 16px 40px; }
@media (max-width: 900px) { main { grid-template-columns: 1fr; } }
article, aside { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px 20px; min-width: 0; }
aside { position: sticky; top: 64px; align-self: start; max-height: calc(100vh - 80px); overflow: auto; }
article h2 { font-size: 20px; margin: 4px 0 12px; }
.tag { display: inline-block; font-size: 12px; padding: 1px 7px; margin: 0 4px 4px 0; border-radius: 10px; background: var(--accent-soft); }
#body pre { background: var(--code-bg); padding: 10px 12px; border-radius: 6px; overflow: auto; font-size: 13px; }
#body code { background: var(--code-bg); padding: 1px 4px; border-radius: 4px; font-size: 13px; }
#body pre code { padding: 0; background: none; }
#body blockquote { margin: 0; padding-left: 12px; border-left: 3px solid var(--line); color: var(--muted); }
#body table { border-collapse: collapse; } #body td, #body th { border: 1px solid var(--line); padding: 2px 6px; }
.img-ph { display: inline-block; padding: 1px 8px; border-radius: 4px; background: var(--ph-bg); color: var(--ph); font-size: 13px; }
.label { border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px; margin-bottom: 8px; }
.label.active { border-color: var(--accent); box-shadow: inset 3px 0 0 var(--accent); }
.label .name { font-weight: 600; font-size: 14px; }
.label .levels { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.label .levels button { font-size: 13px; padding: 3px 8px; }
.label .levels button.on { background: var(--accent); border-color: var(--accent); color: #fff; }
.label details { margin-top: 6px; font-size: 13px; }
.label details summary { cursor: pointer; color: var(--muted); }
.label .rule { padding: 4px 0 0; } .label .rule ul, .label .rule ol { padding-left: 18px; margin: 4px 0; }
textarea { width: 100%; min-height: 54px; font: inherit; font-size: 13px; color: var(--text); background: var(--bg);
  border: 1px solid var(--line); border-radius: 6px; padding: 6px; }
.keys { font-size: 12px; color: var(--muted); margin-top: 8px; }
kbd { border: 1px solid var(--line); border-bottom-width: 2px; border-radius: 4px; padding: 0 4px; font-size: 11px; }
#rubric { display: none; position: fixed; inset: 56px 16px 16px auto; width: min(720px, calc(100vw - 32px)); z-index: 3;
  overflow: auto; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px 24px; }
#rubric.open { display: block; }
#rubric table { border-collapse: collapse; font-size: 13px; } #rubric td, #rubric th { border: 1px solid var(--line); padding: 3px 6px; }
.rawtag { font-family: ui-monospace, Consolas, monospace; font-size: 13px; color: var(--muted); }
.label.agree { background: var(--agree-soft); }
.label.split { border-color: var(--warn); background: var(--warn-soft); }
.label .state { float: right; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .03em; }
.label.agree .state { color: var(--done); } .label.split .state { color: var(--warn); }
.mk { display: inline-block; font-size: 10px; line-height: 1.4; padding: 0 4px; margin-left: 4px; border-radius: 3px;
  background: var(--ph-bg); color: var(--ph); vertical-align: 1px; }
.levels button.on .mk { background: rgba(255,255,255,.25); color: #fff; }
.why { font-size: 12.5px; margin-top: 6px; } .why b { font-weight: 600; }
#dots span.tie { border: 2px solid var(--warn); }
</style>
</head>
<body>
<header>
  <h1>Gold labels · <span id="setname"></span></h1>
  <span class="muted">rubric <span id="version"></span></span>
  <span class="grow"></span>
  <span id="progress" class="muted"></span>
  <button id="prev">◀ Prev</button>
  <button id="next">Next ▶</button>
  <button id="nextOpen">Next unlabeled</button>
  <button id="toggleRubric">Rubric</button>
  <button id="confirm" hidden>Confirm ✓ <kbd>Enter</kbd></button>
  <button id="save" class="primary">Save CSV</button>
</header>
<div id="dots"></div>
<main>
  <article>
    <div class="muted" id="meta"></div>
    <h2 id="title"></h2>
    <div id="tags"></div>
    <div id="body"></div>
  </article>
  <aside>
    <div id="labelPanel"></div>
    <div class="label"><div class="name">Note (optional)</div><textarea id="note" placeholder="Anything unclear, e.g. why a borderline call went one way"></textarea></div>
    <div class="keys"><kbd>1</kbd>–<kbd>4</kbd> pick a level in the highlighted label (then it moves down) ·
      <kbd>↑</kbd><kbd>↓</kbd> change label · <kbd>→</kbd><kbd>←</kbd> next / previous question<span id="reviewKeys" hidden> ·
      <kbd>Enter</kbd> confirm the question and go to the next one</span></div>
  </aside>
</main>
<div id="rubric"></div>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const R = D.review;  // null on the blind page
const STORE = `gold${R ? '-review' : ''}:${D.set}:${D.rubric_version}`;
let state = {};
try { state = JSON.parse(localStorage.getItem(STORE) || '{}'); } catch (e) { state = {}; }
let cur = 0, activeLabel = 0;

function persist() { try { localStorage.setItem(STORE, JSON.stringify(state)); } catch (e) {} }
function entry(q) { return state[q.id] || (state[q.id] = {}); }
function isDone(q) { const e = state[q.id]; return !!e && D.labels.every(l => e[l.key]) && (!R || !!e.confirmed); }
function isPart(q) { const e = state[q.id]; return !!e && (R ? D.labels.some(l => isSplit(q, l) && e[l.key]) : D.labels.some(l => e[l.key])); }
function votes(q, l) { return R.q[String(q.id)][l.key]; }            // [[level, reason], [level, reason]]
function isSplit(q, l) { const v = votes(q, l); return v[0][0] !== v[1][0]; }
function hasTie(q) { return !!R && D.labels.some(l => isSplit(q, l)); }

// Review: a level both models chose is filled in (the hand labeler can change it); a split waits for a pick.
if (R) D.questions.forEach(q => D.labels.forEach(l => {
  const e = entry(q);
  if (!e[l.key] && !isSplit(q, l)) e[l.key] = votes(q, l)[0][0];
}));

// Tags typed into the body as raw HTML (an <img> or a component in pasted JSX) are shown as text, as a model reads
// them; only simple formatting tags render. So only Markdown images become [image] placeholders below.
const RAW_OK = new Set(['br', 'b', 'i', 'em', 'strong', 'kbd', 'sup', 'sub', 'code', 'pre', 'p', 'hr', 's', 'del',
  'strike', 'ul', 'ol', 'li', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'table', 'thead', 'tbody', 'tr',
  'td', 'th', 'div', 'span']);
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
marked.use({ renderer: { html(arg) {
  const t = typeof arg === 'string' ? arg : (arg && (arg.text || arg.raw)) || '';
  return t.replace(/<\/?([A-Za-z][\w.:-]*)\b[^>]*>/g,
                   (m, name) => RAW_OK.has(name.toLowerCase()) ? m : `<span class="rawtag">${esc(m)}</span>`);
} } });

// Markdown -> HTML; every image becomes a placeholder (the rubric judges from text, images are never loaded).
function render(md) {
  let html = marked.parse(md || '', { gfm: true, breaks: false });
  html = html.replace(/<img\b[^>]*>/gi, tag => {
    const alt = (tag.match(/\balt="([^"]*)"/i) || [, ''])[1];
    return `<span class="img-ph">[image${alt && alt !== 'enter image description here' ? ': ' + alt : ''}]</span>`;
  });
  return DOMPurify.sanitize(html, { FORBID_TAGS: ['img', 'style', 'iframe', 'form', 'input', 'video', 'audio', 'object', 'embed'],
                                   FORBID_ATTR: ['style'] });
}

function show() {
  const q = D.questions[cur];
  document.getElementById('meta').textContent = `Question ${cur + 1} of ${D.questions.length} · ${q.year} · id ${q.id}`;
  document.getElementById('title').textContent = q.title;
  const tags = document.getElementById('tags'); tags.innerHTML = '';
  q.tags.forEach(t => { const s = document.createElement('span'); s.className = 'tag'; s.textContent = t; tags.appendChild(s); });
  document.getElementById('body').innerHTML = render(q.body);
  document.querySelectorAll('#body a').forEach(a => { a.target = '_blank'; a.rel = 'noopener noreferrer'; });
  document.getElementById('note').value = (state[q.id] || {}).note || '';
  activeLabel = R ? Math.max(0, D.labels.findIndex(l => isSplit(q, l))) : 0;
  drawLabels(); drawDots(); window.scrollTo(0, 0);
}

function whyLine(who, level, reason) {
  const d = document.createElement('div');
  const b = document.createElement('b'); b.textContent = `${who} → ${level.replace(/_/g, ' ')}: `;
  d.append(b, document.createTextNode(reason || '(no reason)'));
  return d;
}

function drawLabels() {
  const q = D.questions[cur], e = state[q.id] || {};
  const panel = document.getElementById('labelPanel'); panel.innerHTML = '';
  D.labels.forEach((l, i) => {
    const split = R && isSplit(q, l);
    const box = document.createElement('div');
    box.className = 'label' + (i === activeLabel ? ' active' : '') + (R ? (split ? ' split' : ' agree') : '');
    box.onclick = () => { activeLabel = i; drawLabels(); };
    const name = document.createElement('div'); name.className = 'name'; name.textContent = `${i + 1}. ${l.title}`;
    if (R) {
      const st = document.createElement('span'); st.className = 'state';
      st.textContent = split ? (e[l.key] ? 'tie broken' : 'tie-break') : (e[l.key] === votes(q, l)[0][0] ? 'both agree' : 'changed');
      name.appendChild(st);
    }
    const levels = document.createElement('div'); levels.className = 'levels';
    l.levels.forEach((lv, j) => {
      const b = document.createElement('button'); b.textContent = `${j + 1} ${lv.replace(/_/g, ' ')}`;
      if (R) votes(q, l).forEach(([v], k) => {
        if (v === lv) { const m = document.createElement('span'); m.className = 'mk'; m.textContent = R.models[k].short; b.appendChild(m); }
      });
      if (e[l.key] === lv) b.className = 'on';
      b.onclick = ev => { ev.stopPropagation(); pick(i, j); };
      levels.appendChild(b);
    });
    box.append(name, levels);
    if (R) {
      const why = document.createElement('div'); why.className = 'why';
      votes(q, l).forEach(([v, r], k) => why.appendChild(whyLine(R.models[k].short, v, r)));
      if (split) box.appendChild(why);
      else { const d = document.createElement('details'); d.innerHTML = '<summary>why</summary>'; d.appendChild(why); box.appendChild(d); }
    }
    const det = document.createElement('details'); det.innerHTML = '<summary>rule</summary>';
    const rule = document.createElement('div'); rule.className = 'rule'; rule.innerHTML = render(l.section);
    det.appendChild(rule);
    box.append(det); panel.appendChild(box);
  });
  const done = D.questions.filter(isDone).length;
  let text = `${done} / ${D.questions.length} ${R ? 'confirmed' : 'complete'}`;
  if (R) {
    const open = D.questions.reduce((n, x) => n + D.labels.filter(l => isSplit(x, l) && !(state[x.id] || {})[l.key]).length, 0);
    text += ` · ${open} tie-break${open === 1 ? '' : 's'} left`;
  }
  document.getElementById('progress').textContent = text;
}

function drawDots() {
  const dots = document.getElementById('dots'); dots.innerHTML = '';
  D.questions.forEach((q, i) => {
    const s = document.createElement('span');
    s.className = (isDone(q) ? 'done' : isPart(q) ? 'part' : '') + (hasTie(q) ? ' tie' : '') + (i === cur ? ' cur' : '');
    s.title = `Question ${i + 1}${hasTie(q) ? ' (has a tie-break)' : ''}`; s.onclick = () => { cur = i; show(); };
    dots.appendChild(s);
  });
}

function pick(i, j) {
  const q = D.questions[cur], l = D.labels[i];
  if (j >= l.levels.length) return;
  const e = entry(q); e[l.key] = l.levels[j]; e.at = new Date().toISOString();
  persist();
  if (R) {  // next open tie-break on this question, else stay
    const nxt = D.labels.findIndex((x, k) => k > i && isSplit(q, x) && !e[x.key]);
    activeLabel = nxt >= 0 ? nxt : i;
  } else activeLabel = Math.min(i + 1, D.labels.length - 1);
  drawLabels(); drawDots();
}

function confirmQuestion() {
  const q = D.questions[cur], e = entry(q);
  const missing = D.labels.findIndex(l => !e[l.key]);
  if (missing >= 0) { activeLabel = missing; drawLabels(); return; }  // highlights the label still to pick
  e.confirmed = true; e.at = new Date().toISOString(); persist();
  for (let k = 1; k <= D.questions.length; k++) {
    const i = (cur + k) % D.questions.length;
    if (!isDone(D.questions[i])) { cur = i; show(); return; }
  }
  drawLabels(); drawDots();
}

function go(step) { cur = Math.max(0, Math.min(D.questions.length - 1, cur + step)); show(); }

document.getElementById('note').addEventListener('input', ev => {
  const e = entry(D.questions[cur]); e.note = ev.target.value; persist();
});
document.getElementById('prev').onclick = () => go(-1);
document.getElementById('next').onclick = () => go(1);
document.getElementById('nextOpen').onclick = () => {
  for (let k = 1; k <= D.questions.length; k++) {
    const i = (cur + k) % D.questions.length;
    if (!isDone(D.questions[i])) { cur = i; show(); return; }
  }
};
document.getElementById('toggleRubric').onclick = () => document.getElementById('rubric').classList.toggle('open');
document.addEventListener('keydown', ev => {
  if (ev.target.tagName === 'TEXTAREA' || ev.ctrlKey || ev.metaKey || ev.altKey) return;
  if (/^[1-9]$/.test(ev.key)) { pick(activeLabel, Number(ev.key) - 1); ev.preventDefault(); }
  else if (ev.key === 'ArrowDown') { activeLabel = Math.min(activeLabel + 1, D.labels.length - 1); drawLabels(); ev.preventDefault(); }
  else if (ev.key === 'ArrowUp') { activeLabel = Math.max(activeLabel - 1, 0); drawLabels(); ev.preventDefault(); }
  else if (ev.key === 'ArrowRight') { go(1); ev.preventDefault(); }
  else if (ev.key === 'ArrowLeft') { go(-1); ev.preventDefault(); }
  else if (ev.key === 'Enter' && R) { confirmQuestion(); ev.preventDefault(); }
  else if (ev.key === 'Escape') { document.getElementById('rubric').classList.remove('open'); }
});

// How the final level relates to the two models' levels (review only).
function decision(q, l, final) {
  const [[a], [b]] = votes(q, l);
  if (!final) return '';
  if (a === b) return final === a ? 'agreed' : 'overrode';
  return final === a ? `picked_${R.models[0].short}` : final === b ? `picked_${R.models[1].short}` : 'other';
}

function csv() {
  const cell = v => { v = v == null ? '' : String(v); return /[",\n\r]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
  const head = ['question_id', 'gold_set', 'gold_rank', 'labeler', 'rubric_version', ...D.labels.map(l => l.key),
                ...(R ? D.labels.map(l => `${l.key}__decision`) : []), 'note', 'labeled_at_utc'];
  const rows = D.questions.map(q => {
    const e = state[q.id] || {}, ok = !R || !!e.confirmed;  // an unconfirmed review row is saved empty
    return [q.id, D.set, q.rank, R ? 'human_review' : 'human', D.rubric_version,
            ...D.labels.map(l => ok ? e[l.key] || '' : ''),
            ...(R ? D.labels.map(l => ok ? decision(q, l, e[l.key]) : '') : []), e.note || '', ok ? e.at || '' : ''];
  });
  return [head, ...rows].map(r => r.map(cell).join(',')).join('\n') + '\n';
}
document.getElementById('confirm').onclick = confirmQuestion;
if (R) { document.getElementById('confirm').hidden = false; document.getElementById('reviewKeys').hidden = false; }
document.getElementById('save').onclick = async () => {
  const name = `gold_labels_${D.set}${R ? '_reviewed' : ''}.csv`, text = csv();
  if (window.showSaveFilePicker) {
    try {
      const h = await showSaveFilePicker({ suggestedName: name, types: [{ description: 'CSV', accept: { 'text/csv': ['.csv'] } }] });
      const w = await h.createWritable(); await w.write(text); await w.close(); return;
    } catch (e) { if (e.name === 'AbortError') return; }
  }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], { type: 'text/csv' })); a.download = name; a.click();
};

document.getElementById('setname').textContent = `${D.set} set${R ? ` · review of ${R.models.map(m => m.short).join(' + ')}` : ''}`;
persist();
document.getElementById('version').textContent = D.rubric_version;
document.getElementById('rubric').innerHTML = render(D.rubric_text);
show();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
