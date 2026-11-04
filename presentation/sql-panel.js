/* Live SQL panels. DuckDB-WASM runs in the browser over the CSV files in presentation/data/ (snapshots of the dbt
   marts). Each .sql-panel has an editable query, Run and Reset; the result is drawn as a table with bars (data-render
   "table"), as dots with interval lines (data-render "range") or as one big number (data-render "number", written into
   the element marked data-bound). A panel may carry query chips (.qchip): each loads its <template>'s query, chart
   and note into the panel; the query stays editable and Reset goes back to the pressed chip's query.
   The library comes from jsDelivr at an exact version; nothing here talks to BigQuery. */
import * as duckdb from "https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.29.0/+esm";

const panels = Array.from(document.querySelectorAll("[data-panel]"));
const hasGsap = () => window.gsap && !(window.presentation && window.presentation.reduced);

function setStatus(text, state) {
  panels.forEach((p) => {
    const s = p.querySelector(".sql-status");
    s.textContent = text;
    s.dataset.state = state;
  });
}

/* ---------- engine ---------- */
async function startEngine() {
  const bundle = await duckdb.selectBundle(duckdb.getJsDelivrBundles());
  // a worker has to come from the same origin, so wrap the CDN worker script in a tiny blob that imports it
  const workerUrl = URL.createObjectURL(new Blob([`importScripts("${bundle.mainWorker}");`], { type: "text/javascript" }));
  const db = new duckdb.AsyncDuckDB(new duckdb.ConsoleLogger(duckdb.LogLevel.WARNING), new Worker(workerUrl));
  await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
  URL.revokeObjectURL(workerUrl);

  const conn = await db.connect();
  // one table per mart, same name as in dbt (a panel may list several); the first line of each file is the
  // attribution comment, so skip it
  for (const name of new Set(panels.flatMap((p) => p.dataset.table.split(" ")))) {
    const text = await (await fetch(`data/${name}.csv`)).text();
    await db.registerFileText(`${name}.csv`, text);
    await conn.query(`CREATE OR REPLACE TABLE ${name} AS SELECT * FROM read_csv('${name}.csv', skip=1, header=true)`);
  }
  return conn;
}

/* ---------- running and drawing ---------- */
const plain = (v) => (typeof v === "bigint" ? Number(v) : v);

async function run(conn, panel) {
  const out = panel.querySelector(".sql-out");
  const meta = panel.querySelector(".meta");
  const sql = panel.querySelector(".sql-editor").value;
  const t0 = performance.now();
  try {
    const result = await conn.query(sql);
    const columns = result.schema.fields.map((f) => f.name);
    const rows = result.toArray().map((r) => columns.map((c) => plain(r[c])));
    meta.textContent = `${rows.length} row${rows.length === 1 ? "" : "s"} · ${Math.round(performance.now() - t0)} ms`;
    if (panel.dataset.render === "number") drawNumber(panel, out, columns, rows);
    else if (panel.dataset.render === "range") drawRange(panel, out, columns, rows);
    else drawTable(panel, out, columns, rows);
    const note = panel.querySelector(".sql-note");
    if (note) note.textContent = panel.dataset.note || "";
    syncSteps(panel, sql);
  } catch (err) {
    meta.textContent = "";
    out.replaceChildren(el("div", "sql-error", String(err.message || err)));
  }
}

/* Year step buttons (data-year, data-for="<panel's data-bind>"): the pressed one is the year the query filters on. */
const YEAR = /creation_year\s*=\s*(\d{4})/;
function syncSteps(panel, sql) {
  if (!panel.dataset.bind) return;
  const year = (sql.match(YEAR) || [])[1];
  document.querySelectorAll(`.step[data-for="${panel.dataset.bind}"]`)
    .forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.year === year)));
}

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

const fmt = (v) => (v == null ? "–" : typeof v === "number" ? (Number.isInteger(v) ? v.toLocaleString("en-US") : String(v)) : String(v));

function drawNumber(panel, out, columns, rows) {
  const target = document.querySelector(`[data-bound="${panel.dataset.bind}"]`) || out;
  const label = document.querySelector(`[data-bound-label="${panel.dataset.bind}"]`);
  out.replaceChildren();
  if (!rows.length) { target.textContent = "no rows"; return; }
  const value = rows[0][0];
  if (label) label.textContent = columns[0].replace(/_/g, " ");
  const decimals = typeof value === "number" && !Number.isInteger(value) ? String(value).split(".")[1].length : 0;
  if (typeof value === "number") window.presentation.countUp(target, value, decimals);
  else target.textContent = String(value);
}

/* A column named "list" splits the result into side-by-side blocks, one per value, in the order they first appear
   (e.g. the ten highest and the ten lowest); every other column keeps its role. */
function splitByList(columns, rows) {
  const at = columns.indexOf("list");
  if (at < 0) return { columns, groups: [{ name: "", rows }] };
  const groups = [];
  rows.forEach((r) => {
    const name = String(r[at]);
    let g = groups.find((x) => x.name === name);
    if (!g) groups.push((g = { name, rows: [] }));
    g.rows.push(r.filter((_, k) => k !== at));
  });
  return { columns: columns.filter((_, k) => k !== at), groups };
}

function blocks(groups, stacked) {
  const wrap = el("div", groups.length > 1 ? "rgroups" + (stacked ? " stacked" : "") : "");
  return { wrap, add: (g, body) => {
    const block = el("div", "rblock");
    if (g.name) block.append(el("p", "rblock-t", g.name));
    block.append(body);
    wrap.append(block);
  } };
}

/* Table with a bar per row. Columns: first = label, last = the bar's value, the one before it (if any) = a plain figure.
   When the query is re-run, rows that were already on screen slide from their old place to the new one (FLIP). */
function drawTable(panel, out, allColumns, allRows) {
  const { columns, groups } = splitByList(allColumns, allRows);
  const keyCol = 0, valCol = columns.length - 1, midCol = columns.length > 2 ? 1 : -1;
  const max = Math.max(...groups.flatMap((g) => g.rows.map((r) => Number(r[valCol]))), 0) || 1;
  const before = panel._pos || {};
  const { wrap, add } = blocks(groups);
  const rowEls = [];

  groups.forEach((g) => {
    const table = el("div", "rtable" + (midCol < 0 ? " two" : ""));
    const head = el("div", "rhead");
    [ "#", columns[keyCol], midCol >= 0 ? columns[midCol] : "", columns[valCol] ].forEach((t) => head.append(el("span", "", t)));
    table.append(head);
    g.rows.forEach((r, i) => {
      const row = el("div", "rrow");
      row.dataset.key = String(r[keyCol]);
      const barCell = el("div", "bar-cell");
      const bar = el("div", "bar");
      bar.style.width = `${(Number(r[valCol]) / max) * 100 || 0}%`; // a null value (no row that year) draws no bar
      barCell.append(bar, el("span", "", fmt(r[valCol])));
      row.append(el("span", "rk", String(i + 1)), el("span", "", String(r[keyCol])),
                 el("span", "", midCol >= 0 ? fmt(r[midCol]) : ""), barCell);
      table.append(row);
      rowEls.push(row);
    });
    add(g, table);
  });
  out.replaceChildren(wrap);

  const after = {};
  rowEls.forEach((row) => { after[row.dataset.key] = row.offsetTop; });
  panel._pos = after;

  if (!hasGsap()) return;
  rowEls.forEach((row) => {
    const key = row.dataset.key;
    const bar = row.querySelector(".bar");
    if (key in before) gsap.fromTo(row, { y: before[key] - after[key] }, { y: 0, duration: 0.7, ease: "power3.out" });
    else gsap.fromTo(row, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" });
    gsap.fromTo(bar, { scaleX: 0 }, { scaleX: 1, duration: 0.7, ease: "power3.out" });
  });
}

/* Dots with interval lines. Columns: first = label; "low" and "high" = the interval; the first other column = the dot.
   Rates (data-scale "pct") run on a 0-100% axis, anything else from 0 to just above the largest value. A
   data-baseline value draws a dashed line down every row (e.g. the accepted rate of all questions). */
function drawRange(panel, out, allColumns, allRows) {
  const { columns, groups } = splitByList(allColumns, allRows);
  const lo = columns.indexOf("low"), hi = columns.indexOf("high");
  const val = columns.findIndex((c, k) => k > 0 && k !== lo && k !== hi);
  const pct = panel.dataset.scale === "pct";
  const top = pct ? 1 : Math.max(...groups.flatMap((g) => g.rows.map((r) => Number(r[hi >= 0 ? hi : val]) || 0)), 0) * 1.1 || 1;
  const x = (v) => `${Math.max(0, Math.min(1, Number(v) / top)) * 100}%`;
  const show = (v) => (v === null || v === undefined ? "–" : pct ? `${(Number(v) * 100).toFixed(1)}%` : Number(v).toFixed(2));
  const base = panel.dataset.baseline;
  const { wrap, add } = blocks(groups, true);
  const marks = [];

  groups.forEach((g) => {
    const list = el("div", "rg");
    g.rows.forEach((r) => {
      const row = el("div", "rg-row");
      const label = el("span", "rg-label", String(r[0]));
      label.title = String(r[0]);
      const track = el("div", "rg-track");
      if (base) track.style.setProperty("--b", x(base));
      if (r[val] !== null && r[val] !== undefined) {
        if (lo >= 0 && hi >= 0) {
          const line = el("span", "rg-line");
          line.style.left = x(r[lo]);
          line.style.width = `calc(${x(r[hi])} - ${x(r[lo])})`;
          track.append(line);
          marks.push(line);
        }
        const dot = el("span", "rg-dot");
        dot.style.left = x(r[val]);
        track.append(dot);
        marks.push(dot);
      }
      row.append(label, el("span", "rg-v", show(r[val])), track);
      list.append(row);
    });
    add(g, list);
  });
  out.replaceChildren(wrap);
  if (hasGsap()) gsap.fromTo(marks, { opacity: 0 }, { opacity: 1, duration: 0.5, ease: "power2.out", stagger: 0.01 });
}

/* ---------- wire up ---------- */
try {
  const conn = await startEngine();
  setStatus("ready", "ready");
  panels.forEach((panel) => {
    const editor = panel.querySelector(".sql-editor");
    // the panel's own settings belong to the chip without a template (the default query in the textarea)
    const own = { render: panel.dataset.render, baseline: panel.dataset.baseline, scale: panel.dataset.scale, note: panel.dataset.note };
    let current = () => editor.defaultValue;
    const chips = panel.querySelectorAll(".qchip");
    chips.forEach((chip) => {
      chip.addEventListener("click", () => {
        const tpl = chip.dataset.q ? document.getElementById(chip.dataset.q) : null;
        const set = tpl ? { render: tpl.dataset.render, baseline: tpl.dataset.baseline, scale: tpl.dataset.scale, note: tpl.dataset.note } : own;
        Object.entries(set).forEach(([k, v]) => { if (v === undefined) delete panel.dataset[k]; else panel.dataset[k] = v; });
        current = () => (tpl ? tpl.content.textContent : editor.defaultValue);
        editor.value = current();
        chips.forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
        panel._pos = {}; // a different query: its rows fade in instead of sliding from the last query's places
        run(conn, panel);
      });
    });
    panel.querySelector(".run").addEventListener("click", () => run(conn, panel));
    panel.querySelector(".reset").addEventListener("click", () => { editor.value = current(); run(conn, panel); });
    editor.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); run(conn, panel); } });
    run(conn, panel);
  });
  // an "SQL" button beside a follow-up question presses the panel chip with the same query
  document.querySelectorAll(".sql-ref[data-q]").forEach((btn) => {
    const chip = document.querySelector(`.qchip[data-q="${btn.dataset.q}"]`);
    if (!chip) return;
    btn.addEventListener("click", () => {
      chip.click();
      if (window.matchMedia("(max-width: 900px)").matches) chip.closest(".sql-panel").scrollIntoView({ block: "start" });
    });
  });
  // only year buttons bound to a panel: chapter 4's buttons also carry .step but have no data-for / data-year
  document.querySelectorAll(".step[data-for]").forEach((btn) => {
    const panel = panels.find((p) => p.dataset.bind === btn.dataset.for);
    if (!panel) return;
    btn.addEventListener("click", () => {
      const editor = panel.querySelector(".sql-editor");
      editor.value = editor.value.replace(YEAR, `creation_year = ${btn.dataset.year}`);
      run(conn, panel);
    });
  });
} catch (err) {
  console.error(err);
  setStatus("engine unavailable (offline?)", "error");
}
