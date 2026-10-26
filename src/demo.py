"""Build an isolated standard-library demonstration, with no raw XES or ERP.

A fresh output directory is reserved before generation. Existing directories fail
without edits. Seeds are explicit; report content has no execution timestamps.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from build_dashboard import build
from check_conformance import load, write_results
from compare_lab_field import compare
from evaluate import ROOT, evaluate, write_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'output' / 'demo')
    parser.add_argument('--n', type=int, default=20, help='cases per scenario, positive integer')
    parser.add_argument('--seed-r1', type=int, default=42)
    parser.add_argument('--seed-r2', type=int, default=7)
    parser.add_argument('--without-field', action='store_true', help='omit optional historical field summary')
    args = parser.parse_args(argv)
    if args.n <= 0:
        parser.error('--n must be positive')
    out = args.output_dir.resolve()
    try:
        out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.exit(1, 'demo error: output directory already exists: %s\n' % out)
    try:
        for era in ('r1', 'r2'):
            generator = ROOT / 'src' / ('generate_log.py' if era == 'r1' else 'generate_log_r2.py')
            event_path = out / ('event-log-%s.csv' % era)
            # Propagate -S so the whole end-to-end guarantee covers child interpreters.
            command = [sys.executable] + (['-S'] if sys.flags.no_site else [])
            command += [str(generator), '--n', str(args.n), '--seed', str(getattr(args, 'seed_' + era)), '--out', str(event_path)]
            subprocess.run(command, check=True)
            write_results(load(event_path), out, era)
        field_path = ROOT / 'data' / 'bpic2019_results.json'
        if not args.without_field and field_path.is_file():
            # Preserve historical counts while removing the author's local XES path.
            field = json.loads(field_path.read_text())
            if 'source_xes' in field:
                field['source_xes'] = Path(field['source_xes']).name
            write_json(field, out / 'bpic2019_results.json')
        lab = evaluate(out)
        write_json(lab, out / 'evaluation.json')
        write_json(compare(out, lab=lab), out / 'comparison.json')
        build(out, out / 'dashboard.json')
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, 'demo error (partial output retained): %s\n' % exc)
    print('Built %s/dashboard.json' % out)
    return out


if __name__ == '__main__':
    main()
