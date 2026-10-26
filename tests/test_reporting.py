"""Reporting fixtures catch fixed anchors, unknown-as-clean, and provenance drift."""
import csv
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SRC = Path(__file__).resolve().parents[1] / 'src'
sys.path.insert(0, str(SRC))


def fixture(root):
    # Hand counted: R1 overall 1 bad / 2 evaluated + 1 unknown; targeted
    # S3+S4+S6 has 1 bad / 1 evaluated + 1 unknown. R2 is 0 / 1.
    columns = ['case_id', 'scenario', 'violations', 'not_evaluable', 'status', 'rule_version']
    rows = {
        'r1': [('a', 'S1', 'OK', '', 'compliant', 'v2'),
               ('b', 'S3', 'R2', 'R3', 'violating', 'v2'),
               ('c', 'S4', '', 'R3', 'not_evaluable', 'v2')],
        'r2': [('d', 'S3R', 'OK', '', 'compliant', 'v2')],
    }
    for era, values in rows.items():
        with (root / ('conformance-%s.csv' % era)).open('w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(values)
        with (root / ('event-log-%s.csv' % era)).open('w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['case_id', 'activity', 'timestamp', 'scenario', 'vendor', 'qty_received', 'qty_invoiced'])
            for cid, scen, *_ in values:
                activities = ['Purchase Request', 'Purchase Request Approval', 'Purchase Order',
                              'Goods Receipt', 'Vendor Invoice', 'Payment']
                if cid == 'b':
                    activities[3], activities[4] = activities[4], activities[3]
                    activities.insert(5, 'Vendor Invoice')
                for index, activity in enumerate(activities):
                    hour = ((0, 8, 16, 24, 36, 42, 48) if cid == 'b' else (0, 8, 16, 24, 36, 48))[index]
                    writer.writerow([cid, activity, '2026-01-%02dT%02d:00:00' % (1 + hour // 24, hour % 24),
                                     scen, 'NewVendor',
                                     '' if cid in ('b', 'c') else ('10' if activity == 'Goods Receipt' else ''),
                                     ('10' if cid != 'b' or index == 5 else '')
                                     if activity == 'Vendor Invoice' else ''])


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fixture(self.root)

    def test_counts_targeting_unknowns_and_cycles_derive_from_artifacts(self):
        evaluate = importlib.import_module('evaluate').evaluate
        result = evaluate(self.root)
        r1 = result['cohorts']['r1']
        self.assertEqual(r1['rule_version'], 'v2')
        self.assertEqual(r1['overall']['cases'], 3)
        self.assertEqual(r1['overall']['evaluated_cases'], 2)
        self.assertEqual(r1['overall']['not_evaluable'], 1)
        self.assertEqual(r1['overall']['violation_rate'], 0.5)
        self.assertEqual(r1['targeted']['cases'], 2)
        self.assertEqual(r1['targeted']['violation_rate'], 1.0)
        self.assertEqual(r1['overall']['rules']['R3']['not_evaluable'], 2)
        self.assertEqual(r1['overall']['rules']['R3']['evaluated_cases'], 1)
        self.assertEqual(result['throughput']['r1']['S1']['mean_days'], 2.0)
        self.assertEqual(result['vendors']['r1']['NewVendor']['cases'], 3)
        self.assertIsNone(result['throughput']['r1']['S2']['mean_days'])
        self.assertFalse(result['scientific']['requested'])

    def test_empty_cohort_and_unknown_only_stratum_have_unknown_rates(self):
        evaluate = importlib.import_module('evaluate').evaluate
        path = self.root / 'conformance-r2.csv'
        path.write_text('case_id,scenario,violations,not_evaluable,status,rule_version\n')
        (self.root / 'event-log-r2.csv').write_text('case_id,activity,timestamp,scenario,vendor\n')
        result = evaluate(self.root)
        self.assertIsNone(result['cohorts']['r2']['overall']['violation_rate'])
        self.assertIsNone(result['cohorts']['r1']['scenarios']['S4']['violation_rate'])
        self.assertEqual(result['cohorts']['r2']['overall']['cases'], 0)

    def test_legacy_rows_are_labeled_v1_and_mixed_versions_rejected(self):
        evaluate = importlib.import_module('evaluate').evaluate
        path = self.root / 'conformance-r1.csv'
        path.write_text('case_id,scenario,violations\na,S1,OK\nb,S3,R2\nc,S4,R3\n')
        self.assertEqual(evaluate(self.root)['cohorts']['r1']['rule_version'], 'v1')
        path.write_text(path.read_text().replace('violations\n', 'violations,rule_version\n').replace('OK\n', 'OK,v1\n').replace('R2\n', 'R2,v2\n').replace('R3\n', 'R3,v1\n'))
        with self.assertRaisesRegex(ValueError, 'version|v2'):
            evaluate(self.root)

    def test_missing_and_inconsistent_input_fail_visibly(self):
        evaluate = importlib.import_module('evaluate').evaluate
        (self.root / 'conformance-r1.csv').unlink()
        with self.assertRaises(FileNotFoundError):
            evaluate(self.root)
        fixture(self.root)
        path = self.root / 'conformance-r1.csv'
        path.write_text(path.read_text().replace('R2,R3,violating', 'R2,R3,compliant'))
        with self.assertRaisesRegex(ValueError, 'status'):
            evaluate(self.root)

    def test_incomplete_v2_evidence_columns_are_rejected(self):
        evaluate = importlib.import_module('evaluate').evaluate
        path = self.root / 'conformance-r1.csv'
        path.write_text('case_id,scenario,violations,status,rule_version\na,S1,OK,compliant,v2\nb,S3,R2,violating,v2\nc,S4,OK,compliant,v2\n')
        with self.assertRaisesRegex(ValueError, 'not_evaluable'):
            evaluate(self.root)

    def test_mixed_cohort_versions_are_not_compared_as_one_policy(self):
        evaluate = importlib.import_module('evaluate').evaluate
        (self.root / 'conformance-r2.csv').write_text('case_id,scenario,violations\nd,S3R,OK\n')
        result = evaluate(self.root)
        self.assertFalse(result['targeted_comparison']['comparable'])
        self.assertIsNone(result['targeted_comparison']['absolute_rate_difference'])

    def test_absent_targeted_stratum_has_unknown_rate_and_malformed_field_fails(self):
        evaluate = importlib.import_module('evaluate').evaluate
        for name in ('conformance-r1.csv', 'event-log-r1.csv'):
            path = self.root / name
            path.write_text(path.read_text().replace('S3', 'OTHER').replace('S4', 'OTHER'))
        self.assertIsNone(evaluate(self.root)['cohorts']['r1']['targeted']['violation_rate'])
        compare = importlib.import_module('compare_lab_field').compare
        (self.root / 'bpic2019_results.json').write_text('{"overall":{"r2_viol":{"n_true":4,"n_applicable":3}}}')
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            compare(self.root)

    def test_scientific_is_requested_explicitly_and_uses_actual_cohort_counts(self):
        # The optional path is exercised when SciPy is present; the dependency-
        # absent environment must give a clear failure on explicit request.
        evaluate_module = importlib.import_module('evaluate')
        try:
            import scipy
        except ImportError:
            with self.assertRaisesRegex(RuntimeError, 'optional SciPy'):
                evaluate_module.evaluate(self.root, scientific=True)
        else:
            result = evaluate_module.evaluate(self.root, scientific=True)
            self.assertTrue(result['scientific']['available'])
            # Fixture targeted rows give [[1, 0], [0, 1]], not [[60, 0], [0, 60]].
            self.assertEqual(result['scientific']['fisher_p'], 1.0)
            self.assertIsNone(result['scientific']['welch_p'])

    def test_field_rates_come_from_counts_and_strata_stay_separate(self):
        compare = importlib.import_module('compare_lab_field').compare
        field = {'source_xes': '/private/machine/raw.xes',
                 'three_way_strata': {'after': {'r2_viol': {'n_true': 2, 'n_applicable': 5, 'rate': 0.99},
                                               'r3_viol': {'n_true': 0, 'n_applicable': 0, 'rate': 0}},
                                      'before': {'r2_viol': {'n_true': 0, 'n_applicable': 0}}}}
        path = self.root / 'bpic2019_results.json'
        path.write_text(json.dumps(field))
        result = compare(self.root)
        self.assertTrue(result['available'])
        self.assertEqual(result['strata']['three_way_after']['metrics']['r2_viol']['rate'], 0.4)
        self.assertIsNone(result['strata']['three_way_after']['metrics']['r3_viol']['rate'])
        self.assertIsNone(result['strata']['three_way_before']['metrics']['r2_viol']['rate'])
        self.assertFalse(result['contrasts'][0]['comparable'])
        field['three_way_strata']['after']['r2_viol']['n_true'] = 3
        path.write_text(json.dumps(field))
        self.assertEqual(compare(self.root)['strata']['three_way_after']['metrics']['r2_viol']['rate'], 0.6)
        self.assertNotIn('/private', json.dumps(result))

    def test_field_r3_definition_describes_monetary_worth_basis(self):
        definition = importlib.import_module('compare_lab_field').DEFINITIONS['r3_viol']
        self.assertIn('Cumulative net worth', definition)
        self.assertIn('maximum invoice', definition)
        self.assertIn('first PO', definition)
        self.assertIn('cumulative invoice/receipt item quantities', definition)

    def test_field_applicable_count_cannot_exceed_known_stratum_cases(self):
        stratum = importlib.import_module('compare_lab_field')._stratum
        with self.assertRaisesRegex(ValueError, 'n_applicable.*n_cases'):
            stratum({'n_cases': 1, 'r3_viol': {'n_true': 2, 'n_applicable': 2}})
        self.assertIsNone(stratum({'r3_viol': {'n_true': 2, 'n_applicable': 2}})['n_cases'])
        empty = stratum({'n_cases': 0, 'r3_viol': {'n_true': 0, 'n_applicable': 0}})
        self.assertEqual(empty['n_cases'], 0)
        self.assertIsNone(empty['metrics']['r3_viol']['rate'])

    def test_field_overall_uses_top_level_case_count_and_rejects_conflict(self):
        compare = importlib.import_module('compare_lab_field').compare
        path = self.root / 'bpic2019_results.json'
        source = {'n_cases': 3, 'overall': {'r3_viol': {'n_true': 1, 'n_applicable': 2}}}
        path.write_text(json.dumps(source))
        overall = compare(self.root)['strata']['overall']
        self.assertEqual(overall['n_cases'], 3)
        self.assertEqual(overall['metrics']['r3_viol']['n_applicable'], 2)
        source['overall']['n_cases'] = 2
        path.write_text(json.dumps(source))
        with self.assertRaisesRegex(ValueError, 'n_cases'):
            compare(self.root)
        del source['n_cases']
        path.write_text(json.dumps(source))
        self.assertEqual(compare(self.root)['strata']['overall']['n_cases'], 2)
        del source['overall']['n_cases']
        path.write_text(json.dumps(source))
        self.assertIsNone(compare(self.root)['strata']['overall']['n_cases'])

    def test_raw_field_offsets_are_normalized_and_fresh_results_are_versioned(self):
        analyzer = importlib.import_module('analyze_bpic2019')
        # These two event strings represent the same instant; dropping offsets
        # would invent a two-hour ordering difference.
        self.assertEqual(analyzer.parse_timestamp('2018-01-01T02:00:00+02:00'),
                         analyzer.parse_timestamp('2018-01-01T00:00:00Z'))
        raw = self.root / 'tiny.xes'
        raw.write_text('<log><trace><string key="concept:name" value="x"/><string key="Item Category" value="2-way match"/><event><string key="concept:name" value="Create Purchase Order Item"/><date key="time:timestamp" value="2018-01-01T00:00:00Z"/></event></trace></log>')
        _, result = analyzer.analyze(raw, self.root / 'cases.csv', self.root / 'bpic2019_results.json')
        self.assertEqual(result['source_xes'], 'tiny.xes')
        self.assertEqual(result['rule_version'], 'field-proxies-utc-v2')
        compare = importlib.import_module('compare_lab_field').compare
        self.assertEqual(compare(self.root)['rule_version'], 'field-proxies-utc-v2')
        build = importlib.import_module('build_dashboard').build
        payload = build(self.root, self.root / 'dashboard.json')
        source = next(item for item in payload['provenance']['sources'] if item['path'] == 'bpic2019_results.json')
        self.assertEqual(source['rule_version'], 'field-proxies-utc-v2')

    def test_missing_field_is_explicitly_unavailable(self):
        compare = importlib.import_module('compare_lab_field').compare
        result = compare(self.root)
        self.assertFalse(result['available'])
        self.assertEqual(result['strata'], {})

    def test_dashboard_is_deterministic_with_relative_hashed_sources(self):
        build = importlib.import_module('build_dashboard').build
        out = self.root / 'dashboard.json'
        payload = build(self.root, out)
        content = out.read_bytes()
        self.assertEqual(payload['lab']['cohorts']['r1']['overall']['violation_rate'], 0.5)
        self.assertFalse(payload['field']['available'])
        self.assertEqual(build(self.root, out), payload)
        self.assertEqual(out.read_bytes(), content)
        source = next(row for row in payload['provenance']['sources'] if row['path'] == 'conformance-r1.csv')
        self.assertEqual(source['sha256'], hashlib.sha256((self.root / source['path']).read_bytes()).hexdigest())
        self.assertEqual(source['rule_version'], 'v2')
        self.assertNotIn(str(self.root), content.decode())
        events = self.root / 'event-log-r1.csv'
        events.write_text(events.read_text().replace('a,Purchase Order,2026-01-01T16:00:00',
                                                    'a,Purchase Order,2026-01-01T04:00:00'))
        checker = importlib.import_module('check_conformance')
        checker.write_results(checker.load(events), self.root, 'r1')
        changed = build(self.root, out)
        self.assertEqual(changed['lab']['cohorts']['r1']['overall']['violation_rate'], 1.0)
        self.assertNotEqual(changed['provenance'], payload['provenance'])

    def test_imports_do_not_write_and_cli_runs_without_site_packages(self):
        # Hashes catch the previous compare module's data/comparison.csv import write.
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        code = 'import sys; sys.path.insert(0, %r); import evaluate, compare_lab_field, build_dashboard' % str(SRC)
        proc = subprocess.run([sys.executable, '-S', '-c', code], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in self.root.iterdir()}, before)
        for script in ('evaluate.py', 'compare_lab_field.py', 'build_dashboard.py'):
            out = self.root / (script + '.json')
            proc = subprocess.run([sys.executable, '-S', str(SRC / script), '--data-dir', str(self.root), '--out', str(out)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIsInstance(json.loads(out.read_text()), dict)


if __name__ == '__main__':
    unittest.main()
