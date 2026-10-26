"""Exercise real subprocess runs: catch canonical writes and unsafe reuse."""
import csv
import contextlib
import io
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch
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

    def test_default_workflow_preserves_historical_registry(self):
        # Catch a default rooted at the checked-in, incompatible v1 registry.
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory)
            shutil.copytree(ROOT / 'src', checkout / 'src')
            (checkout / 'data').mkdir()
            historical = (ROOT / 'data' / 'runs.csv').read_bytes()
            (checkout / 'data' / 'runs.csv').write_bytes(historical)
            result = subprocess.run(
                [sys.executable, str(checkout / 'src' / 'run_manager.py'),
                 '--n', '1', '--era', 'both', '--seed', '17', '--tag', 'default'],
                cwd=str(checkout), text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual((checkout / 'data' / 'runs.csv').read_bytes(), historical)
            self.assertEqual(list((checkout / 'data').iterdir()), [checkout / 'data' / 'runs.csv'])
            generated = checkout / 'output' / 'experiments'
            with (generated / 'runs.csv').open(newline='') as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row['run_id'] for row in rows], ['default-r1', 'default-r2'])
            for era in ('r1', 'r2'):
                self.assertTrue((generated / 'runs' / 'default' / ('summary-%s.csv' % era)).is_file())

    def test_incompatible_registry_rejected_before_reserving_or_generating(self):
        # Catch late rejection that consumes the tag and leaves partial output.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            historical = (ROOT / 'data' / 'runs.csv').read_bytes()
            (root / 'runs.csv').write_bytes(historical)
            for _ in range(2):
                result = self.invoke(root, '--n', '1', '--era', 'r1', '--seed', '1', '--tag', 'unused')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('incompatible', result.stderr.lower())
                self.assertNotIn('Traceback', result.stderr)
                self.assertEqual(list(root.iterdir()), [root / 'runs.csv'])
                self.assertEqual((root / 'runs.csv').read_bytes(), historical)

    def test_competing_run_is_busy_before_generation_during_header_initialization(self):
        # Force the exact interleaving: a published, empty runs.csv while its
        # creator is paused before writing the header. Keep real IO/generation.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            header_started, release_header = Event(), Event()
            real_open = Path.open

            def paused_open(path, mode='r', *args, **kwargs):
                handle = real_open(path, mode, *args, **kwargs)
                if path == root / 'runs.csv' and mode == 'x':
                    header_started.set()
                    if not release_header.wait(10):
                        handle.close()
                        raise AssertionError('header writer was not released')
                return handle

            arguments = ['--output-dir', str(root), '--n', '1', '--era', 'r1', '--seed', '1']
            with patch.object(Path, 'open', paused_open), contextlib.redirect_stdout(io.StringIO()):
                with ThreadPoolExecutor(max_workers=1) as executor:
                    first = executor.submit(run_manager.main, arguments + ['--tag', 'first'])
                    second_error = None
                    try:
                        self.assertTrue(header_started.wait(10), 'first run did not initialize registry')
                        try:
                            run_manager.main(arguments + ['--tag', 'second'])
                        except BaseException as exc:
                            second_error = exc
                    finally:
                        release_header.set()
                    first.result(timeout=10)
            self.assertIsInstance(second_error, SystemExit)
            self.assertIn('busy', str(second_error).lower())
            self.assertFalse((root / 'runs' / 'second').exists())
            # The lock must be released and the complete registry remain usable.
            result = self.invoke(root, '--n', '1', '--era', 'r1', '--seed', '2', '--tag', 'second')
            self.assertEqual(result.returncode, 0, result.stderr)
            with (root / 'runs.csv').open(newline='') as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row['run_id'] for row in rows], ['first-r1', 'second-r1'])
            self.assertTrue(all(row['rule_version'] == 'v2' and None not in row
                                and all(value is not None for value in row.values()) for row in rows))

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
