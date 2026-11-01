/* Live SQL panels. DuckDB-WASM runs in the browser over the CSV files in presentation/data/ (snapshots of the dbt
   marts). Each .sql-panel has an editable query, Run and Reset; the result is drawn as a table with bars (data-render
   "table") or as one big number (data-render "number", written into the element marked data-bound).
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
  // one table per mart, same name as in dbt; the first line of each file is the attribution comment, so skip it
  for (const name of new Set(panels.map((p) => p.dataset.table))) {
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
    else drawTable(panel, out, columns, rows);
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

const fmt = (v) => (typeof v === "number" ? (Number.isInteger(v) ? v.toLocaleString("en-US") : String(v)) : String(v));

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

/* Table with a bar per row. Columns: first = label, last = the bar's value, the one before it (if any) = a plain figure.
   When the query is re-run, rows that were already on screen slide from their old place to the new one (FLIP). */
function drawTable(panel, out, columns, rows) {
  const keyCol = 0, valCol = columns.length - 1, midCol = columns.length > 2 ? 1 : -1;
  const max = Math.max(...rows.map((r) => Number(r[valCol])), 0) || 1;
  const before = panel._pos || {};

  const table = el("div", "rtable");
  const head = el("div", "rhead");
  [ "#", columns[keyCol], midCol >= 0 ? columns[midCol] : "", columns[valCol] ].forEach((t) => head.append(el("span", "", t)));
  table.append(head);

  const rowEls = rows.map((r, i) => {
    const row = el("div", "rrow");
    row.dataset.key = String(r[keyCol]);
    const barCell = el("div", "bar-cell");
    const bar = el("div", "bar");
    bar.style.width = `${(Number(r[valCol]) / max) * 100}%`;
    barCell.append(bar, el("span", "", fmt(r[valCol])));
    row.append(el("span", "rk", String(i + 1)), el("span", "", String(r[keyCol])),
               el("span", "", midCol >= 0 ? fmt(r[midCol]) : ""), barCell);
    table.append(row);
    return row;
  });
  out.replaceChildren(table);

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

/* ---------- wire up ---------- */
try {
  const conn = await startEngine();
  setStatus("ready", "ready");
  panels.forEach((panel) => {
    const editor = panel.querySelector(".sql-editor");
    panel.querySelector(".run").addEventListener("click", () => run(conn, panel));
    panel.querySelector(".reset").addEventListener("click", () => { editor.value = editor.defaultValue; run(conn, panel); });
    editor.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); run(conn, panel); } });
    run(conn, panel);
  });
  document.querySelectorAll(".step").forEach((btn) => {
    const panel = panels.find((p) => p.dataset.bind === btn.dataset.for);
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
