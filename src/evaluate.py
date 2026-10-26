"""Descriptive synthetic-cohort reporting, derived from conformance/event artifacts.

No optional dependency or write is triggered on import. --scientific explicitly
requests SciPy diagnostics; generated cohorts support no causal interpretation.
JSON null means unknown/unavailable, including rates with zero denominators.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import statistics

from check_conformance import load

ROOT = Path(__file__).resolve().parents[1]
RULES = ('R1', 'R2', 'R3', 'R4', 'R5')
TARGETED = {'r1': ('S3', 'S4', 'S6'), 'r2': ('S3R', 'S4R', 'S6R')}
SCENARIOS = {'r1': ('S1', 'S2', 'S3', 'S4', 'S5', 'S6'), 'r2': TARGETED['r2']}


def wilson_ci(k, n, z=1.959963984540054):
    """95% Wilson interval for evaluated Bernoulli observations, else unknown."""
    if not n or k is None:
        return [None, None]
    p = k / n
    denom = 1 + z * z / n
    center = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [max(0.0, (center - margin) / denom), min(1.0, (center + margin) / denom)]


def _rules(value, label):
    items = value.strip().split(';') if value.strip() else []
    if len(items) != len(set(items)) or set(items) - set(RULES):
        raise ValueError('unsupported or duplicate %s rules: %s' % (label, value))
    return set(items)


def load_conformance(path):
    """Read v1 historical or v2 tri-state rows without relabeling history."""
    with Path(path).open(newline='') as handle:
        reader = csv.DictReader(handle)
        if not {'case_id', 'scenario', 'violations'} <= set(reader.fieldnames or []):
            raise ValueError('conformance requires case_id, scenario, violations: %s' % path)
        records = list(reader)
        columns = set(reader.fieldnames or [])
    rows, versions, seen = [], set(), set()
    for row in records:
        cid = row['case_id'].strip()
        if not cid or cid in seen:
            raise ValueError('blank or duplicate conformance case_id: %s' % cid)
        seen.add(cid)
        version = row.get('rule_version', '').strip() or 'v1'
        if version not in ('v1', 'v2'):
            raise ValueError('unsupported rule version: %s' % version)
        versions.add(version)
        violations = _rules('' if row['violations'].strip() == 'OK' else row['violations'], 'violation')
        unknown = _rules(row.get('not_evaluable', ''), 'unknown')
        if violations & unknown:
            raise ValueError('rule cannot be both violated and not_evaluable')
        expected = 'violating' if violations else ('not_evaluable' if unknown else 'compliant')
        if version == 'v2':
            if not {'not_evaluable', 'status', 'rule_version'} <= columns:
                raise ValueError('v2 requires not_evaluable, status, and rule_version columns')
            if row.get('status') != expected:
                raise ValueError('inconsistent v2 status for case %s' % cid)
            if expected == 'compliant' and row['violations'].strip() != 'OK':
                raise ValueError('v2 compliant status requires OK for case %s' % cid)
        elif unknown or row['violations'].strip() == '':
            raise ValueError('v1 rows require OK or violations and cannot express unknown rules')
        rows.append(dict(case_id=cid, scenario=row['scenario'].strip(),
                         violations=violations, unknown=unknown, status=expected))
    if len(versions) > 1:
        raise ValueError('mixed rule versions in one conformance cohort')
    return rows, next(iter(versions), None)


def summarize(rows):
    """Case status denominator and separate rule-specific evidence denominators."""
    counts = {key: sum(row['status'] == key for row in rows)
              for key in ('compliant', 'violating', 'not_evaluable')}
    n = counts['compliant'] + counts['violating']
    rules = {}
    for rule in RULES:
        bad = sum(rule in row['violations'] for row in rows)
        unknown = sum(rule in row['unknown'] for row in rows)
        evaluated = len(rows) - unknown
        rules[rule] = dict(violating=bad, compliant=evaluated - bad,
                           not_evaluable=unknown, evaluated_cases=evaluated,
                           violation_rate=bad / evaluated if evaluated else None,
                           wilson_95=wilson_ci(bad, evaluated))
    return dict(counts, cases=len(rows), evaluated_cases=n,
                violation_rate=counts['violating'] / n if n else None,
                conformance_rate=counts['compliant'] / n if n else None,
                wilson_95=wilson_ci(counts['violating'], n), rules=rules)


def _sample(values):
    return dict(n=len(values), mean_days=statistics.fmean(values) if values else None,
                median_days=statistics.median(values) if values else None,
                stdev_days=statistics.stdev(values) if len(values) > 1 else None)


def _finite(value):
    value = float(value)
    return value if math.isfinite(value) else None


def scientific_diagnostics(cohorts, samples):
    """Optional dynamic diagnostics; no pooling of lab and field definitions."""
    try:
        from scipy.stats import chi2_contingency, fisher_exact, ttest_ind
    except ImportError as exc:
        raise RuntimeError('--scientific requires optional SciPy; omit it for the stdlib report') from exc
    result = dict(requested=True, available=True,
                  interpretation='Exploratory diagnostics on generated cohorts; no causal inference.',
                  chi2=None, chi2_p=None, fisher_p=None, fisher_oddsratio=None,
                  cohens_h=None, welch_t=None, welch_p=None, welch_df=None,
                  cohens_d_cycle=None)
    a, b = (cohorts[era]['targeted'] for era in ('r1', 'r2'))
    if (a['evaluated_cases'] and b['evaluated_cases'] and
            cohorts['r1']['rule_version'] == cohorts['r2']['rule_version']):
        table = [[r['violating'], r['compliant']] for r in (a, b)]
        odds, p = fisher_exact(table, alternative='two-sided')
        result.update(fisher_p=_finite(p), fisher_oddsratio=_finite(odds))
        if all(sum(row[col] for row in table) for col in (0, 1)):
            chi2, p, _, _ = chi2_contingency(table, correction=False)
            result.update(chi2=_finite(chi2), chi2_p=_finite(p))
        result['cohens_h'] = abs(2 * math.asin(math.sqrt(a['violation_rate'])) -
                                 2 * math.asin(math.sqrt(b['violation_rate'])))
    s1, s2 = (samples['r1'].get(scenario, []) for scenario in ('S1', 'S2'))
    if len(s1) > 1 and len(s2) > 1:
        v1, v2 = statistics.variance(s1), statistics.variance(s2)
        if v1 + v2:
            test = ttest_ind(s1, s2, equal_var=False)
            denom = (v1 / len(s1)) ** 2 / (len(s1) - 1) + (v2 / len(s2)) ** 2 / (len(s2) - 1)
            df = (v1 / len(s1) + v2 / len(s2)) ** 2 / denom
            result.update(welch_t=_finite(test.statistic), welch_p=_finite(test.pvalue),
                          welch_df=df,
                          cohens_d_cycle=(statistics.fmean(s2) - statistics.fmean(s1)) / math.sqrt((v1 + v2) / 2))
    return result


def evaluate(data_dir: Path, scientific=False):
    """Return data-derived description of required r1/r2 input pairs; never write."""
    data_dir = Path(data_dir)
    cohorts, throughput, vendors, samples = {}, {}, {}, {}
    for era in ('r1', 'r2'):
        rows, version = load_conformance(data_dir / ('conformance-%s.csv' % era))
        events = load(data_dir / ('event-log-%s.csv' % era))
        if set(events) != {row['case_id'] for row in rows}:
            raise ValueError('event/conformance case IDs differ for %s' % era)
        by_scenario = sorted(set(SCENARIOS[era]) | {row['scenario'] for row in rows})
        cohorts[era] = dict(rule_version=version, evidence_class='synthetic_demonstration',
                            overall=summarize(rows), targeted_scenarios=list(TARGETED[era]),
                            targeted=summarize([row for row in rows if row['scenario'] in TARGETED[era]]),
                            scenarios={s: summarize([row for row in rows if row['scenario'] == s]) for s in by_scenario})
        samples[era] = {s: [] for s in by_scenario}
        vendor_cases = {}
        for row in rows:
            trace = events[row['case_id']]
            scenarios = {event.get('scenario', '').strip() for event in trace} - {''}
            if scenarios and scenarios != {row['scenario']}:
                raise ValueError('event/conformance scenarios differ for case %s' % row['case_id'])
            dates = [event['_ts'] for event in trace]
            samples[era][row['scenario']].append((max(dates) - min(dates)).total_seconds() / 86400)
            names = {event.get('vendor', '').strip() for event in trace} - {''}
            if len(names) > 1:
                raise ValueError('conflicting vendors for case %s' % row['case_id'])
            vendor = next(iter(names), '(unknown)')
            vendor_cases.setdefault(vendor, []).append(row)
        throughput[era] = {s: _sample(values) for s, values in samples[era].items()}
        vendors[era] = {vendor: summarize(values) for vendor, values in sorted(vendor_cases.items())}
    a, b = (cohorts[era]['targeted']['violation_rate'] for era in ('r1', 'r2'))
    comparable = (cohorts['r1']['rule_version'] is not None and
                  cohorts['r1']['rule_version'] == cohorts['r2']['rule_version'])
    difference = a - b if comparable and a is not None and b is not None else None
    return dict(evidence_class='synthetic_demonstration', cohorts=cohorts, throughput=throughput,
                vendors=vendors,
                targeted_comparison=dict(comparable=comparable, absolute_rate_difference=difference,
                    relative_rate_difference=difference / a if a and difference is not None else None,
                    interpretation='Descriptive difference between generated targeted cohorts; no measured operational or causal effect.'),
                scientific=scientific_diagnostics(cohorts, samples) if scientific else dict(requested=False, available=False),
                limitations=[
                    'Generated cases demonstrate fictional controls; they do not measure operational savings.',
                    'Case rates exclude not_evaluable status; rule rates exclude unknown outcomes for that rule.',
                    'A proven violation establishes violating status even when other rules are unknown.',
                    'Wilson intervals describe these samples; generator design limits statistical generalization.',
                    'Cycle times derive from observed first/last timestamps, not business-calendar durations.'])


def write_json(payload, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    parser.add_argument('--out', type=Path, default=ROOT / 'output' / 'reports' / 'evaluation.json')
    parser.add_argument('--scientific', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = evaluate(args.data_dir, scientific=args.scientific)
        write_json(result, args.out)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, 'evaluation error: %s\n' % exc)
    print('Wrote %s' % args.out)
    return result


if __name__ == '__main__':
    main()
