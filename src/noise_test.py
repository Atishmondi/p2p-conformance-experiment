"""Seeded drop-noise diagnostic using the shared v2 checker (stdlib only).

Rates use evaluated cases. Unknown cases and their separate denominators are
reported; missing events never become false positives or compliant evidence.
The synthetic S3/S4/S6 labels are fixture expectations, not field ground truth.
"""
import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

from check_conformance import RULES, RULE_VERSION, check_case, load


def case_status(rules):
    if any(value is True for value in rules.values()):
        return 'violating'
    return 'not_evaluable' if any(value is None for value in rules.values()) else 'compliant'


def eval_cases(cases):
    """Return known failed rules and full tri-state evaluations, including empties."""
    failed, full = {}, {}
    for case_id, events in cases.items():
        rules = check_case(events)[0]
        failed[case_id] = [rule for rule in RULES if rules[rule] is True]
        full[case_id] = rules
    return failed, full


def run_sweep(cases, levels=(0, .02, .05, .10), seeds=(1, 2, 3)):
    scenarios = {case_id: events[0].get('scenario', '') for case_id, events in cases.items() if events}
    targets = [case_id for case_id, scenario in scenarios.items() if scenario in ('S3', 'S4', 'S6')]
    clean = [case_id for case_id, scenario in scenarios.items() if scenario == 'S1']
    events = [(case_id, event) for case_id, rows in cases.items() for event in rows]
    results = []
    for level in levels:
        if not 0 <= level <= 1:
            raise ValueError('noise level must be between zero and one')
        for seed in seeds:
            dropped = set(random.Random(seed).sample(range(len(events)), round(level * len(events))))
            noisy = defaultdict(list)
            for index, (case_id, event) in enumerate(events):
                if index not in dropped:
                    noisy[case_id].append(event)
            _, full = eval_cases(noisy)
            statuses = {case_id: case_status(rules) for case_id, rules in full.items()}
            target_evaluated = sum(statuses.get(case_id, 'not_evaluable') != 'not_evaluable' for case_id in targets)
            s1_evaluated = sum(statuses.get(case_id, 'not_evaluable') != 'not_evaluable' for case_id in clean)
            tp = sum(statuses.get(case_id) == 'violating' for case_id in targets)
            fp = sum(statuses.get(case_id) == 'violating' for case_id in clean)
            results.append({'noise_level': level, 'seed': seed,
                            'recall': tp / target_evaluated if target_evaluated else None,
                            'fpr': fp / s1_evaluated if s1_evaluated else None,
                            'target_evaluated': target_evaluated,
                            'target_not_evaluable': len(targets) - target_evaluated,
                            's1_evaluated': s1_evaluated, 's1_not_evaluable': len(clean) - s1_evaluated,
                            'rule_version': RULE_VERSION})
    return results


def main(argv=None):
    base = Path(__file__).resolve().parents[1] / 'data'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=base / 'event-log-r1.csv')
    parser.add_argument('--output-dir', type=Path, default=base)
    args = parser.parse_args(argv)
    try:
        results = run_sweep(load(args.input))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / 'robustness.csv'
    fields = ['noise_level', 'seed', 'recall', 'fpr', 'target_evaluated',
              'target_not_evaluable', 's1_evaluated', 's1_not_evaluable', 'rule_version']
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in results:
            writer.writerow(dict(row, **{field: '%.4f' % row[field] if row[field] is not None else ''
                                         for field in ('recall', 'fpr')}))
    print('Wrote %s (%s v2 diagnostic rows; evaluated denominators reported)' % (path, len(results)))
    return path


if __name__ == '__main__':
    main()
