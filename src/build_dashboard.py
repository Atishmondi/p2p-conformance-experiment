"""Build deterministic dashboard JSON from explicit input artifacts.

Required: event-log-r1/r2.csv and conformance-r1/r2.csv under --data-dir.
Optional: bpic2019_results.json. No static fallback data or run timestamps.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from compare_lab_field import compare
from evaluate import ROOT, evaluate, write_json


def build(data_dir: Path, output_path: Path) -> dict:
    """Derive, hash and write a strict JSON payload. Paths are source-relative."""
    data_dir = Path(data_dir)
    required = ['conformance-r1.csv', 'conformance-r2.csv', 'event-log-r1.csv', 'event-log-r2.csv']
    # Read source bytes before writing so missing inputs cannot create partial output.
    contents = {name: (data_dir / name).read_bytes() for name in required}
    lab = evaluate(data_dir)
    field = compare(data_dir, lab=lab)
    if field['available']:
        contents['bpic2019_results.json'] = (data_dir / 'bpic2019_results.json').read_bytes()
    sources = []
    for name, content in sorted(contents.items()):
        era = 'r1' if '-r1.' in name else 'r2'
        is_field = name == 'bpic2019_results.json'
        sources.append(dict(path=name, sha256=hashlib.sha256(content).hexdigest(),
                            evidence_class='observational_field_summary' if is_field else 'synthetic_demonstration',
                            rule_version=field['rule_version'] if is_field else lab['cohorts'][era]['rule_version']))
    payload = dict(schema_version='2.0', lab=lab, field=field,
                   provenance=dict(builder='build_dashboard.py', sources=sources,
                                   path_base='Paths are relative to the selected data directory.',
                                   historical_note='Unversioned conformance CSV is historical v1; v2 is explicit. Field proxy version is separate.'),
                   limitations=lab['limitations'] + field['limitations'])
    write_json(payload, output_path)
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    parser.add_argument('--out', type=Path, default=ROOT / 'output' / 'reports' / 'dashboard.json')
    args = parser.parse_args(argv)
    try:
        result = build(args.data_dir, args.out)
    except (OSError, ValueError) as exc:
        parser.exit(1, 'dashboard build error: %s\n' % exc)
    print('Wrote %s' % args.out)
    return result


if __name__ == '__main__':
    main()
