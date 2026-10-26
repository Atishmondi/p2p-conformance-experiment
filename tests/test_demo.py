"""End-to-end demo proves isolated, deterministic output without site packages."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DemoTests(unittest.TestCase):
    def test_fresh_roots_match_and_canonical_artifacts_are_immutable(self):
        # A generator/checker default path regression changes one of these bytes.
        canonical = {path: hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in (ROOT / 'data').iterdir() if path.suffix in ('.csv', '.json')}
        with tempfile.TemporaryDirectory() as temp:
            outputs = []
            for name in ('first', 'second'):
                out = Path(temp) / name
                proc = subprocess.run([sys.executable, '-S', str(ROOT / 'src' / 'demo.py'),
                                       '--output-dir', str(out), '--n', '2'],
                                      cwd=temp, capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                outputs.append({p.relative_to(out).as_posix(): p.read_bytes() for p in out.rglob('*') if p.is_file()})
                payload = json.loads((out / 'dashboard.json').read_text())
                self.assertEqual(payload['lab']['cohorts']['r1']['rule_version'], 'v2')
                self.assertEqual(payload['lab']['cohorts']['r1']['overall']['cases'], 12)
                self.assertEqual(payload['lab']['cohorts']['r1']['overall']['violating'], 6)
                self.assertEqual(payload['lab']['cohorts']['r1']['overall']['rules']['R3']['violating'], 4)
                self.assertEqual(payload['lab']['cohorts']['r2']['overall']['cases'], 6)
                self.assertTrue(payload['field']['available'])
            self.assertEqual(outputs[0], outputs[1])
            existing = Path(temp) / 'first'
            before = outputs[0]
            proc = subprocess.run([sys.executable, '-S', str(ROOT / 'src' / 'demo.py'), '--output-dir', str(existing)], capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual({p.relative_to(existing).as_posix(): p.read_bytes() for p in existing.rglob('*') if p.is_file()}, before)
        self.assertEqual({path: hashlib.sha256(path.read_bytes()).hexdigest() for path in canonical}, canonical)

    def test_without_field_source_is_explicit_and_nonpositive_n_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'demo'
            proc = subprocess.run([sys.executable, '-S', str(ROOT / 'src' / 'demo.py'), '--output-dir', str(out), '--n', '1', '--without-field'], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(json.loads((out / 'dashboard.json').read_text())['field']['available'])
            self.assertFalse((out / 'bpic2019_results.json').exists())
            invalid = Path(temp) / 'invalid'
            proc = subprocess.run([sys.executable, '-S', str(ROOT / 'src' / 'demo.py'), '--output-dir', str(invalid), '--n', '0'], capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse(invalid.exists())


if __name__ == '__main__':
    unittest.main()
