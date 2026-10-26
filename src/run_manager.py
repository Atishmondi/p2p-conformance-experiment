"""Generate and check isolated experiments without touching canonical artifacts.

--output-dir selects the data root (default: output/experiments). A new runs/<tag>/ is
reserved exclusively; its logs and v2 results are written directly there.
The root's runs.csv records cohort counts, seeds, and evaluated denominators.
"""
import argparse
import csv
import random
import statistics
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from check_conformance import RULE_VERSION, load, validate_tag, write_results

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
DATA = ROOT / 'output' / 'experiments'
HEADER = ['run_id', 'utc_time', 'era', 'n_per_scenario', 'seed',
          'cases', 'events', 'viol_rate', 'mean_cycle',
          'compliant', 'violating', 'not_evaluable', 'evaluated_cases', 'rule_version']
GEN = {'r1': SRC / 'generate_log.py', 'r2': SRC / 'generate_log_r2.py'}


def default_tag():
    return datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f') + '-' + uuid4().hex[:12]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n', type=int, default=20, help='per-scenario cases (positive integer)')
    parser.add_argument('--era', choices=['r1', 'r2', 'both'], default='both')
    parser.add_argument('--tag', default=None, help='new single-component run directory name')
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--seed-r1', type=int, default=None)
    parser.add_argument('--seed-r2', type=int, default=None)
    parser.add_argument('--output-dir', type=Path, default=DATA, help='data root containing runs/ and runs.csv')
    args = parser.parse_args(argv)
    if args.n <= 0:
        parser.error('--n must be positive')
    if args.tag is not None:
        try:
            validate_tag(args.tag)
        except ValueError as exc:
            parser.error(str(exc))
    return args


def run_cmd(command):
    print('+ ' + ' '.join(str(value) for value in command))
    subprocess.run(command, check=True, cwd=str(ROOT))


def compute_metrics(conformance_csv, event_log_csv):
    with open(conformance_csv, newline='') as handle:
        rows = list(csv.DictReader(handle))
    counts = {status: sum(row['status'] == status for row in rows)
              for status in ('compliant', 'violating', 'not_evaluable')}
    if sum(counts.values()) != len(rows):
        raise ValueError('conformance rows contain an unsupported status')
    evaluated = counts['compliant'] + counts['violating']
    cycles = [float(row['cycle_days']) for row in rows if row['cycle_days'].strip()]
    with open(event_log_csv, newline='') as handle:
        events = sum(1 for _ in csv.DictReader(handle))
    return dict(counts, cases=len(rows), events=events, evaluated_cases=evaluated,
                viol_rate=counts['violating'] / evaluated if evaluated else None,
                mean_cycle=statistics.fmean(cycles) if cycles else None)



@contextmanager
def registry_session(output_dir):
    """Serialize preflight and all writes, failing busy before run reservation.

    mkdir is atomic and available in the standard library on every supported
    platform. A killed process can leave the lock directory; never steal it.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    lock = output_dir / '.runs.lock'
    try:
        lock.mkdir()
    except FileExistsError:
        raise SystemExit('run registry busy: %s; retry after the active run finishes' % output_dir)
    try:
        registry = output_dir / 'runs.csv'
        try:
            with registry.open(newline='') as handle:
                if next(csv.reader(handle), None) != HEADER:
                    raise SystemExit('runs.csv has an incompatible header; choose a fresh --output-dir')
        except FileNotFoundError:
            with registry.open('x', newline='') as handle:
                csv.writer(handle).writerow(HEADER)
        yield
    finally:
        lock.rmdir()


def run_era(era, n, seed, tag, utc_time, output_dir):
    """Run one era with registry serialization; the caller reserves its tag."""
    with registry_session(output_dir):
        return _run_era(era, n, seed, tag, utc_time, output_dir)


def _run_era(era, n, seed, tag, utc_time, output_dir):
    """Generate and append while the caller holds registry_session."""
    output_dir = Path(output_dir)
    run_dir = output_dir / 'runs' / tag
    out_log = run_dir / ('event-log-%s.csv' % era)
    run_cmd([sys.executable, str(GEN[era]), '--n', str(n), '--seed', str(seed), '--out', str(out_log)])
    paths = write_results(load(out_log), run_dir, era)
    metrics = compute_metrics(paths['conformance'], out_log)
    registry = output_dir / 'runs.csv'
    run_id = '%s-%s' % (tag, era)
    row = [run_id, utc_time, era, n, seed, metrics['cases'], metrics['events'],
           '%.4f' % metrics['viol_rate'] if metrics['viol_rate'] is not None else '',
           '%.4f' % metrics['mean_cycle'] if metrics['mean_cycle'] is not None else '']
    row += [metrics[key] for key in ('compliant', 'violating', 'not_evaluable', 'evaluated_cases')]
    with registry.open('a', newline='') as handle:
        csv.writer(handle).writerow(row + [RULE_VERSION])
    print('logged %s: seed=%s cases=%s evaluated=%s' %
          (run_id, seed, metrics['cases'], metrics['evaluated_cases']))
    return run_id


def main(argv=None):
    args = parse_args(argv)
    tag = args.tag if args.tag is not None else default_tag()
    output_dir = args.output_dir.resolve()
    run_dir = output_dir / 'runs' / tag
    eras = ['r1', 'r2'] if args.era == 'both' else [args.era]
    seeds = {}
    for era in eras:
        override = args.seed_r1 if era == 'r1' else args.seed_r2
        seeds[era] = override if override is not None else (args.seed if args.seed is not None
                                                           else random.SystemRandom().randint(0, 2 ** 31 - 1))
    with registry_session(output_dir):
        try:
            run_dir.parent.mkdir(parents=True, exist_ok=True)
            run_dir.mkdir()  # atomic reservation, rejecting duplicate tags and symlinks
        except FileExistsError:
            raise SystemExit('run directory already exists: %s' % run_dir)
        utc_time = datetime.now(timezone.utc).isoformat(timespec='seconds')
        for era in eras:
            _run_era(era, args.n, seeds[era], tag, utc_time, output_dir)
    print('done tag=%s eras=%s' % (tag, eras))
    return run_dir


if __name__ == '__main__':
    main()
