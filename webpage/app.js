'use strict';

/**
 * P2P Conformance Experiment — showcase dashboard.
 *
 * Masters-level vanilla JS controller. All rendering is driven by
 * `fetch('data.json')` and every data / DOM access is guarded so a
 * missing key or a missing element degrades to an explicit empty state
 * instead of throwing.
 *
 * Expected (all keys optional) data.json shape:
 * {
 *   "meta": {},
 *   "r1": { "cases", "events", "conformance_rate",
 *            "variants": [{ "label", "count" }],
 *            "violations": { "R1".."R5" },
 *            "performance": [{ "scenario", "mean_cycle", "median_cycle" }] },
 *   "r2": { ...same as r1... },
 *   "stats": { "p_value", "chi2", "cohens_h" },
 *   "pm4py": { "fitness", "precision", "variants_mined",
 *              "alignments_sample": [{ "case_id", "fitness", "deviations" }] },
 *   "robustness": [{ "noise_level", "recall", "fpr" }],
 *   "log_sample": [{ "case_id", "scenario", "variant", "violations", "cycle" }]
 * }
 */

document.addEventListener('DOMContentLoaded', () => {
  init();
});

/** Parsed data.json payload (object, never null after init attempt). */
let appData = null;

/** Currently selected round key: 'r1' | 'r2'. */
let currentRound = 'r1';

/** Live Chart.js instances keyed by logical name. */
const charts = {
  variant: null,
  viol: null,
  perf: null,
  robust: null,
  trend: null
};

const VIOLATION_RULES = ['R1', 'R2', 'R3', 'R4', 'R5'];

/* ------------------------------------------------------------------ */
/* Generic guards                                                      */
/* ------------------------------------------------------------------ */

/**
 * Return value if it is a plain object, else {}.
 * @param {*} v
 * @returns {Object}
 */
function safeObject(v) {
  return v !== null && typeof v === 'object' && !Array.isArray(v) ? v : {};
}

/**
 * Return value if it is an array, else [].
 * @param {*} v
 * @returns {Array}
 */
function safeArray(v) {
  return Array.isArray(v) ? v : [];
}

/**
 * Coerce to finite number or return fallback.
 * @param {*} v
 * @param {number|null} fallback
 * @returns {number|null}
 */
function safeNumber(v, fallback) {
  const n = typeof v === 'string' && v.trim() !== '' ? Number(v) : v;
  return typeof n === 'number' && Number.isFinite(n) ? n : fallback;
}

/**
 * Coerce to trimmed non-empty string or return fallback.
 * @param {*} v
 * @param {string} fallback
 * @returns {string}
 */
function safeString(v, fallback) {
  if (typeof v === 'string') {
    const t = v.trim();
    return t !== '' ? t : fallback;
  }
  if (typeof v === 'number' && Number.isFinite(v)) return String(v);
  return fallback;
}

/**
 * Format a number with fixed fraction digits or return placeholder.
 * @param {*} v
 * @param {number} digits
 * @param {string} placeholder
 * @returns {string}
 */
function fmtNum(v, digits, placeholder) {
  const n = safeNumber(v, null);
  if (n === null) return placeholder;
  return n.toFixed(digits);
}

/**
 * Format a 0..1 rate as percent string or placeholder.
 * @param {*} v
 * @param {string} placeholder
 * @returns {string}
 */
function fmtRate(v, placeholder) {
  const n = safeNumber(v, null);
  if (n === null) return placeholder;
  return (n * 100).toFixed(1) + '%';
}

/**
 * Shorthand guarded getElementById.
 * @param {string} id
 * @returns {HTMLElement|null}
 */
function el(id) {
  if (typeof document === 'undefined' || !document.getElementById) return null;
  return document.getElementById(id) || null;
}

/**
 * Remove all child nodes of an element.
 * @param {HTMLElement} node
 */
function clearElement(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

/**
 * Build an element with text content (XSS-safe: no innerHTML).
 * @param {string} tag
 * @param {string} text
 * @returns {HTMLElement}
 */
function textEl(tag, text) {
  const node = document.createElement(tag);
  node.textContent = text;
  return node;
}

/* ------------------------------------------------------------------ */
/* Data loading + round selection                                      */
/* ------------------------------------------------------------------ */

/**
 * Fetch data.json. Never throws; returns object or null on failure.
 * @returns {Promise<Object|null>}
 */
async function fetchData() {
  try {
    const res = await fetch('data.json');
    if (!res || !res.ok) {
      const status = res ? res.status + ' ' + (res.statusText || '') : 'no response';
      console.error('Failed to fetch data.json: HTTP ' + status);
      return null;
    }
    const data = await res.json();
    return safeObject(data);
  } catch (err) {
    console.error('Failed to fetch data.json: ' + (err && err.message ? err.message : String(err)));
    return null;
  }
}

/**
 * Read the selected round from #roundToggle.
 * Supports <select>, checkbox (r1/r2), or radio group input[name="round"].
 * @returns {string} 'r1' or 'r2' (falls back to currentRound)
 */
function getSelectedRound() {
  const toggle = el('roundToggle');
  if (!toggle) {
    const checked = typeof document !== 'undefined' && document.querySelector
      ? document.querySelector('input[name="round"]:checked')
      : null;
    if (checked && (checked.value === 'r1' || checked.value === 'r2')) return checked.value;
    return currentRound;
  }
  const tag = (toggle.tagName || '').toUpperCase();
  if (tag === 'SELECT') {
    return toggle.value === 'r2' ? 'r2' : 'r1';
  }
  if (toggle.type === 'checkbox') {
    return toggle.checked ? 'r2' : 'r1';
  }
  if (toggle.type === 'radio') {
    const checked = document.querySelector('input[name="round"]:checked');
    if (checked && (checked.value === 'r1' || checked.value === 'r2')) return checked.value;
    return toggle.value === 'r2' ? 'r2' : 'r1';
  }
  // Generic input / fallback + radio-group override.
  const checked = document.querySelector ? document.querySelector('input[name="round"]:checked') : null;
  if (checked && (checked.value === 'r1' || checked.value === 'r2')) return checked.value;
  if (toggle.value === 'r1' || toggle.value === 'r2') return toggle.value;
  return currentRound;
}

/**
 * Return guarded round payload for 'r1' | 'r2', or null.
 * @param {string} round
 * @returns {Object|null}
 */
function getRoundData(round) {
  if (!appData) return null;
  const payload = safeObject(appData[round]);
  return Object.keys(payload).length > 0 ? payload : null;
}

/* ------------------------------------------------------------------ */
/* Chart helpers                                                       */
/* ------------------------------------------------------------------ */

/**
 * Destroy a cached Chart.js instance.
 * @param {string} key one of variant|viol|perf|robust|trend
 */
function destroyChart(key) {
  const inst = charts[key];
  if (inst) {
    try {
      inst.destroy();
    } catch (e) {
      console.error('Failed to destroy chart ' + key + ': ' + (e && e.message ? e.message : e));
    }
    charts[key] = null;
  }
}

/**
 * Check Chart.js availability once per render call.
 * @returns {boolean}
 */
function chartLibAvailable() {
  if (typeof Chart === 'undefined') {
    console.error('Chart.js not loaded; skipping chart render.');
    return false;
  }
  return true;
}

/**
 * Doughnut of variant distribution for the active round.
 * Guards: missing canvas, missing variants, non-numeric counts.
 * @param {Object|null} roundData
 */
function renderVariantChart(roundData) {
  const canvas = el('variantChart');
  if (!canvas) return;
  destroyChart('variant');
  if (!chartLibAvailable()) return;
  const data = safeObject(roundData);
  const variants = safeArray(data.variants).filter(
    (v) => v !== null && typeof v === 'object'
  );
  const labels = variants.map((v, i) => safeString(v.label, 'Variant ' + (i + 1)));
  const counts = variants.map((v) => safeNumber(v.count, 0));
  charts.variant = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: labels.length > 0 ? labels : ['No variants'],
      datasets: [{ data: counts.length > 0 ? counts : [1] }]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom' } }
    }
  });
}

/**
 * Bar chart of violations R1..R5 for the active round.
 * Guards: missing canvas / violations object; defaults each rule to 0.
 * @param {Object|null} roundData
 */
function renderViolChart(roundData) {
  const canvas = el('violChart');
  if (!canvas) return;
  destroyChart('viol');
  if (!chartLibAvailable()) return;
  const data = safeObject(roundData);
  const violations = safeObject(data.violations);
  const counts = VIOLATION_RULES.map((k) => safeNumber(violations[k], 0));
  charts.viol = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: VIOLATION_RULES.slice(),
      datasets: [{ label: 'Violations', data: counts }]
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
    }
  });
}

/**
 * Bar chart of mean_cycle per scenario for the active round.
 * Guards: missing canvas / performance array; skips rows without scenario.
 * @param {Object|null} roundData
 */
function renderPerfChart(roundData) {
  const canvas = el('perfChart');
  if (!canvas) return;
  destroyChart('perf');
  if (!chartLibAvailable()) return;
  const data = safeObject(roundData);
  const perf = safeArray(data.performance).filter(
    (p) => p !== null && typeof p === 'object'
  );
  const labels = perf.map((p, i) => safeString(p.scenario, 'S' + (i + 1)));
  const values = perf.map((p) => safeNumber(p.mean_cycle, 0));
  charts.perf = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: labels.length > 0 ? labels : ['No data'],
      datasets: [{ label: 'Mean cycle time', data: values.length > 0 ? values : [0] }]
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true } }
    }
  });
}

/**
 * Line chart of recall vs noise_level (global robustness sweep).
 * Guards: missing canvas / robustness array; sorts by noise_level.
 * An fpr series is added only if at least one row carries a valid fpr.
 * @param {Array} robustness
 */
function renderRobustChart(robustness) {
  const canvas = el('robustChart');
  if (!canvas) return;
  destroyChart('robust');
  if (!chartLibAvailable()) return;
  const rows = safeArray(robustness)
    .filter((r) => r !== null && typeof r === 'object')
    .map((r) => ({
      noise: safeNumber(r.noise_level, null),
      recall: safeNumber(r.recall, null),
      fpr: safeNumber(r.fpr, null)
    }))
    .filter((r) => r.noise !== null)
    .sort((a, b) => a.noise - b.noise);
  if (rows.length === 0) return;
  const labels = rows.map((r) => String(r.noise));
  const recall = rows.map((r) => (r.recall === null ? null : r.recall));
  const datasets = [{ label: 'Recall', data: recall, fill: false, tension: 0.2 }];
  if (rows.some((r) => r.fpr !== null)) {
    datasets.push({
      label: 'FPR',
      data: rows.map((r) => r.fpr),
      fill: false,
      tension: 0.2
    });
  }
  charts.robust = new Chart(canvas, {
    type: 'line',
    data: { labels: labels, datasets: datasets },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true, max: 1 } }
    }
  });
}

/**
 * Line chart of violation rate over runs (global trend).
 * x = run_id, y = viol_rate; splits r1/r2 eras into separate series if present.
 * Guards: missing canvas, missing/empty runs array, non-numeric rates.
 * @param {Array} runs
 */
function renderTrendChart(runs) {
  const canvas = el('trendChart');
  if (!canvas) return;
  destroyChart('trend');
  if (!chartLibAvailable()) return;
  const rows = safeArray(runs)
    .filter((r) => r !== null && typeof r === 'object')
    .map((r) => ({
      run_id: safeString(r.run_id, ''),
      era: typeof r.era === 'string' ? r.era.trim().toLowerCase() : safeString(r.era, ''),
      viol_rate: safeNumber(r.viol_rate, null)
    }))
    .filter((r) => r.run_id !== '' && r.viol_rate !== null);
  if (rows.length === 0) return;
  const labels = rows.map((r) => r.run_id);
  const hasR1 = rows.some((r) => r.era === 'r1');
  const hasR2 = rows.some((r) => r.era === 'r2');
  let datasets;
  if (hasR1 || hasR2) {
    datasets = [];
    if (hasR1) {
      datasets.push({
        label: 'r1',
        data: rows.map((r) => (r.era === 'r1' ? r.viol_rate : null)),
        fill: false,
        tension: 0.2
      });
    }
    if (hasR2) {
      datasets.push({
        label: 'r2',
        data: rows.map((r) => (r.era === 'r2' ? r.viol_rate : null)),
        fill: false,
        tension: 0.2
      });
    }
    if (rows.some((r) => r.era !== 'r1' && r.era !== 'r2')) {
      datasets.push({
        label: 'other',
        data: rows.map((r) => (r.era !== 'r1' && r.era !== 'r2' ? r.viol_rate : null)),
        fill: false,
        tension: 0.2
      });
    }
  } else {
    datasets = [{ label: 'Violation rate', data: rows.map((r) => r.viol_rate), fill: false, tension: 0.2 }];
  }
  charts.trend = new Chart(canvas, {
    type: 'line',
    data: { labels: labels, datasets: datasets },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true, max: 1 } }
    }
  });
}

/* ------------------------------------------------------------------ */
/* KPI / stats / pm4py boxes                                           */
/* ------------------------------------------------------------------ */

/**
 * Render KPI cards into div#kpis for the active round.
 * Guards every key; missing values render as '—'.
 * @param {Object|null} roundData
 */
function updateKpis(roundData) {
  const box = el('kpis');
  if (!box) return;
  clearElement(box);
  const data = safeObject(roundData);
  const isEmpty = Object.keys(data).length === 0;
  if (isEmpty) {
    box.appendChild(textEl('p', 'No round data available.'));
    return;
  }
  const violations = safeObject(data.violations);
  const totalViol = VIOLATION_RULES.reduce(
    (acc, k) => acc + safeNumber(violations[k], 0),
    0
  );
  const perf = safeArray(data.performance);
  const meanCycles = perf
    .map((p) => (p !== null && typeof p === 'object' ? safeNumber(p.mean_cycle, null) : null))
    .filter((n) => n !== null);
  const avgCycle = meanCycles.length > 0
    ? meanCycles.reduce((a, b) => a + b, 0) / meanCycles.length
    : null;

  const cards = [
    { label: 'Cases', value: safeNumber(data.cases, null) === null ? '—' : String(safeNumber(data.cases, 0)) },
    { label: 'Events', value: safeNumber(data.events, null) === null ? '—' : String(safeNumber(data.events, 0)) },
    { label: 'Conformance rate', value: fmtRate(data.conformance_rate, '—') },
    { label: 'Violations (R1–R5)', value: String(totalViol) },
    { label: 'Mean cycle (days)', value: avgCycle === null ? '—' : avgCycle.toFixed(2) }
  ];
  cards.forEach((c) => {
    const card = document.createElement('div');
    card.appendChild(textEl('h3', c.label));
    const strong = document.createElement('strong');
    strong.textContent = c.value;
    card.appendChild(strong);
    box.appendChild(card);
  });
}

/**
 * Render inferential stats into div#statsBox (p / chi2 / h).
 * Guards every key; missing stats render an explicit empty state.
 * @param {Object|null|undefined} stats
 */
function renderStats(stats) {
  const box = el('statsBox');
  if (!box) return;
  clearElement(box);
  const s = safeObject(stats);
  const hasAny = s.p_value !== undefined || s.chi2 !== undefined || s.cohens_h !== undefined;
  if (!hasAny) {
    box.appendChild(textEl('p', 'No inferential statistics available.'));
    return;
  }
  const dl = document.createElement('dl');
  const rows = [
    ['p-value', fmtNum(s.p_value, 4, '—')],
    ['Chi²', fmtNum(s.chi2, 3, '—')],
    ["Cohen's h", fmtNum(s.cohens_h, 3, '—')]
  ];
  rows.forEach(([term, val]) => {
    dl.appendChild(textEl('dt', term));
    dl.appendChild(textEl('dd', val));
  });
  box.appendChild(dl);
}

/**
 * Render PM4Py discovery/conformance summary into div#pm4pyBox.
 * Guards fitness / precision / variants_mined; missing renders empty state.
 * @param {Object|null|undefined} pm4py
 */
function renderPm4py(pm4py) {
  const box = el('pm4pyBox');
  if (!box) return;
  clearElement(box);
  const p = safeObject(pm4py);
  const hasAny = p.fitness !== undefined || p.precision !== undefined || p.variants_mined !== undefined;
  if (!hasAny) {
    box.appendChild(textEl('p', 'No PM4Py results available.'));
    return;
  }
  const dl = document.createElement('dl');
  const rows = [
    ['Fitness', fmtNum(p.fitness, 3, '—')],
    ['Precision', fmtNum(p.precision, 3, '—')],
    [
      'Variants mined',
      safeNumber(p.variants_mined, null) === null ? '—' : String(safeNumber(p.variants_mined, 0))
    ]
  ];
  rows.forEach(([term, val]) => {
    dl.appendChild(textEl('dt', term));
    dl.appendChild(textEl('dd', val));
  });
  box.appendChild(dl);
}

/* ------------------------------------------------------------------ */
/* Tables                                                              */
/* ------------------------------------------------------------------ */

/**
 * Ensure a table has a tbody; create one if absent.
 * @param {HTMLTableElement} table
 * @returns {HTMLTableSectionElement|null}
 */
function ensureTbody(table) {
  let tbody = table.querySelector('tbody');
  if (!tbody) {
    tbody = document.createElement('tbody');
    table.appendChild(tbody);
  }
  return tbody;
}

/**
 * Normalise a deviations cell: array -> comma-joined, else stringified.
 * @param {*} v
 * @returns {string}
 */
function formatDeviations(v) {
  if (Array.isArray(v)) return v.map((d) => String(d)).join(', ');
  if (v === undefined || v === null) return '';
  return String(v);
}

/**
 * Render alignments_sample into table#alignTable.
 * Columns: case_id | fitness | deviations. Guards missing table/rows/keys.
 * @param {Array} alignments
 */
function renderAlignTable(alignments) {
  const table = el('alignTable');
  if (!table) return;
  const tbody = ensureTbody(table);
  if (!tbody) return;
  clearElement(tbody);
  const rows = safeArray(alignments);
  if (rows.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.setAttribute('colspan', '3');
    td.textContent = 'No alignments available.';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }
  rows.forEach((row) => {
    const r = safeObject(row);
    const tr = document.createElement('tr');
    const cells = [
      safeString(r.case_id, ''),
      r.fitness === undefined || r.fitness === null ? '' : fmtNum(r.fitness, 3, ''),
      formatDeviations(r.deviations)
    ];
    cells.forEach((c) => {
      const td = document.createElement('td');
      td.textContent = c;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

/**
 * Render log_sample into table#logTable.
 * Columns: case_id | scenario | variant | violations | cycle.
 * Guards missing table/rows/keys, then re-applies the active filter.
 * @param {Array} logSample
 */
function renderLogTable(logSample) {
  const table = el('logTable');
  if (!table) return;
  const tbody = ensureTbody(table);
  if (!tbody) return;
  clearElement(tbody);
  const rows = safeArray(logSample);
  if (rows.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.setAttribute('colspan', '5');
    td.textContent = 'No log records available.';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }
  rows.forEach((row) => {
    const r = safeObject(row);
    const tr = document.createElement('tr');
    const cells = [
      safeString(r.case_id, ''),
      safeString(r.scenario, ''),
      safeString(r.variant, ''),
      r.violations === undefined || r.violations === null ? '' : String(r.violations),
      r.cycle === undefined || r.cycle === null ? '' : String(r.cycle)
    ];
    cells.forEach((c) => {
      const td = document.createElement('td');
      td.textContent = c;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  // Keep newly rendered rows consistent with any active filter text.
  filterLogTable();
}

/**
 * Render runs history into table#runsTable.
 * Columns: run_id | era | cases | viol_rate | mean_cycle.
 * Guards missing table/rows/keys with an explicit empty state; never throws.
 * @param {Array} runs
 */
function renderRunsTable(runs) {
  const table = el('runsTable');
  if (!table) return;
  const tbody = ensureTbody(table);
  if (!tbody) return;
  clearElement(tbody);
  const rows = safeArray(runs);
  if (rows.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.setAttribute('colspan', '5');
    td.textContent = 'No runs available.';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }
  rows.forEach((row) => {
    const r = safeObject(row);
    const tr = document.createElement('tr');
    const cases = safeNumber(r.cases, null);
    const cells = [
      safeString(r.run_id, ''),
      safeString(r.era, ''),
      cases === null ? '' : String(cases),
      r.viol_rate === undefined || r.viol_rate === null ? '' : fmtRate(r.viol_rate, ''),
      r.mean_cycle === undefined || r.mean_cycle === null ? '' : fmtNum(r.mean_cycle, 2, '')
    ];
    cells.forEach((c) => {
      const td = document.createElement('td');
      td.textContent = c;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

/**
 * Substring filter for #logTable driven by #filterInput.
 * Case-insensitive match across the full row text; header rows skipped.
 * Guards missing input/table; empty query shows all rows.
 */
function filterLogTable() {
  const table = el('logTable');
  if (!table) return;
  const input = el('filterInput');
  const q = input && typeof input.value === 'string' ? input.value.trim().toLowerCase() : '';
  const tbody = table.querySelector('tbody');
  const rows = tbody ? tbody.querySelectorAll('tr') : table.querySelectorAll('tr');
  rows.forEach((tr) => {
    if (tr.querySelector('th')) return;
    const text = (tr.textContent || '').toLowerCase();
    tr.style.display = !q || text.includes(q) ? '' : 'none';
  });
}

/* ------------------------------------------------------------------ */
/* Orchestration                                                       */
/* ------------------------------------------------------------------ */

/**
 * Re-render everything derived from appData for the active round:
 * round-specific charts + KPIs, plus global stats / pm4py /
 * robustness / alignments / log sample (each guarded independently).
 */
function renderAll() {
  const roundData = getRoundData(currentRound);
  renderVariantChart(roundData);
  renderViolChart(roundData);
  renderPerfChart(roundData);
  updateKpis(roundData);

  const root = safeObject(appData);
  renderStats(root.stats);
  renderPm4py(root.pm4py);
  renderRobustChart(root.robustness);
  renderAlignTable(safeObject(root.pm4py).alignments_sample);
  renderLogTable(root.log_sample);
  renderTrendChart(root.runs);
  renderRunsTable(root.runs);
}

/**
 * Entry point: fetch data, pick initial round, render once, wire controls.
 * #roundToggle change re-renders charts + KPIs (via renderAll);
 * #filterInput input re-applies the substring filter.
 * @returns {Promise<void>}
 */
async function init() {
  const data = await fetchData();
  if (!data) {
    const kpis = el('kpis');
    if (kpis) {
      clearElement(kpis);
      kpis.appendChild(textEl('p', 'Failed to load data.json.'));
    }
    console.error('init aborted: data.json could not be loaded.');
    return;
  }
  appData = data;
  currentRound = getSelectedRound() || 'r1';
  if (!getRoundData(currentRound)) {
    if (getRoundData('r1')) currentRound = 'r1';
    else if (getRoundData('r2')) currentRound = 'r2';
  }

  renderAll();

  const toggle = el('roundToggle');
  if (toggle) {
    toggle.addEventListener('change', () => {
      currentRound = getSelectedRound();
      renderAll();
    });
  }
  if (typeof document !== 'undefined' && document.querySelectorAll) {
    const radios = document.querySelectorAll('input[name="round"]');
    if (radios && radios.forEach) {
      radios.forEach((r) => {
        r.addEventListener('change', () => {
          currentRound = getSelectedRound();
          renderAll();
        });
      });
    }
  }

  const filterInput = el('filterInput');
  if (filterInput) {
    filterInput.addEventListener('input', () => {
      filterLogTable();
    });
  }
}
