-- FAIL CLOSED: no generic Odoo 17 recorded-action extractor is verified.
-- This retired entry point is deliberately non-extracting. The prior SQL is
-- archived as non-executable text in odoo_extract_legacy_UNSAFE.txt; it inferred
-- request/approval dates, fabricated +1 second PO ordering, mixed item/header
-- quantities, and linked payments through a memo heuristic.
-- Instrument and independently audit actual recorded actions in the isolated
-- pilot first. Export the documented event CSV, then run
-- python3 src/validate_erp_export.py INPUT --out OUTPUT.
-- A source_id or timestamp_kind value alone cannot establish authentic ERP history.
DO $$ BEGIN
  RAISE EXCEPTION 'No verified Odoo recorded-action extractor: use audited pilot export and src/validate_erp_export.py';
END $$;
