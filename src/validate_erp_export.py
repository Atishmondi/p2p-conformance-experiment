"""Fail-closed boundary for audited, recorded P2P events (not an ERP extractor).

Syntactically valid source IDs and timestamps do not attest authentic history.
The operator must separately verify audit instrumentation and source records.
"""
import argparse
import csv
import os
import tempfile
from datetime import timezone
from pathlib import Path

import check_conformance as checker

REQUIRED = ('case_id', 'activity', 'timestamp', 'event_id', 'source_model',
            'source_id', 'source_action', 'timestamp_kind', 'product_id', 'uom')
OPTIONAL = ('invoice_event_id', 'qty_ordered', 'qty_received', 'qty_invoiced',
            'scenario', 'resource', 'vendor', 'po_id')
COLUMNS = REQUIRED + OPTIONAL
SOURCE_ACTIONS = {
    'Purchase Request': 'request_submitted',
    'Purchase Request Approval': 'request_approved',
    'Purchase Request Approval (re-approval)': 'request_reapproved',
    'PO Modification': 'po_modified',
    'Purchase Order': 'po_confirmed',
    'Goods Receipt': 'receipt_validated',
    'Vendor Invoice': 'vendor_bill_posted',
    'Payment': 'payment_registered',
}


def validate_export(path: Path) -> list:
    """Return time/case/ID sorted normalized rows, or raise ValueError.

    Every source_model/source_id pair must identify one distinct recorded action.
    An invoice_event_id is an exact same-case invoice-event link, not a settlement proof.
    """
    rows = []
    event_ids, sources, grains = set(), set(), {}
    with Path(path).open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        if len(header) != len(set(header)) or not set(REQUIRED).issubset(header) or set(header) - set(COLUMNS):
            raise ValueError('invalid export columns: require %s; optional %s' % (REQUIRED, OPTIONAL))
        for line, original in enumerate(reader, 2):
            if None in original or any(value is None for value in original.values()):
                raise ValueError('malformed row at line %d' % line)
            row = {key: (original.get(key) or '').strip() for key in COLUMNS}
            for key in REQUIRED:
                if not row[key]:
                    raise ValueError('missing %s at line %d' % (key, line))
            if row['timestamp_kind'] != 'recorded':
                raise ValueError('timestamp_kind must be recorded at line %d' % line)
            if row['activity'] not in SOURCE_ACTIONS:
                raise ValueError('unsupported activity at line %d: %s' % (line, row['activity']))
            if row['source_action'] != SOURCE_ACTIONS[row['activity']]:
                raise ValueError('unsupported or mismatched source_action at line %d: %s'
                                 % (line, row['source_action']))
            stamp = checker.parse_ts(row['timestamp'])
            if stamp.tzinfo is None:
                raise ValueError('recorded timestamp must have timezone at line %d' % line)
            row['timestamp'] = stamp.astimezone(timezone.utc).isoformat()
            for key in ('qty_ordered', 'qty_received', 'qty_invoiced'):
                value = checker._quantity(row[key], key)
                row[key] = str(value) if value is not None else ''
            if row['activity'] == 'Goods Receipt' and not row['qty_received']:
                raise ValueError('qty_received required on Goods Receipt at line %d' % line)
            if row['activity'] == 'Vendor Invoice' and not row['qty_invoiced']:
                raise ValueError('qty_invoiced required on Vendor Invoice at line %d' % line)
            for activity, field in (('Purchase Order', 'qty_ordered'),
                                    ('Goods Receipt', 'qty_received'),
                                    ('Vendor Invoice', 'qty_invoiced')):
                if row['activity'] != activity and row[field]:
                    raise ValueError('%s only allowed on %s at line %d' % (field, activity, line))
            if row['activity'] != 'Payment' and row['invoice_event_id']:
                raise ValueError('invoice_event_id only allowed on Payment at line %d' % line)
            if row['activity'] == 'Payment' and not row['invoice_event_id']:
                raise ValueError('invoice_event_id required on Payment at line %d' % line)
            identity = row['event_id']
            source = (row['source_model'], row['source_id'])
            if identity in event_ids or source in sources:
                raise ValueError('duplicate event_id or source action at line %d' % line)
            event_ids.add(identity)
            sources.add(source)
            grain = (row['product_id'], row['uom'])
            previous = grains.setdefault(row['case_id'], grain)
            if previous != grain:
                raise ValueError('mixed product_id/uom grain in case %s' % row['case_id'])
            rows.append(row)
    if not rows:
        raise ValueError('empty recorded-event export')
    invoices = {row['event_id']: row['case_id'] for row in rows if row['activity'] == 'Vendor Invoice'}
    for row in rows:
        if row['activity'] == 'Payment' and invoices.get(row['invoice_event_id']) != row['case_id']:
            raise ValueError('unmapped or cross-case payment invoice_event_id: %s' % row['event_id'])
    return sorted(rows, key=lambda row: (row['case_id'], row['timestamp'], row['event_id']))


def write_export(rows, path: Path) -> None:
    """Atomically write validated normalized rows with fixed column order."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='',
                                         dir=path.parent, prefix='.erp-export-',
                                         delete=False) as handle:
            temporary = Path(handle.name)
            writer = csv.DictWriter(handle, COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--out', required=True, type=Path, help='normalized checker-compatible CSV')
    args = parser.parse_args(argv)
    try:
        rows = validate_export(args.input)
        write_export(rows, args.out)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print('Validated %d source-linked recorded events into %s' % (len(rows), args.out))
    return rows


if __name__ == '__main__':
    main()
