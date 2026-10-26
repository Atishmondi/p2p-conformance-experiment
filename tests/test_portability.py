"""Portable bundle boundaries: actual source bytes, HTTP, and changed inputs."""
import csv
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


class PortabilityTests(unittest.TestCase):
    def test_site_can_refresh_its_own_template_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / 'repo'
            shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns('.git', '__pycache__', 'output', 'BPI_Challenge_2019.xes'))
            out = Path(temp) / 'run'
            proc = subprocess.run([sys.executable, '-S', str(repo / 'src/demo.py'), '--output-dir', str(out), '--n', '1'],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            proc = subprocess.run([sys.executable, '-S', str(repo / 'src/build_dashboard.py'), '--data-dir', str(out),
                                   '--out', str(out / 'dashboard.json'), '--site-dir', str(repo / 'webpage')],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_fresh_copy_serves_demo_and_optional_field_is_absent(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / 'repo'
            shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns('.git', '__pycache__', 'output', 'BPI_Challenge_2019.xes'))
            shutil.rmtree(repo / 'data')
            (repo / 'data').mkdir()
            out = Path(temp) / 'run'
            proc = subprocess.run([sys.executable, '-S', str(repo / 'src/demo.py'), '--output-dir', str(out), '--n', '1', '--without-field'],
                                  cwd=temp, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            web = out / 'webpage'
            payload = json.loads((web / 'data.json').read_text())
            self.assertFalse(payload['field']['available'])
            self.assertEqual(payload['lab']['cohorts']['r1']['overall']['cases'], 6)
            self.assertTrue(payload['examples']['r1'])
            self.assertEqual(payload['examples']['r1'][0]['rule_version'], 'v2')
            for example in payload['examples']['r1'] + payload['examples']['r2']:
                for event in example['trace']:
                    if event['activity'] != 'Goods Receipt':
                        self.assertEqual(event['qty_received'], '')
                    if event['activity'] != 'Vendor Invoice':
                        self.assertEqual(event['qty_invoiced'], '')
            for name in ('erp-pilot.md', 'event-contract.md'):
                self.assertTrue((web / 'docs' / name).is_file())
                for target in re.findall(r'\]\(([^)]+)\)', (web / 'docs' / name).read_text()):
                    if not target.startswith(('http:', 'https:', '#')):
                        self.assertTrue((web / 'docs' / target.split('#')[0]).is_file(), target)
            self.assertNotIn(str(repo), (web / 'data.json').read_text())
            self.assertNotIn(str(out), (web / 'data.json').read_text())
            for source in payload['provenance']['sources']:
                self.assertEqual(hashlib.sha256((web / source['download']).read_bytes()).hexdigest(), source['sha256'])
            class Handler(SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=str(web), **kwargs)
                def log_message(self, *_):
                    pass
            try:
                server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            except PermissionError:
                self.skipTest('sandbox denies loopback listening; HTTP assertions run in CI')
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            self.addCleanup(server.server_close)
            self.addCleanup(thread.join)
            self.addCleanup(server.shutdown)
            base = 'http://127.0.0.1:%s/' % server.server_port
            for name in ('index.html', 'app.js', 'styles.css', 'data.json'):
                with urlopen(base + name) as response:
                    self.assertEqual(response.status, 200)
                    self.assertTrue(response.read())
            for source in payload['provenance']['sources']:
                with urlopen(base + source['download']) as response:
                    self.assertEqual(hashlib.sha256(response.read()).hexdigest(), source['sha256'])

    def test_rebuild_rejects_stale_verdict_then_accepts_regenerated_checker_output(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'run'
            proc = subprocess.run([sys.executable, '-S', str(ROOT / 'src/demo.py'), '--output-dir', str(out), '--n', '1'],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            original = json.loads((out / 'webpage/data.json').read_text())
            dashboard_before = (out / 'dashboard.json').read_bytes()
            published_event_before = (out / 'webpage/artifacts/event-log-r1.csv').read_bytes()
            source = out / 'event-log-r1.csv'
            with source.open(newline='') as f:
                rows = list(csv.DictReader(f))
            altered = rows[0]['case_id']
            next(row for row in rows if row['case_id'] == altered and row['activity'] == 'Vendor Invoice')['qty_invoiced'] = '99999'
            with source.open('w', newline='') as f:
                writer = csv.DictWriter(f, rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            proc = subprocess.run([sys.executable, '-S', str(ROOT / 'src/build_dashboard.py'), '--data-dir', str(out),
                                   '--out', str(out / 'dashboard.json'), '--site-dir', str(out / 'webpage')],
                                  capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn('conformance', proc.stderr)
            self.assertEqual(json.loads((out / 'webpage/data.json').read_text()), original)
            self.assertEqual((out / 'dashboard.json').read_bytes(), dashboard_before)
            self.assertEqual((out / 'webpage/artifacts/event-log-r1.csv').read_bytes(), published_event_before)
            proc = subprocess.run([sys.executable, '-S', str(ROOT / 'src/check_conformance.py'), str(source),
                                   '--output-dir', str(out), '--tag', 'r1'], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            proc = subprocess.run([sys.executable, '-S', str(ROOT / 'src/build_dashboard.py'), '--data-dir', str(out),
                                   '--out', str(out / 'dashboard.json'), '--site-dir', str(out / 'webpage')],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            changed = json.loads((out / 'webpage/data.json').read_text())
            self.assertEqual(changed['lab']['cohorts']['r1']['overall']['violating'], original['lab']['cohorts']['r1']['overall']['violating'] + 1)
            example = next(c for c in changed['examples']['r1'] if c['case_id'] == altered)
            self.assertEqual(example['violations'], ['R3'])
            source_record = next(s for s in changed['provenance']['sources'] if s['path'] == 'conformance-r1.csv')
            self.assertEqual(hashlib.sha256((out / 'webpage' / source_record['download']).read_bytes()).hexdigest(), source_record['sha256'])

    def test_manual_conformance_edit_and_canonical_field_source_are_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'run'
            proc = subprocess.run([sys.executable, '-S', str(ROOT / 'src/demo.py'), '--output-dir', str(out), '--n', '1'],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            original = (out / 'webpage/data.json').read_bytes()
            path = out / 'conformance-r1.csv'
            path.write_text(path.read_text().replace(',OK,', ',R1,').replace(',compliant,v2', ',violating,v2'))
            proc = subprocess.run([sys.executable, '-S', str(ROOT / 'src/build_dashboard.py'), '--data-dir', str(out),
                                   '--out', str(out / 'dashboard.json'), '--site-dir', str(out / 'webpage')],
                                  capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual((out / 'webpage/data.json').read_bytes(), original)
            canonical = Path(temp) / 'canonical'
            proc = subprocess.run([sys.executable, '-S', str(ROOT / 'src/build_dashboard.py'), '--data-dir', str(ROOT / 'data'),
                                   '--out', str(canonical / 'dashboard.json'), '--site-dir', str(canonical / 'webpage')],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            field = canonical / 'webpage/artifacts/bpic2019_results.json'
            self.assertNotIn(str(ROOT), field.read_text())
            self.assertFalse(Path(json.loads(field.read_text())['source_xes']).is_absolute())
            payload = json.loads((canonical / 'webpage/data.json').read_text())
            record = next(s for s in payload['provenance']['sources'] if s['path'] == field.name)
            self.assertEqual(record['sha256'], hashlib.sha256(field.read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
