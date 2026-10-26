"""Exercise real subprocess runs: catch canonical writes and unsafe reuse."""
import csv
import contextlib
import io
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import run_manager


def digest_canonical():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (ROOT / 'data').glob('*.csv')}


class RunTests(unittest.TestCase):
    def invoke(self, root, *args):
        return subprocess.run([sys.executable, str(ROOT / 'src' / 'run_manager.py'),
                               '--output-dir', str(root)] + list(args),
                              cwd=str(ROOT), text=True, capture_output=True)

    def test_explicit_root_isolated_seeded_runs_and_registry(self):
        before = digest_canonical()
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / 'first', Path(directory) / 'second'
            for root in (first, second):
                result = self.invoke(root, '--n', '2', '--seed', '17', '--tag', 'fixed')
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                with (root / 'runs.csv').open(newline='') as handle:
                    records = list(csv.DictReader(handle))
                self.assertEqual([row['run_id'] for row in records], ['fixed-r1', 'fixed-r2'])
                self.assertEqual([row['cases'] for row in records], ['12', '6'])
                self.assertEqual([row['viol_rate'] for row in records], ['0.5000', '0.0000'])
                self.assertTrue(all(row['rule_version'] == 'v2' for row in records))
                self.assertTrue(all(row['not_evaluable'] == '0' for row in records))
            for era in ('r1', 'r2'):
                for prefix in ('event-log', 'conformance', 'summary'):
                    filename = '%s-%s.csv' % (prefix, era)
                    self.assertEqual((first / 'runs' / 'fixed' / filename).read_bytes(),
                                     (second / 'runs' / 'fixed' / filename).read_bytes())
            result = self.invoke(first, '--n', '1', '--era', 'r1', '--seed', '99', '--tag', 'other')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((second / 'runs' / 'other').exists())
        self.assertEqual(digest_canonical(), before)

    def test_duplicate_tag_fails_without_modifying_existing_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.invoke(root, '--n', '1', '--era', 'r1', '--seed', '1', '--tag', 'once')
            self.assertEqual(result.returncode, 0, result.stderr)
            before = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()}
            result = self.invoke(root, '--n', '3', '--era', 'r1', '--seed', '2', '--tag', 'once')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('exists', result.stderr.lower())
            after = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()}
            self.assertEqual(after, before)

    def test_zero_and_negative_case_counts_rejected_before_writes(self):
        for count in ('0', '-1'):
            with self.subTest(count=count), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                run_manager.parse_args(['--n', count])

    def test_unsafe_tag_rejected_before_writes(self):
        for tag in ('../escape', '/tmp/escape', 'a/b', 'a\\b', '..', '.', ''):
            with self.subTest(tag=tag), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                run_manager.parse_args(['--tag', tag])

    def test_default_run_ids_do_not_collide(self):
        self.assertEqual(len({run_manager.default_tag() for _ in range(30)}), 30)

    def test_metrics_keep_unknown_cases_out_of_compliant_denominator(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            conf, log = root / 'conformance.csv', root / 'events.csv'
            conf.write_text('case_id,violations,status,cycle_days\n'
                            'C1,OK,compliant,1\nC2,R3,violating,2\nC3,,not_evaluable,3\n')
            log.write_text('case_id,activity\nC1,Payment\nC2,Payment\nC3,Payment\n')
            result = run_manager.compute_metrics(conf, log)
            self.assertIsInstance(result, dict)
            self.assertEqual({key: result[key] for key in ('cases', 'events', 'compliant', 'violating',
                                                          'not_evaluable', 'evaluated_cases')},
                             {'cases': 3, 'events': 3, 'compliant': 1, 'violating': 1,
                              'not_evaluable': 1, 'evaluated_cases': 2})
            self.assertEqual(result['viol_rate'], 0.5)
            self.assertEqual(result['mean_cycle'], 2.0)


if __name__ == '__main__':
    unittest.main()
