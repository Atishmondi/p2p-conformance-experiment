"""Describe separate lab controls and historical BPI field proxies.

The definitions differ: contrasts are contextual, never a pooled estimate or a
causal/statistical test of a shared control. Counts in the JSON source determine
all displayed field rates; cached source rate fields are deliberately ignored.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from evaluate import ROOT, evaluate, wilson_ci, write_json

FIELD_VERSION = 'historical-field-proxies-v1'
METRICS = ('r1_maverick', 'r2_viol', 'r3_viol', 'r4_rework', 'r5_viol', 'approval_change_after_po')
DEFINITIONS = {
    'r1_maverick': 'Vendor-created invoice before PO item (field proxy, not lab approval R1).',
    'r2_viol': 'Invoice receipt before goods receipt in after-GR stratum; field applicability differs from lab R2.',
    'r3_viol': 'Historical monetary-value proxy from Cumulative net worth: maximum invoice worth exceeds first PO worth by more than epsilon; differs from lab cumulative invoice/receipt item quantities R3.',
    'r4_rework': 'Quantity or price change after PO item; not lab modification/reapproval interval R4.',
    'r5_viol': 'Invoice clearing before invoice receipt; payment signal differs from lab R5.',
    'approval_change_after_po': 'Approval-change activity after PO; separate from corrected field rework.'}


def _count(value, name):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError('field %s must be a nonnegative integer or null' % name)
    return value


def _metric(source):
    if not isinstance(source, dict):
        raise ValueError('field metric must be an object')
    x, n = (_count(source.get(key), key) for key in ('n_true', 'n_applicable'))
    if x is not None and n is not None and x > n:
        raise ValueError('field n_true exceeds n_applicable')
    return dict(n_true=x, n_applicable=n, rate=x / n if x is not None and n else None,
                wilson_95=wilson_ci(x, n))


def _stratum(source, n_cases=None):
    if source is None:
        return dict(available=False, n_cases=n_cases, metrics={})
    if not isinstance(source, dict):
        raise ValueError('field stratum must be an object')
    embedded_cases = _count(source.get('n_cases'), 'n_cases')
    if n_cases is not None and embedded_cases is not None and n_cases != embedded_cases:
        raise ValueError('field overall n_cases conflicts with top-level n_cases')
    total = n_cases if n_cases is not None else embedded_cases
    metrics = {key: _metric(source[key]) for key in METRICS if key in source}
    if total is not None:
        for key, metric in metrics.items():
            applicable = metric['n_applicable']
            if applicable is not None and applicable > total:
                raise ValueError('field %s n_applicable exceeds n_cases' % key)
    return dict(available=True, n_cases=total, metrics=metrics)


def compare(data_dir: Path, lab=None):
    """Return explicit availability and disjoint field strata; never write."""
    path = Path(data_dir) / 'bpic2019_results.json'
    result = dict(available=False, source='bpic2019_results.json',
                  evidence_class='observational_field_summary', rule_version=FIELD_VERSION,
                  strata={}, contrasts=[], definitions=DEFINITIONS,
                  limitations=[
                      'Checked-in historical summary; raw XES is not rerun by the demo.',
                      'Field proxies and lab rules have different activities, quantities, and applicability.',
                      'Strata retain their own denominators; no lab/field pooling or inferential comparison.'])
    if not path.exists():
        result['unavailable_reason'] = 'Optional bpic2019_results.json was not supplied.'
        return result
    with path.open() as handle:
        source = json.load(handle)
    if not isinstance(source, dict):
        raise ValueError('field summary must be an object')
    version = source.get('rule_version', FIELD_VERSION)
    if not isinstance(version, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', version):
        raise ValueError('field rule_version must be a nonempty version label')
    result['rule_version'] = version
    result['available'] = True
    for key in ('three_way_strata', 'by_item_category'):
        if key in source and not isinstance(source[key], dict):
            raise ValueError('field %s must be an object' % key)
    # Never copy source_xes or arbitrary metadata: legacy summaries can contain
    # machine-local absolute paths and old cached anchors/verdicts.
    strata = dict(overall=_stratum(source.get('overall'), _count(source.get('n_cases'), 'n_cases')),
                  two_way=_stratum(source.get('r1_two_way_stratum')),
                  three_way_after=_stratum(source.get('three_way_strata', {}).get('after')),
                  three_way_before=_stratum(source.get('three_way_strata', {}).get('before')))
    categories = source.get('by_item_category', {})
    if any(not isinstance(category, str) for category in categories):
        raise ValueError('field by_item_category keys must be strings')
    for category, values in sorted(categories.items()):
        strata['item_category:' + category] = _stratum(values)
    result['strata'] = strata
    lab = evaluate(data_dir) if lab is None else lab
    for rule, scenario, field_key, field_stratum in (
            ('R2', 'S3', 'r2_viol', 'three_way_after'),
            ('R3', 'S4', 'r3_viol', 'three_way_after'),
            ('R3', 'S4', 'r3_viol', 'three_way_before'),
            ('R4', 'S6', 'r4_rework', 'three_way_after'),
            ('R4', 'S6', 'r4_rework', 'three_way_before'),
            ('R1', None, 'r1_maverick', 'two_way')):
        cohort = lab['cohorts']['r1']['scenarios'][scenario] if scenario else lab['cohorts']['r1']['overall']
        result['contrasts'].append(dict(lab_era='r1', lab_scenario=scenario, lab_rule=rule,
                                       lab=cohort['rules'][rule], field_stratum=field_stratum,
                                       field_metric=field_key, field=strata[field_stratum]['metrics'].get(field_key),
                                       comparable=False, reason=DEFINITIONS[field_key]))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    parser.add_argument('--out', type=Path, default=ROOT / 'output' / 'reports' / 'comparison.json')
    args = parser.parse_args(argv)
    try:
        # Required lab inputs fail visibly even when optional field data is absent.
        result = compare(args.data_dir, lab=evaluate(args.data_dir))
        write_json(result, args.out)
    except (OSError, ValueError) as exc:
        parser.exit(1, 'comparison error: %s\n' % exc)
    print('Wrote %s' % args.out)
    return result


if __name__ == '__main__':
    main()
