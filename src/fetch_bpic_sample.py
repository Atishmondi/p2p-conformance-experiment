"""Fetch a SMALL public BPIC-2019-derived sample, else build a lab proxy.

Real P2P dataset: BPI Challenge 2019, 4TU DOI
  10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1,
  file BPI_Challenge_2019.xes (728MB -- DO NOT download the full file).

Strategy:
  1. Try SMALL public candidates only (<5MB each) via urllib with 60s
     timeout (e.g. pm4py sample XES or a <5MB mirror CSV). Size-guard via
     Content-Length header + capped read. Any oversize counts as failure.
  2. On ANY failure (network, HTTP, size, parse), fall back to building
     data/bpic_sample.csv locally from data/event-log-r1.csv (first 300
     events) remapped to real BPIC column names (documented approximate
     mapping below).
  3. EITHER WAY write data/bpic_sample.csv with <=300 rows and print
     REAL_DOWNLOAD or LAB_PROXY mode token.

Lab-proxy APPROXIMATE mapping (documented; not real BPIC data):
  case_concept = po_id + "_1"  (BPIC case concept:name is
    PurchasingDocument_Item composite; lab has 1 line-item per PO so
    item suffix is fixed to 1)
  activity: lab -> BPIC event concept:name approx:
    Purchase Request          -> Create Purchase Requisition Item
    Purchase Request Approval -> Change Approval for Purchase Order
      (approval-gate proxy; no exact BPIC equivalent in happy path)
    Purchase Order            -> Create Purchase Order Item
    Goods Receipt             -> Record Goods Receipt
    Vendor Invoice            -> Record Invoice Receipt
    Payment                   -> Clear Invoice
    PO Modification           -> Change Quantity (rework proxy)
  event_time = timestamp (BPIC time:timestamp)
  user = resource (BPIC User == org:resource)
  vendor = vendor (BPIC case Vendor)
  document = po_id (BPIC case Purchasing Document)
  item_category by scenario (BPIC case Item Category approx; lab has no
    native Item Category, so normative/timing scenarios map to the
    after-GR policy and the slow-approval/rework scenarios map to the
    before-GR policy to exercise both 3-way variants):
    S1,S2,S3,S4 -> 3-way match, invoice after GR
      (S3 order violates R2 under this policy by design)
    S5,S6       -> 3-way match, invoice before GR
  net_value = qty_ordered * 100 (atomic EUR proxy; BPIC Cumulative net
    worth is cumulative per case and linearly anonymized, so this is a
    scale proxy only)
Output columns (8):
  case_concept,activity,event_time,user,vendor,document,item_category,net_value
"""

import csv
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

TIMEOUT = 60  # seconds, per spec (urllib + 60s timeout)
MAX_BYTES = 5 * 1024 * 1024  # <5MB mirror guard; never pull the 728MB XES
MAX_ROWS = 300

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOCAL_SRC = DATA_DIR / "event-log-r1.csv"
OUT_PATH = DATA_DIR / "bpic_sample.csv"

OUT_COLUMNS = [
    "case_concept",
    "activity",
    "event_time",
    "user",
    "vendor",
    "document",
    "item_category",
    "net_value",
]

# Small public candidates only. These are pm4py-bundled samples / tiny
# mirrors (<5MB), NOT the 728MB BPI_Challenge_2019.xes (never fetched).
SAMPLE_URLS = [
    "https://raw.githubusercontent.com/pm4py/pm4py-core/master/tests/input_data/running-example.xes",
    "https://raw.githubusercontent.com/pm4py/pm4py-core/master/tests/input_data/receipt.xes",
]

ACTIVITY_MAP = {
    "Purchase Request": "Create Purchase Requisition Item",
    "Purchase Request Approval": "Change Approval for Purchase Order",
    "Purchase Order": "Create Purchase Order Item",
    "Goods Receipt": "Record Goods Receipt",
    "Vendor Invoice": "Record Invoice Receipt",
    "Payment": "Clear Invoice",
    "PO Modification": "Change Quantity",
}

SCENARIO_ITEM_CATEGORY = {
    "S1": "3-way match, invoice after GR",
    "S2": "3-way match, invoice after GR",
    "S3": "3-way match, invoice after GR",
    "S4": "3-way match, invoice after GR",
    "S5": "3-way match, invoice before GR",
    "S6": "3-way match, invoice before GR",
}

# Markers proving a remote sample is genuinely BPIC-2019 P2P (not a generic
# pm4py demo log such as running-example.xes with "register request" etc.).
# A remote payload must yield >=1 activity containing one of these substrings
# (case-insensitive) to qualify as REAL_DOWNLOAD; otherwise it is treated as
# a failure and the lab proxy is built. This keeps REAL_DOWNLOAD honest:
# the task requires P2P activities like 'Create Purchase Order Item' and
# 'Record Goods Receipt'.
BPIC_P2P_MARKERS = (
    "purchase order",
    "purchase requisition",
    "goods receipt",
    "invoice receipt",
    "clear invoice",
    "vendor creates",
    "change quantity",
    "change price",
    "change approval",
    "record goods",
    "record invoice",
    "create purchase",
)


def is_bpic_p2p_like(rows) -> bool:
    for r in rows:
        act = str(r.get("activity", "")).lower()
        if any(m in act for m in BPIC_P2P_MARKERS):
            return True
    return False


def fetch_bytes(url: str) -> bytes:
    """Fetch URL with urllib + 60s timeout, enforcing the <5MB cap."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "p2p-conformance-experiment/fetch_bpic_sample"}
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        length = resp.headers.get("Content-Length")
        if length is not None:
            try:
                if int(length) > MAX_BYTES:
                    raise ValueError(f"remote file too large ({length} bytes)")
            except ValueError:
                raise
        payload = resp.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES:
        raise ValueError("remote file exceeds 5MB cap")
    if not payload:
        raise ValueError("empty download")
    return payload


def _local_tag(tag: str) -> str:
    return tag.split("}")[-1]


def parse_xes_payload(payload: bytes):
    """Parse XES XML payload into OUT_COLUMNS rows (truncated to MAX_ROWS).

    Missing BPIC case attributes in generic pm4py samples are filled with
    documented defaults (vendor='unknown', item_category after-GR default,
    net_value 0) so the output schema is stable.
    """
    root = ET.fromstring(payload)
    rows = []
    for trace in root.iter():
        if _local_tag(trace.tag) != "trace":
            continue
        case_attrs = {}
        for child in trace:
            if _local_tag(child.tag) in (
                "string",
                "date",
                "int",
                "float",
                "boolean",
                "id",
            ):
                case_attrs[child.attrib.get("key")] = child.attrib.get("value")
        raw_case = case_attrs.get("concept:name", "unknown")
        purch_doc = case_attrs.get("Purchasing Document")
        if not purch_doc:
            purch_doc = str(raw_case).split("_")[0] if "_" in str(raw_case) else str(raw_case)
        item = case_attrs.get("Item", "1")
        case_concept = f"{purch_doc}_{item}" if "_" not in str(raw_case) else str(raw_case)
        # If raw case id already looks composite (contains _), keep it.
        if "_" in str(raw_case) and purch_doc in str(raw_case):
            case_concept = str(raw_case)
        vendor = case_attrs.get("Vendor", "unknown")
        item_cat = case_attrs.get("Item Category", "3-way match, invoice after GR")
        for ev in trace:
            if _local_tag(ev.tag) != "event":
                continue
            if len(rows) >= MAX_ROWS:
                break
            e = {}
            for child in ev:
                if _local_tag(child.tag) in (
                    "string",
                    "date",
                    "int",
                    "float",
                    "boolean",
                    "id",
                ):
                    e[child.attrib.get("key")] = child.attrib.get("value")
            activity = e.get("concept:name", "unknown")
            event_time = e.get("time:timestamp", "")
            user = e.get("org:resource", e.get("User", "unknown"))
            net_value = e.get("Cumulative net worth", e.get("net_value", "0"))
            try:
                net_value = str(int(float(str(net_value))))
            except (TypeError, ValueError):
                net_value = "0"
            rows.append(
                {
                    "case_concept": case_concept,
                    "activity": activity,
                    "event_time": event_time,
                    "user": user,
                    "vendor": vendor,
                    "document": purch_doc,
                    "item_category": item_cat,
                    "net_value": net_value,
                }
            )
            if len(rows) >= MAX_ROWS:
                break
        if len(rows) >= MAX_ROWS:
            break
    if not rows:
        raise ValueError("no XES events parsed")
    return rows[:MAX_ROWS]


def parse_csv_payload(payload: bytes):
    """Parse a small mirror CSV payload into OUT_COLUMNS rows (<=MAX_ROWS)."""
    text = payload.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if not lines:
        raise ValueError("empty CSV")
    reader = csv.DictReader(lines)
    if not reader.fieldnames:
        raise ValueError("CSV has no header")
    norm = {h: h.strip() for h in reader.fieldnames}

    def pick(row, *keys):
        for k in keys:
            for h in reader.fieldnames:
                if h.strip().lower() == k.lower():
                    v = row.get(h)
                    if v not in (None, ""):
                        return v
        return None

    rows = []
    for row in reader:
        if len(rows) >= MAX_ROWS:
            break
        # Skip blank lines
        if not any((v or "").strip() for v in row.values() if isinstance(v, str)):
            continue
        raw_case = pick(row, "case_concept", "concept:name", "case_id", "case") or "unknown"
        doc = pick(row, "document", "Purchasing Document", "po_id", "purchasing document") or str(
            raw_case
        ).split("_")[0]
        item = pick(row, "Item", "item") or "1"
        case_concept = raw_case if "_" in str(raw_case) else f"{doc}_{item}"
        rows.append(
            {
                "case_concept": case_concept,
                "activity": pick(row, "activity", "concept:name", "concept_name") or "unknown",
                "event_time": pick(row, "event_time", "time:timestamp", "timestamp",
                                   "time_timestamp") or "",
                "user": pick(row, "user", "org:resource", "User", "resource",
                              "org_resource") or "unknown",
                "vendor": pick(row, "vendor", "Vendor") or "unknown",
                "document": doc,
                "item_category": pick(row, "item_category", "Item Category",
                                      "item category", "scenario") or "3-way match, invoice after GR",
                "net_value": pick(row, "net_value", "Cumulative net worth",
                                  "net worth", "qty_ordered") or "0",
            }
        )
    if not rows:
        raise ValueError("no CSV rows parsed")
    return rows[:MAX_ROWS]


def rows_from_remote(payload: bytes):
    """Dispatch payload to XES or CSV parser based on leading content."""
    stripped = payload.lstrip()
    if stripped.startswith(b"<"):
        return parse_xes_payload(payload)
    # Heuristic: XES without leading '<' (BOM/whitespace handled above) -> try XML first
    try:
        return parse_xes_payload(payload)
    except ET.ParseError:
        return parse_csv_payload(payload)


def write_rows(rows) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLUMNS)
        w.writeheader()
        for r in rows[:MAX_ROWS]:
            w.writerow({c: r.get(c, "") for c in OUT_COLUMNS})


def build_lab_proxy():
    """Build data/bpic_sample.csv from first 300 events of event-log-r1.csv."""
    rows = []
    with open(LOCAL_SRC, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, r in enumerate(reader):
            if i >= MAX_ROWS:
                break
            po_id = (r.get("po_id") or "").strip()
            case_concept = f"{po_id}_1"  # PurchDoc_Item composite proxy
            activity = ACTIVITY_MAP.get((r.get("activity") or "").strip(),
                                        (r.get("activity") or "").strip())
            try:
                net_value = str(int(float(r.get("qty_ordered") or 0)) * 100)
            except (TypeError, ValueError):
                net_value = "0"
            rows.append(
                {
                    "case_concept": case_concept,
                    "activity": activity,
                    "event_time": (r.get("timestamp") or "").strip(),
                    "user": (r.get("resource") or "").strip(),
                    "vendor": (r.get("vendor") or "").strip(),
                    "document": po_id,
                    "item_category": SCENARIO_ITEM_CATEGORY.get(
                        (r.get("scenario") or "").strip(),
                        "3-way match, invoice after GR",
                    ),
                    "net_value": net_value,
                }
            )
    if not rows:
        raise ValueError(f"no events read from {LOCAL_SRC}")
    write_rows(rows)
    return rows


def main() -> None:
    # 1. Try real small download (ANY failure -> fallback).
    try:
        last_err = None
        for url in SAMPLE_URLS:
            try:
                payload = fetch_bytes(url)
                rows = rows_from_remote(payload)
                if not is_bpic_p2p_like(rows):
                    raise ValueError(
                        "remote sample is not BPIC-2019 P2P-like "
                        "(no Create Purchase Order Item / Record Goods Receipt "
                        "family activity); using lab proxy"
                    )
                write_rows(rows)
                print(f"REAL_DOWNLOAD mode: fetched {url}")
                print(f"rows={len(rows)} columns={','.join(OUT_COLUMNS)} -> {OUT_PATH}")
                return
            except Exception as exc:  # noqa: BLE001 - any failure falls back
                last_err = exc
                print(f"download attempt failed for {url}: {exc}")
                continue
        raise RuntimeError(f"all {len(SAMPLE_URLS)} download attempts failed ({last_err})")
    except Exception as exc:  # noqa: BLE001 - spec: on ANY failure use lab proxy
        print(f"falling back to lab proxy ({exc})")
    # 2. Lab proxy from local first-300 events.
    rows = build_lab_proxy()
    print("LAB_PROXY mode: built from data/event-log-r1.csv first 300 events")
    print(f"rows={len(rows)} columns={','.join(OUT_COLUMNS)} -> {OUT_PATH}")


if __name__ == "__main__":
    main()
