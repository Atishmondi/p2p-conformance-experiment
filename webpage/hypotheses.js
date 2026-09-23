'use strict';

/**
 * Hypotheses table controller (vanilla JS).
 *
 * Fetches `data.json` key "hypotheses" (array of
 * { hypo_id, rule, track, predicted_signature, lab_rate, field_rate, status })
 * and renders rows into table#hypoTable. Missing key / missing table
 * degrades to an explicit empty state instead of throwing.
 *
 * Render pattern mirrors app.js: safeObject/safeArray guards, textContent
 * only (no innerHTML), guarded getElementById.
 */

document.addEventListener('DOMContentLoaded', () => {
  initHypotheses();
});

/* ------------------------------------------------------------------ */
/* Generic guards (same pattern as app.js)                             */
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

/* ------------------------------------------------------------------ */
/* Hypotheses-specific helpers                                         */
/* ------------------------------------------------------------------ */

/**
 * Fetch data.json "hypotheses" array. Never throws; returns [] when the
 * key is missing, not an array, or the fetch fails.
 * @returns {Promise<Array>}
 */
async function fetchHypotheses() {
  try {
    const res = await fetch('data.json');
    if (!res || !res.ok) {
      return [];
    }
    const data = await res.json();
    return safeArray(safeObject(data).hypotheses);
  } catch (err) {
    return [];
  }
}

/**
 * Map a status string to a reused badge class.
 * supported -> .badge-ok; refuted/violated/rejected -> .badge-violation;
 * everything else (nuanced, open, ...) -> .badge-warn.
 * @param {*} status
 * @returns {string}
 */
function statusBadgeClass(status) {
  const s = safeString(status, '').toLowerCase();
  if (s === 'supported' || s === 'confirmed' || s === 'ok' || s === 'pass') {
    return 'badge-ok';
  }
  if (s === 'refuted' || s === 'rejected' || s === 'violated' || s === 'violation' || s === 'fail' || s === 'failed') {
    return 'badge-violation';
  }
  return 'badge-warn';
}

/**
 * Format a lab/field rate cell: missing (undefined/null/""/"NA"/"n/a")
 * renders as placeholder; otherwise the string form.
 * @param {*} v
 * @returns {string}
 */
function formatRateCell(v) {
  if (v === undefined || v === null) return '—';
  if (typeof v === 'number') {
    return Number.isFinite(v) ? String(v) : '—';
  }
  if (typeof v === 'string') {
    const t = v.trim();
    if (t === '' || t.toUpperCase() === 'NA' || t.toUpperCase() === 'N/A') return '—';
    return t;
  }
  return safeString(v, '—');
}

/**
 * Render hypotheses rows into table#hypoTable.
 * Columns: hypo | rule | lab | field | status (status as badge span).
 * Guards missing table/rows/keys with an explicit empty state; never throws.
 * @param {Array} hypotheses
 */
function renderHypoTable(hypotheses) {
  const table = el('hypoTable');
  if (!table) return;
  const tbody = ensureTbody(table);
  if (!tbody) return;
  clearElement(tbody);
  const rows = safeArray(hypotheses);
  if (rows.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.setAttribute('colspan', '5');
    td.textContent = 'No hypotheses available.';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }
  rows.forEach((row) => {
    const r = safeObject(row);
    const tr = document.createElement('tr');

    const hypoTd = document.createElement('td');
    hypoTd.textContent = safeString(r.hypo_id, '');
    tr.appendChild(hypoTd);

    const ruleTd = document.createElement('td');
    ruleTd.textContent = safeString(r.rule, '');
    tr.appendChild(ruleTd);

    const labTd = document.createElement('td');
    labTd.textContent = formatRateCell(r.lab_rate);
    tr.appendChild(labTd);

    const fieldTd = document.createElement('td');
    fieldTd.textContent = formatRateCell(r.field_rate);
    tr.appendChild(fieldTd);

    const statusTd = document.createElement('td');
    const badge = document.createElement('span');
    badge.className = statusBadgeClass(r.status);
    badge.textContent = safeString(r.status, '—');
    statusTd.appendChild(badge);
    tr.appendChild(statusTd);

    tbody.appendChild(tr);
  });
}

/**
 * Entry point: fetch hypotheses and render once.
 * @returns {Promise<void>}
 */
async function initHypotheses() {
  const hypotheses = await fetchHypotheses();
  renderHypoTable(hypotheses);
}
