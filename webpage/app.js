'use strict';
const $ = id => document.getElementById(id);
const fmt = value => value == null ? 'Unavailable' : String(value);
const rate = value => value == null ? 'Unavailable' : (value * 100).toFixed(1) + '%';
const number = value => value == null ? 'Unavailable' : Number(value).toLocaleString();
let data;
const policy = {
  R1: 'Approval precedes each purchase order',
  R2: 'A receipt precedes each invoice',
  R3: 'Invoiced quantity does not exceed received quantity at invoice time',
  R4: 'A modification has a later approval before the next purchase order',
  R5: 'A payment follows an invoice'
};
function cell(row, value) { const td = row.insertCell(); td.textContent = fmt(value); return td; }
function clear(id) { $(id).replaceChildren(); }
function card(label, value, detail) {
  const el = document.createElement('div'); el.className = 'card';
  const p = document.createElement('p'); p.textContent = label;
  const strong = document.createElement('strong'); strong.textContent = value;
  const small = document.createElement('small'); small.textContent = detail;
  el.append(p, strong, small); $('cards').append(el);
}
function renderLab() {
  const era = $('round').value, cohort = data.lab.cohorts[era], overall = cohort.overall;
  $('lab-context').textContent = `${era.toUpperCase()} · checker ${fmt(cohort.rule_version)} · ${number(overall.cases)} cases total. Case-level evaluated = compliant + violating; ${number(overall.not_evaluable)} cases have no decisive case status.`;
  clear('cards');
  card('Case violations', `${number(overall.violating)} / ${number(overall.evaluated_cases)}`, `${rate(overall.violation_rate)} of evaluated cases`);
  card('Compliant cases', number(overall.compliant), 'Cases with all evaluated rules clean');
  card('Unknown case status', number(overall.not_evaluable), 'Excluded from case rate');
  card('Targeted strata', `${number(cohort.targeted.violating)} / ${number(cohort.targeted.evaluated_cases)}`, `${rate(cohort.targeted.violation_rate)} · ${number(cohort.targeted.cases)} cases`);
  clear('rules');
  Object.entries(overall.rules).forEach(([name, summary]) => {
    const tr = $('rules').insertRow();
    [name, policy[name] || 'Definition unavailable', number(summary.violating), number(summary.evaluated_cases), number(summary.not_evaluable), rate(summary.violation_rate)].forEach(v => cell(tr, v));
  });
  clear('scenarios');
  Object.entries(cohort.scenarios).forEach(([name, summary]) => {
    const duration = (data.lab.throughput[era] || {})[name];
    const tr = $('scenarios').insertRow();
    [name, number(summary.cases), `${number(summary.violating)} / ${number(summary.evaluated_cases)}`, number(summary.not_evaluable),
      duration && duration.mean_days != null ? duration.mean_days.toFixed(1) + ' d (n=' + duration.n + ')' : 'Unavailable'].forEach(v => cell(tr, v));
  });
  const compare = data.lab.targeted_comparison;
  $('comparison').textContent = compare.comparable && compare.absolute_rate_difference != null ?
    `Targeted descriptive difference (R1 minus R2): ${(compare.absolute_rate_difference * 100).toFixed(1)} percentage points. Designed cohorts; no causal or field transfer estimate.` :
    `Targeted round comparison unavailable: ${fmt(compare.interpretation)}`;
  const select = $('case-select'); select.replaceChildren();
  (data.examples[era] || []).forEach((example, i) => {
    const option = new Option(`${example.scenario} · ${example.case_id} · ${example.status}`, String(i)); select.add(option);
  });
  renderCase();
}
function renderCase() {
  const cases = data.examples[$('round').value] || [], chosen = cases[Number($('case-select').value) || 0];
  const container = $('case-detail'); container.replaceChildren();
  if (!chosen) { container.textContent = 'No example cases available.'; return; }
  const p = document.createElement('p');
  p.textContent = `${chosen.case_id} · ${chosen.status} · checker ${chosen.rule_version}. Violations: ${chosen.violations.join(', ') || 'none'}; unknown rules: ${chosen.unknown_rules.join(', ') || 'none'}.`;
  const scroll = document.createElement('div'); scroll.className = 'table-scroll';
  const table = document.createElement('table');
  const head = table.createTHead().insertRow();
  ['Activity', 'Timestamp', 'Received delta', 'Invoiced delta'].forEach(v => { const th = document.createElement('th'); th.textContent = v; head.append(th); });
  const body = table.createTBody();
  chosen.trace.forEach(event => {
    const tr = body.insertRow();
    [event.activity, event.timestamp, event.qty_received || '—', event.qty_invoiced || '—'].forEach(v => cell(tr, v));
  });
  scroll.append(table); container.append(p, scroll);
}
function renderField() {
  const field = data.field;
  $('field-context').textContent = field.available ?
    `Historical observational summary · ${field.rule_version}. Counts derive from the supplied summary; the raw XES was not rerun by this demo.` :
    `Unavailable: ${fmt(field.unavailable_reason)}`;
  const select = $('stratum'); select.replaceChildren();
  Object.keys(field.strata).forEach(name => select.add(new Option(name.replaceAll('_', ' '), name)));
  if (!field.available) { $('stratum-context').textContent = 'No field summary supplied.'; clear('field-rules'); select.disabled = true; return; }
  select.disabled = false; renderStratum();
}
function renderStratum() {
  const stratum = data.field.strata[$('stratum').value]; clear('field-rules');
  if (!stratum) return;
  $('stratum-context').textContent = `${stratum.available ? 'Available' : 'Unavailable'} · ${number(stratum.n_cases)} cases in this stratum. Each proxy has its own applicable count.`;
  Object.entries(stratum.metrics).forEach(([key, metric]) => {
    const tr = $('field-rules').insertRow();
    [key, `${number(metric.n_true)} / ${number(metric.n_applicable)}`, rate(metric.rate), data.field.definitions[key] || 'Definition unavailable'].forEach(v => cell(tr, v));
  });
  if (!Object.keys(stratum.metrics).length) $('stratum-context').textContent += ' No reported metrics.';
}
function renderSources() {
  clear('provenance');
  data.provenance.sources.forEach(source => {
    const tr = $('provenance').insertRow(); const td = tr.insertCell();
    const a = document.createElement('a'); a.textContent = source.path; a.href = source.download || '#'; td.append(a);
    if (source.transformation) {
      const note = document.createElement('small');
      note.textContent = ` Public copy: ${source.transformation} Input SHA-256: ${source.source_sha256}`;
      td.append(note);
    }
    [source.evidence_class, source.rule_version, source.sha256].forEach(v => cell(tr, v));
  });
  clear('limits'); data.limitations.forEach(value => {
    const li = document.createElement('li'); li.textContent = value; $('limits').append(li);
  });
}
async function init() {
  try {
    const response = await fetch('data.json', {cache: 'no-store'});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    data = await response.json();
    if (data.schema_version !== '2.0') throw new Error('Unsupported payload version');
    renderLab(); renderField(); renderSources();
    $('round').addEventListener('change', renderLab);
    $('case-select').addEventListener('change', renderCase);
    $('stratum').addEventListener('change', renderStratum);
    $('content').hidden = false; $('state').hidden = true;
  } catch (error) {
    $('state').textContent = `Evidence unavailable: ${error.message}. Serve this directory over HTTP and rebuild the dashboard from its source artifacts.`;
    $('state').classList.add('error');
  }
}
init();
