"""Build deterministic dashboard JSON from explicit input artifacts.

Required: event-log-r1/r2.csv and conformance-r1/r2.csv under --data-dir.
Optional: bpic2019_results.json. No static fallback data or run timestamps.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path, PureWindowsPath
import shutil

from compare_lab_field import compare
from check_conformance import RULES, check_case, load
from evaluate import ROOT, evaluate, load_conformance, write_json


def validate_conformance(data_dir: Path) -> None:
    """Reject a stale verdict artifact before publishing any output."""
    legacy_path = ROOT / 'src' / 'legacy' / 'check_conformance_v1.py'
    legacy = None
    for era in ('r1', 'r2'):
        rows, version = load_conformance(data_dir / ('conformance-%s.csv' % era))
        event_path = data_dir / ('event-log-%s.csv' % era)
        if version == 'v1':
            if legacy is None:
                spec = importlib.util.spec_from_file_location('frozen_checker_v1', legacy_path)
                legacy = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(legacy)
            cases = legacy.load(event_path)
        else:
            cases = load(event_path)
        if set(cases) != {row['case_id'] for row in rows}:
            raise ValueError('event/conformance case IDs differ for %s' % era)
        for row in rows:
            cid = row['case_id']
            trace = cases[cid]
            if version == 'v1':
                rules = legacy.check_case(trace)[0]
                failed = {rule for rule in RULES if rules[rule]}
                unknown = set()
            else:
                rules = check_case(trace)[0]
                failed = {rule for rule in RULES if rules[rule] is True}
                unknown = {rule for rule in RULES if rules[rule] is None}
            if failed != row['violations'] or unknown != row['unknown']:
                raise ValueError('event/conformance verdicts differ for %s case %s (%s); rerun its %s checker'
                                 % (era, cid, version, version))


def public_field_bytes(source: bytes) -> bytes:
    """Preserve the source summary while removing a local XES location from public copies."""
    field = json.loads(source)
    if not isinstance(field, dict):
        raise ValueError('field summary must be an object')
    location = field.get('source_xes')
    if isinstance(location, str):
        basename = PureWindowsPath(location).name if '\\' in location else Path(location).name
        if basename != location:
            field['source_xes'] = basename
            return (json.dumps(field, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')
    return source


def case_examples(data_dir: Path) -> dict:
    """One deterministic observed case per scenario, paired with its source trace."""
    result = {}
    for era in ('r1', 'r2'):
        with (data_dir / ('conformance-%s.csv' % era)).open(newline='') as handle:
            rows = list(csv.DictReader(handle))
        chosen = {}
        for row in rows:
            chosen.setdefault(row.get('scenario') or '(unknown)', row)
        traces = {row['case_id']: [] for row in chosen.values()}
        with (data_dir / ('event-log-%s.csv' % era)).open(newline='') as handle:
            for event in csv.DictReader(handle):
                if event['case_id'] in traces:
                    traces[event['case_id']].append(dict(
                        activity=event.get('activity', ''), timestamp=event.get('timestamp', ''),
                        qty_received=event.get('qty_received', '') if event.get('activity') == 'Goods Receipt' else '',
                        qty_invoiced=event.get('qty_invoiced', '') if event.get('activity') == 'Vendor Invoice' else ''))
        result[era] = [dict(case_id=row['case_id'], scenario=scenario,
                            status=row.get('status') or ('compliant' if row.get('violations') == 'OK' else 'violating'),
                            rule_version=row.get('rule_version') or 'v1',
                            violations=[v for v in row.get('violations', '').split(';') if v and v != 'OK'],
                            unknown_rules=[v for v in row.get('not_evaluable', '').split(';') if v],
                            trace=traces[row['case_id']])
                       for scenario, row in sorted(chosen.items())]
    return result


def build(data_dir: Path, output_path: Path) -> dict:
    """Derive, hash and write a strict JSON payload. Paths are source-relative."""
    data_dir = Path(data_dir)
    required = ['conformance-r1.csv', 'conformance-r2.csv', 'event-log-r1.csv', 'event-log-r2.csv']
    # Read source bytes before writing so missing inputs cannot create partial output.
    contents = {name: (data_dir / name).read_bytes() for name in required}
    validate_conformance(data_dir)
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
                   examples=case_examples(data_dir),
                   provenance=dict(builder='build_dashboard.py', sources=sources,
                                   path_base='Paths are relative to the selected data directory.',
                                   historical_note='Unversioned conformance CSV is historical v1; v2 is explicit. Field proxy version is separate.'),
                   limitations=lab['limitations'] + field['limitations'])
    write_json(payload, output_path)
    return payload


def build_site(data_dir: Path, site_dir: Path, payload: dict) -> None:
    """Copy small source files and an offline-capable static viewer for this run."""
    site_dir.mkdir(parents=True, exist_ok=True)
    for name in ('index.html', 'app.js', 'styles.css'):
        source, target = ROOT / 'webpage' / name, site_dir / name
        if source.resolve() != target.resolve():
            shutil.copyfile(source, target)
    docs = site_dir / 'docs'
    docs.mkdir(exist_ok=True)
    for name in ('erp-pilot.md', 'event-contract.md'):
        shutil.copyfile(ROOT / 'docs' / name, docs / name)
    examples = site_dir / 'examples'
    examples.mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'examples' / 'erp-recorded-events.csv', examples / 'erp-recorded-events.csv')
    artifacts = site_dir / 'artifacts'
    artifacts.mkdir(exist_ok=True)
    for source in payload['provenance']['sources']:
        name = source['path']
        original = (data_dir / name).read_bytes()
        if hashlib.sha256(original).hexdigest() != source['sha256']:
            raise ValueError('source changed during build: %s' % name)
        source['source_sha256'] = source['sha256']
        if name == 'bpic2019_results.json':
            content = public_field_bytes(original)
            (artifacts / name).write_bytes(content)
        else:
            content = original
            (artifacts / name).write_bytes(content)
        source['sha256'] = hashlib.sha256(content).hexdigest()
        if content != original:
            source['transformation'] = 'Public copy reduces source_xes to its basename; source_sha256 identifies the original input.'
        source['download'] = 'artifacts/' + name
    payload['provenance']['path_base'] = ('path is relative to the selected input data directory; '
                                          'download is relative to this viewer. source_sha256 hashes the input; '
                                          'sha256 hashes the downloadable public copy.')
    write_json(payload, site_dir / 'data.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    parser.add_argument('--out', type=Path, default=ROOT / 'output' / 'reports' / 'dashboard.json')
    parser.add_argument('--site-dir', type=Path, help='build a self-contained static viewer here')
    args = parser.parse_args(argv)
    try:
        result = build(args.data_dir, args.out)
        if args.site_dir:
            build_site(args.data_dir, args.site_dir, result)
    except (OSError, ValueError) as exc:
        parser.exit(1, 'dashboard build error: %s\n' % exc)
    print('Wrote %s' % args.out)
    return result


if __name__ == '__main__':
    main()
