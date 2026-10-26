"""Boundary tests against hand-authored recorded-action rows, not an Odoo assertion."""
import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import validate_erp_export as adapter
import check_conformance as checker

FIELDS = ['case_id', 'activity', 'timestamp', 'event_id', 'source_model', 'source_id',
          'source_action', 'timestamp_kind', 'product_id', 'uom', 'invoice_event_id',
          'qty_ordered', 'qty_received', 'qty_invoiced', 'scenario', 'resource', 'po_id']


def row(activity, n, **changes):
    result = dict.fromkeys(FIELDS, '')
    result.update(case_id='A', activity=activity, timestamp=f'2026-01-{n:02d}T10:00:00+00:00',
                  event_id=f'E{n}', source_model='audit.action', source_id=str(n),
                  source_action='recorded transition', timestamp_kind='recorded',
                  product_id='P1', uom='Units', scenario='S1')
    result.update(changes)
    return result


def good_rows():
    return [row('Purchase Request', 1), row('Purchase Request Approval', 2),
            row('Purchase Order', 3, qty_ordered='10'),
            row('Goods Receipt', 4, qty_received='4'),
            row('Goods Receipt', 5, qty_received='6'),
            row('Vendor Invoice', 6, qty_invoiced='10'),
            row('Payment', 7, invoice_event_id='E6')]


class ExportTests(unittest.TestCase):
    def write(self, directory, rows):
        path = Path(directory) / 'input.csv'
        with path.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_valid_export_preserves_sources_and_event_delta_checker_result(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, list(reversed(good_rows())))
            rows = adapter.validate_export(path)
            self.assertEqual([r['event_id'] for r in rows], [f'E{i}' for i in range(1, 8)])
            self.assertEqual(rows[-1]['invoice_event_id'], 'E6')
            self.assertEqual(rows[3]['source_id'], '4')
            self.assertEqual(checker.check_case(checker.load(path)['A'])[0]['R3'], False)
            output = Path(directory) / 'normalized.csv'
            adapter.write_export(rows, output)
            self.assertEqual(adapter.validate_export(output), rows)
            first = output.read_bytes()
            adapter.write_export(adapter.validate_export(self.write(directory, good_rows())), output)
            self.assertEqual(output.read_bytes(), first)
            with output.open(newline='') as handle:
                normalized = list(csv.DictReader(handle))
            self.assertEqual(normalized[3]['qty_received'], '4')
            self.assertEqual(normalized[-1]['source_model'], 'audit.action')

    def test_invalid_source_and_timestamp_evidence_rejected(self):
        for key, value in [('source_model', ''), ('source_id', ''), ('source_action', ''),
                           ('event_id', ''), ('timestamp_kind', 'occurred'),
                           ('timestamp_kind', 'both'), ('timestamp', '2026-01-01'),
                           ('timestamp', '2026-01-01T10:00:00')]:
            with self.subTest(key=key, value=value), tempfile.TemporaryDirectory() as directory:
                rows = good_rows()
                rows[0][key] = value
                with self.assertRaises(ValueError):
                    adapter.validate_export(self.write(directory, rows))

    def test_duplicates_mixed_grain_and_unsupported_activity_rejected(self):
        variants = [dict(event_id='E2'), dict(source_id='2'), dict(product_id='P2'),
                    dict(uom='Kg'), dict(activity='Credit Note'), dict(activity='Unknown')]
        for change in variants:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                rows = good_rows()
                rows[0].update(change)
                with self.assertRaises(ValueError):
                    adapter.validate_export(self.write(directory, rows))

    def test_event_deltas_and_exact_invoice_link_required(self):
        for index, change in [(3, dict(qty_received='')), (5, dict(qty_invoiced='')),
                              (6, dict(invoice_event_id='')), (6, dict(invoice_event_id='E5')),
                              (6, dict(invoice_event_id='other'))]:
            with self.subTest(index=index, change=change), tempfile.TemporaryDirectory() as directory:
                rows = good_rows()
                rows[index].update(change)
                with self.assertRaises(ValueError):
                    adapter.validate_export(self.write(directory, rows))
        with tempfile.TemporaryDirectory() as directory:
            rows = good_rows()
            rows[6]['case_id'] = 'B'
            with self.assertRaises(ValueError):
                adapter.validate_export(self.write(directory, rows))

    def test_invalid_cli_leaves_existing_output_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            rows = good_rows()
            rows[3]['qty_received'] = ''
            path = self.write(directory, rows)
            out = Path(directory) / 'normalized.csv'
            out.write_bytes(b'prior result\n')
            process = subprocess.run([sys.executable, str(ROOT / 'src/validate_erp_export.py'),
                                      str(path), '--out', str(out)], capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertEqual(out.read_bytes(), b'prior result\n')
            self.assertIn('qty_received', process.stderr)

    def test_empty_export_rejected_without_creating_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, [])
            output = Path(directory) / 'missing.csv'
            process = subprocess.run([sys.executable, str(ROOT / 'src/validate_erp_export.py'),
                                      str(path), '--out', str(output)], capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertFalse(output.exists())

    def test_fixture_has_literal_compliant_and_excess_results(self):
        path = ROOT / 'examples/erp-recorded-events.csv'
        rows = adapter.validate_export(path)
        self.assertEqual(len(rows), 14)
        cases = checker.load(path)
        self.assertEqual(set(cases), {'A', 'B'})
        self.assertEqual(checker.check_case(cases['A'])[0],
                         {'R1': False, 'R2': False, 'R3': False, 'R4': False, 'R5': False})
        self.assertEqual(checker.check_case(cases['B'])[0]['R3'], True)


if __name__ == '__main__':
    unittest.main()
