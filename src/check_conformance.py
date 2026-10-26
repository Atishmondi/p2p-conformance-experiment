"""Version 2 P2P checks over recorded events; standard library only.

True means a proven violation, False evaluated compliance, None insufficient
recorded evidence. See docs/event-contract.md for quantities and ordering.
"""
import argparse
import csv
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

RULE_VERSION = 'v2'
RULES = ['R1', 'R2', 'R3', 'R4', 'R5']
NORM = ('Purchase Request', 'Purchase Request Approval', 'Purchase Order',
        'Goods Receipt', 'Vendor Invoice', 'Payment')
QUANTITIES = ('qty_ordered', 'qty_received', 'qty_invoiced')
REQUIRED = ('case_id', 'activity', 'timestamp')
APPROVALS = {'Purchase Request Approval', 'Purchase Request Approval (re-approval)'}


def parse_ts(value):
    """Require an ISO datetime, retaining naive values and normalizing aware UTC."""
    if not isinstance(value, str) or not re.search(r'[Tt ]\d{2}:\d{2}', value):
        raise ValueError('timestamp must be an ISO datetime with recorded time')
    try:
        timestamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('invalid timestamp: %r' % value) from exc
    return timestamp.astimezone(timezone.utc) if timestamp.tzinfo is not None else timestamp


def _quantity(value, field):
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError('%s must be a finite nonnegative decimal' % field) from exc
    if not result.is_finite() or result < 0:
        raise ValueError('%s must be a finite nonnegative decimal' % field)
    return result


def normalize_events(events):
    """Copy and validate one case without inventing missing quantities or order."""
    normalized, identities, anonymous = [], set(), set()
    awareness, products, units, cases = set(), set(), set(), set()
    for original in events:
        row = dict(original)
        for field in ('case_id', 'activity'):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError('missing required value: %s' % field)
            row[field] = row[field].strip()
        cases.add(row['case_id'])
        if len(cases) > 1:
            raise ValueError('check_case requires events from one case')
        activity = row['activity'].lower()
        if any(term in activity for term in ('return', 'revers', 'refund', 'credit note', 'credit memo', 'cancel')):
            raise ValueError('unsupported return/reversal activity: %s' % row['activity'])
        for flag in ('is_return', 'is_reversal'):
            if str(row.get(flag, '')).strip().lower() not in ('', '0', 'false', 'none'):
                raise ValueError('unsupported return/reversal flag: %s' % flag)
        timestamp = row.get('timestamp')
        if timestamp is None and isinstance(row.get('_ts'), datetime):
            timestamp = row['_ts'].isoformat()
        row['_ts'] = parse_ts(timestamp)
        awareness.add(row['_ts'].tzinfo is not None)
        if len(awareness) > 1:
            raise ValueError('mixed naive/aware timestamps within case %s' % row['case_id'])
        for field in QUANTITIES:
            row[field] = _quantity(row.get(field), field)
        for field, values in (('product_id', products), ('unit', units)):
            value = str(row.get(field) or '').strip()
            if value:
                values.add(value)
            if len(values) > 1:
                raise ValueError('conflicting %s within case %s' % (field, row['case_id']))
        identity = str(row.get('event_id') or '').strip()
        if identity:
            if identity in identities:
                raise ValueError('duplicate event_id: %s' % identity)
            identities.add(identity)
        else:
            fingerprint = tuple(sorted((key, str(value)) for key, value in row.items()
                                       if key not in ('_ts', 'event_id')))
            if fingerprint in anonymous:
                raise ValueError('duplicate event without event_id in case %s' % row['case_id'])
            anonymous.add(fingerprint)
        normalized.append(row)
    return sorted(normalized, key=lambda row: row['_ts'])


def load(path):
    cases = defaultdict(list)
    identities = set()
    with open(path, newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        missing = set(REQUIRED) - set(reader.fieldnames or ())
        if missing:
            raise ValueError('missing required CSV columns: %s' % ', '.join(sorted(missing)))
        for line, row in enumerate(reader, 2):
            if None in row or any(row.get(field) is None for field in REQUIRED):
                raise ValueError('malformed CSV row at line %s' % line)
            identity = (row.get('event_id') or '').strip()
            if identity and identity in identities:
                raise ValueError('duplicate event_id at line %s: %s' % (line, identity))
            if identity:
                identities.add(identity)
            cases[row['case_id']].append(row)
    return {case: normalize_events(events) for case, events in cases.items()}


def _combine(results):
    results = list(results)
    if any(result is True for result in results):
        return True
    return None if not results or any(result is None for result in results) else False


def _precedence(predecessors, targets):
    if not predecessors or not targets:
        return None
    results = []
    for target in targets:
        if any(previous['_ts'] < target['_ts'] for previous in predecessors):
            results.append(False)
        elif any(previous['_ts'] == target['_ts'] for previous in predecessors):
            results.append(None)
        else:
            results.append(True)
    return _combine(results)


def _sum_known(values):
    values = [value for value in values if value is not None]
    if not values:
        return Decimal(0)
    # Decimal addition must not round long but valid source quantities.
    width = max(value.adjusted() for value in values) - min(value.as_tuple().exponent for value in values)
    with localcontext() as context:
        context.prec = max(28, width + len(str(len(values))) + 3)
        return sum(values, Decimal(0))


def _total(events, field):
    values = [event[field] for event in events]
    return None if not values or None in values else _sum_known(values)


def _quantity_rule(receipts, invoices):
    if not receipts or not invoices:
        return None
    results = []
    for timestamp in sorted({event['_ts'] for event in invoices}):
        billed = [event['qty_invoiced'] for event in invoices if event['_ts'] <= timestamp]
        available = [event['qty_received'] for event in receipts if event['_ts'] <= timestamp]
        prior = [event['qty_received'] for event in receipts if event['_ts'] < timestamp]
        minimum_billed = _sum_known(billed)
        # Even allowing every same-time receipt first, excess is a violation.
        if None not in available and minimum_billed > _sum_known(available):
            results.append(True)
        elif None in billed or None in available:
            results.append(None)
        elif minimum_billed <= _sum_known(prior):
            results.append(False)
        else:
            results.append(None)  # result depends on order within a timestamp tie
    return _combine(results)


def _modification_rule(modifications, approvals, purchase_orders):
    if not modifications:
        return False
    results = []
    for modification in modifications:
        following = [po for po in purchase_orders if po['_ts'] >= modification['_ts']]
        if not following or not approvals:
            results.append(None)
            continue
        boundary = min(po['_ts'] for po in following)
        if boundary == modification['_ts']:
            results.append(None)
        elif any(modification['_ts'] < approval['_ts'] < boundary for approval in approvals):
            results.append(False)
        elif any(modification['_ts'] <= approval['_ts'] <= boundary for approval in approvals):
            results.append(None)
        else:
            results.append(True)
    return _combine(results)


def check_case(evs):
    """Return (rules, variant, cycle_days, approval_wait, receipt_wait, qr, qi).

    Rules use True/False/None. qr and qi are event-delta totals (Decimal or
    None); performance values are days (float or None for missing evidence).
    """
    evs = normalize_events(evs)
    by_activity = defaultdict(list)
    for event in evs:
        by_activity[event['activity']].append(event)
    approvals = [event for event in evs if event['activity'] in APPROVALS]
    purchase_orders = by_activity['Purchase Order']
    receipts, invoices = by_activity['Goods Receipt'], by_activity['Vendor Invoice']
    rules = {
        'R1': _precedence(approvals, purchase_orders),
        'R2': _precedence(receipts, invoices),
        'R3': _quantity_rule(receipts, invoices),
        'R4': _modification_rule(by_activity['PO Modification'], approvals, purchase_orders),
        'R5': _precedence(invoices, by_activity['Payment']),
    }
    cycle = (evs[-1]['_ts'] - evs[0]['_ts']).total_seconds() / 86400 if evs else None
    approval_wait = (approvals[0]['_ts'] - evs[0]['_ts']).total_seconds() / 86400 if approvals else None
    receipt_wait = ((receipts[0]['_ts'] - purchase_orders[0]['_ts']).total_seconds() / 86400
                    if receipts and purchase_orders else None)
    return (rules, tuple(event['activity'] for event in evs), cycle, approval_wait,
            receipt_wait, _total(receipts, 'qty_received'), _total(invoices, 'qty_invoiced'))


def validate_tag(tag):
    if not isinstance(tag, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', tag) or tag in ('.', '..'):
        raise ValueError('tag must be a safe single path component (letters, numbers, dot, dash, underscore)')
    return tag


def _mean(values):
    values = [value for value in values if value is not None]
    return statistics.fmean(values) if values else ''


def write_results(cases, output_dir, tag):
    """Write v2 CSVs; return {'conformance': Path, 'summary': Path}."""
    validate_tag(tag)
    output_dir = Path(output_dir)
    rows, groups = [], defaultdict(list)
    for case_id in sorted(cases):
        events = cases[case_id]
        rules, variant, cycle, approval_wait, receipt_wait, qr, qi = check_case(events)
        failed = [rule for rule in RULES if rules[rule] is True]
        unknown = [rule for rule in RULES if rules[rule] is None]
        status = 'violating' if failed else ('not_evaluable' if unknown else 'compliant')
        scenario = events[0].get('scenario', '') if events else ''
        rows.append([case_id, scenario, '->'.join(activity[:12] for activity in variant),
                     ';'.join(failed) if failed else ('OK' if status == 'compliant' else ''),
                     cycle, qr, qi, ';'.join(unknown), status, RULE_VERSION])
        groups[scenario].append((rules, status, cycle, approval_wait, receipt_wait))
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {'conformance': output_dir / ('conformance-%s.csv' % tag),
             'summary': output_dir / ('summary-%s.csv' % tag)}
    with paths['conformance'].open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['case_id', 'scenario', 'variant_short', 'violations', 'cycle_days',
                         'qty_received', 'qty_invoiced', 'not_evaluable', 'status', 'rule_version'])
        writer.writerows(rows)
    with paths['summary'].open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['scenario', 'n_cases', 'conformance_rate', 'mean_cycle', 'median_cycle',
                         'mean_approval_wait', 'mean_receipt_wait'] + [rule + '_viol' for rule in RULES] +
                        ['compliant', 'violating', 'not_evaluable', 'evaluated_cases', 'rule_version'] +
                        [rule + '_not_evaluable' for rule in RULES])
        for scenario in sorted(groups):
            records = groups[scenario]
            statuses = Counter(record[1] for record in records)
            evaluated = statuses['compliant'] + statuses['violating']
            cycles = [record[2] for record in records if record[2] is not None]
            writer.writerow([scenario, len(records), statuses['compliant'] / evaluated if evaluated else '',
                             _mean(cycles), statistics.median(cycles) if cycles else '',
                             _mean([record[3] for record in records]), _mean([record[4] for record in records])] +
                            [sum(record[0][rule] is True for record in records) for rule in RULES] +
                            [statuses['compliant'], statuses['violating'], statuses['not_evaluable'], evaluated, RULE_VERSION] +
                            [sum(record[0][rule] is None for record in records) for rule in RULES])
    return paths


def main(argv=None):
    base = Path(__file__).resolve().parents[1] / 'data'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', type=Path, default=base / 'event-log-r1.csv')
    parser.add_argument('--output-dir', type=Path, default=base)
    parser.add_argument('--tag', default=None)
    args = parser.parse_args(argv)
    tag = args.tag or ('r1' if 'r1' in args.input.name else ('r2' if 'r2' in args.input.name else args.input.stem))
    try:
        cases = load(args.input)
        outputs = write_results(cases, args.output_dir, tag)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print('Rule version: %s; Cases: %s; Events: %s' % (RULE_VERSION, len(cases), sum(map(len, cases.values()))))
    for path in outputs.values():
        print('Wrote %s' % path)
    return outputs


if __name__ == '__main__':
    main()
