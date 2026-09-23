-- ==========================================================================
-- Odoo 17 P2P event-log extractor for the conformance experiment.
--
-- DB:      p2p-exp (Odoo 17, modules: Purchase / Inventory / Invoicing)
-- Target:  case_id,activity,timestamp,resource,scenario,vendor,po_id,
--          qty_ordered,qty_received,qty_invoiced,
--          line_no,product_id,price_unit,currency,company_id
--          (superset of data/event-log-template.csv; PM4Py-compatible.
--           First 10 cols match template order, then line granularity.)
--
-- Usage (from repo root):
--   psql -h localhost -U odoo p2p-exp -f sql/odoo_extract.sql -o data/event-log-odoo.csv --csv
-- Requires psql >= 16 for the --csv flag (header row included automatically).
--
-- Design notes / assumptions:
--   * One purchase_order (po.name, e.g. P00001) = one case, so
--     case_id = po_id = po.name. Odoo has no case notion; the PO reference
--     is carried via stock_picking.origin and account_move.invoice_origin.
--   * Line granularity: blocks 1-3 join purchase_order_line (one row per
--     PO line) exposing line_no = pol.sequence, product_id = pol.product_id,
--     price_unit = pol.price_unit, with per-line qty_ordered = pol.product_qty,
--     qty_received = pol.qty_received, qty_invoiced = pol.qty_invoiced.
--     Blocks 4-6 stay at picking / bill / payment grain (NULL line cols)
--     for UNION compatibility; header totals come from pol_agg.
--   * Partial receipts: recv_agg aggregates stock_move.quantity_done
--     per picking (SUM WHERE state = 'done' GROUP BY picking_id), so a
--     picking split over several moves is summed into one qty_received.
--   * Bill lines: inv_agg aggregates account_move_line.quantity per bill
--     (SUM GROUP BY move_id) into qty_invoiced.
--   * Currency: res_currency.name via po.currency_id (1-4), am.currency_id
--     (5), ap.currency_id (6); block 4 falls back to picking company
--     currency when po link is missing.
--   * Single-company filter: single_co = MIN(res_company.id); every block
--     filters to that company_id (po / sp / am / ap). Multi-company DBs
--     therefore export one company only.
--   * Odoo has no "scenario" (S1-S6 live in the experiment protocol), so it
--     is emitted as NULL and enriched downstream from the execution plan.
--   * resource = res_users.login of the acting user, with a role-literal
--     fallback matching the synthetic log (requester / approver / buyer /
--     warehouse / accountant).
--   * Qty columns are cast to integer: src/check_conformance.py applies
--     int(value), and raw float sums (e.g. '10.0') would otherwise coerce
--     to 0 and break the R3 check (qty_invoiced <= qty_received).
--   * Blocks 1-3 all read purchase_order: PR creation = date_order /
--     create_date, while approval and confirmation share date_approve
--     (Odoo merges approval + PO confirmation into one action). The
--     Purchase Order event adds INTERVAL '1 second' so the normative R1
--     order (Approval < Order) is preserved in the export; drop the
--     epsilon if raw timestamps are preferred.
--   * If the OCA purchase_request module is installed, replace block 1
--     with purchase_request (create_date) joined to purchase_request_line.
--   * Goods Receipt filters picking_code = 'incoming' per spec; if your
--     Odoo stores the type only via stock_picking_type, replace with:
--       JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
--       ... WHERE spt.code = 'incoming' AND sp.state = 'done'
--   * Payment -> case linkage is heuristic: paying a bill from the Odoo UI
--     stores the bill name in account_payment.memo, joined back via
--     account_move / invoice_origin. For an exact money trail use
--     account_partial_reconcile instead. Unlinked payments fall back to
--     ap.name as case_id (single-event case) rather than NULL.
--   * Payment filter keeps vendor out-payments only
--     (payment_type = 'outbound', partner_type = 'supplier'). Add
--     AND ap.state = 'posted' if your version carries that column.
-- Tables: purchase_order, purchase_order_line, stock_picking, stock_move,
--         account_move, account_move_line, account_payment,
--         res_partner, res_users, res_currency, res_company.
-- ==========================================================================

WITH pol_agg AS (
    SELECT order_id,
           COALESCE(SUM(product_qty), 0)::integer  AS qty_ordered,
           COALESCE(SUM(qty_received), 0)::integer AS qty_received,
           COALESCE(SUM(qty_invoiced), 0)::integer AS qty_invoiced
    FROM purchase_order_line
    GROUP BY order_id
),
recv_agg AS (
    SELECT picking_id,
           COALESCE(SUM(quantity_done), 0)::integer AS qty_received
    FROM stock_move
    WHERE state = 'done'
    GROUP BY picking_id
),
inv_agg AS (
    SELECT move_id,
           COALESCE(SUM(quantity), 0)::integer AS qty_invoiced
    FROM account_move_line
    GROUP BY move_id
),
single_co AS (
    SELECT MIN(id) AS id FROM res_company
)

-- 1. Purchase Request: PR/RFQ creation (one row per PO line) -----------------
SELECT
    po.name::text                                      AS case_id,
    'Purchase Request'::text                           AS activity,
    COALESCE(po.date_order, po.create_date)::timestamp AS timestamp,
    COALESCE(cu.login, 'requester')::text              AS resource,
    NULL::text                                         AS scenario,
    rp.name::text                                      AS vendor,
    po.name::text                                      AS po_id,
    COALESCE(pol.product_qty, 0)::integer              AS qty_ordered,
    COALESCE(pol.qty_received, 0)::integer             AS qty_received,
    COALESCE(pol.qty_invoiced, 0)::integer             AS qty_invoiced,
    pol.sequence::integer                              AS line_no,
    pol.product_id::integer                            AS product_id,
    pol.price_unit::numeric                            AS price_unit,
    rcu.name::text                                     AS currency,
    po.company_id::integer                             AS company_id
FROM purchase_order po
JOIN res_partner rp         ON rp.id = po.partner_id
JOIN purchase_order_line pol ON pol.order_id = po.id
LEFT JOIN res_users cu      ON cu.id = po.create_uid
LEFT JOIN res_currency rcu  ON rcu.id = po.currency_id
WHERE po.company_id = (SELECT id FROM single_co)

UNION ALL

-- 2. Purchase Request Approval: approval date (one row per PO line) ---------
SELECT
    po.name::text                         AS case_id,
    'Purchase Request Approval'::text     AS activity,
    po.date_approve::timestamp            AS timestamp,
    COALESCE(wu.login, 'approver')::text  AS resource,
    NULL::text                            AS scenario,
    rp.name::text                         AS vendor,
    po.name::text                         AS po_id,
    COALESCE(pol.product_qty, 0)::integer AS qty_ordered,
    COALESCE(pol.qty_received, 0)::integer AS qty_received,
    COALESCE(pol.qty_invoiced, 0)::integer AS qty_invoiced,
    pol.sequence::integer                 AS line_no,
    pol.product_id::integer               AS product_id,
    pol.price_unit::numeric               AS price_unit,
    rcu.name::text                        AS currency,
    po.company_id::integer                AS company_id
FROM purchase_order po
JOIN res_partner rp         ON rp.id = po.partner_id
JOIN purchase_order_line pol ON pol.order_id = po.id
LEFT JOIN res_users wu      ON wu.id = po.write_uid
LEFT JOIN res_currency rcu  ON rcu.id = po.currency_id
WHERE po.date_approve IS NOT NULL
  AND po.company_id = (SELECT id FROM single_co)

UNION ALL

-- 3. Purchase Order: confirmed PO, +1s epsilon (one row per PO line) --------
SELECT
    po.name::text                                        AS case_id,
    'Purchase Order'::text                               AS activity,
    (po.date_approve + INTERVAL '1 second')::timestamp   AS timestamp,
    COALESCE(bu.login, 'buyer')::text                   AS resource,
    NULL::text                                          AS scenario,
    rp.name::text                                       AS vendor,
    po.name::text                                       AS po_id,
    COALESCE(pol.product_qty, 0)::integer               AS qty_ordered,
    COALESCE(pol.qty_received, 0)::integer              AS qty_received,
    COALESCE(pol.qty_invoiced, 0)::integer              AS qty_invoiced,
    pol.sequence::integer                               AS line_no,
    pol.product_id::integer                             AS product_id,
    pol.price_unit::numeric                             AS price_unit,
    rcu.name::text                                      AS currency,
    po.company_id::integer                              AS company_id
FROM purchase_order po
JOIN res_partner rp         ON rp.id = po.partner_id
JOIN purchase_order_line pol ON pol.order_id = po.id
LEFT JOIN res_users bu      ON bu.id = po.user_id
LEFT JOIN res_currency rcu  ON rcu.id = po.currency_id
WHERE po.state IN ('purchase', 'done')
  AND po.date_approve IS NOT NULL
  AND po.company_id = (SELECT id FROM single_co)

UNION ALL

-- 4. Goods Receipt: done incoming picking, qty via stock_move sum ----------
SELECT
    COALESCE(po.name, sp.origin, sp.name)::text AS case_id,
    'Goods Receipt'::text                       AS activity,
    sp.date_done::timestamp                     AS timestamp,
    COALESCE(wu.login, 'warehouse')::text       AS resource,
    NULL::text                                  AS scenario,
    rp.name::text                               AS vendor,
    COALESCE(po.name, sp.origin)::text          AS po_id,
    COALESCE(a.qty_ordered, 0)::integer         AS qty_ordered,
    COALESCE(r.qty_received, 0)::integer        AS qty_received,
    COALESCE(a.qty_invoiced, 0)::integer        AS qty_invoiced,
    NULL::integer                               AS line_no,
    NULL::integer                               AS product_id,
    NULL::numeric                               AS price_unit,
    COALESCE(rcu.name, ccu.name)::text          AS currency,
    sp.company_id::integer                      AS company_id
FROM stock_picking sp
JOIN res_partner rp    ON rp.id = sp.partner_id
LEFT JOIN res_users wu ON wu.id = sp.write_uid
LEFT JOIN purchase_order po ON po.name = sp.origin
LEFT JOIN pol_agg a    ON a.order_id = po.id
LEFT JOIN recv_agg r   ON r.picking_id = sp.id
LEFT JOIN res_currency rcu ON rcu.id = po.currency_id
LEFT JOIN res_company mco  ON mco.id = sp.company_id
LEFT JOIN res_currency ccu  ON ccu.id = mco.currency_id
WHERE sp.state = 'done'
  AND sp.picking_code = 'incoming'
  AND sp.date_done IS NOT NULL
  AND sp.company_id = (SELECT id FROM single_co)

UNION ALL

-- 5. Vendor Invoice: posted supplier bill, qty via account_move_line -------
SELECT
    COALESCE(po.name, am.invoice_origin, am.name)::text AS case_id,
    'Vendor Invoice'::text                              AS activity,
    COALESCE(am.invoice_date, am.date)::timestamp       AS timestamp,
    COALESCE(iu.login, 'accountant')::text              AS resource,
    NULL::text                                          AS scenario,
    rp.name::text                                       AS vendor,
    COALESCE(po.name, am.invoice_origin)::text          AS po_id,
    COALESCE(a.qty_ordered, 0)::integer                 AS qty_ordered,
    COALESCE(a.qty_received, 0)::integer                AS qty_received,
    COALESCE(l.qty_invoiced, 0)::integer                AS qty_invoiced,
    NULL::integer                                       AS line_no,
    NULL::integer                                       AS product_id,
    NULL::numeric                                       AS price_unit,
    rcu.name::text                                      AS currency,
    am.company_id::integer                              AS company_id
FROM account_move am
JOIN res_partner rp    ON rp.id = am.partner_id
LEFT JOIN res_users iu ON iu.id = am.invoice_user_id
LEFT JOIN purchase_order po ON po.name = am.invoice_origin
LEFT JOIN pol_agg a    ON a.order_id = po.id
LEFT JOIN inv_agg l    ON l.move_id = am.id
LEFT JOIN res_currency rcu ON rcu.id = am.currency_id
WHERE am.move_type = 'in_invoice'
  AND am.state = 'posted'
  AND COALESCE(am.invoice_date, am.date) IS NOT NULL
  AND am.company_id = (SELECT id FROM single_co)

UNION ALL

-- 6. Payment: vendor out-payment --------------------------------------------
SELECT
    COALESCE(po.name, bill.invoice_origin, ap.memo, ap.name)::text AS case_id,
    'Payment'::text                                                AS activity,
    ap.date::timestamp                                             AS timestamp,
    COALESCE(pu.login, 'accountant')::text                         AS resource,
    NULL::text                                                    AS scenario,
    rp.name::text                                                 AS vendor,
    COALESCE(po.name, bill.invoice_origin)::text                  AS po_id,
    COALESCE(a.qty_ordered, 0)::integer                           AS qty_ordered,
    COALESCE(a.qty_received, 0)::integer                          AS qty_received,
    COALESCE(a.qty_invoiced, 0)::integer                          AS qty_invoiced,
    NULL::integer                                                 AS line_no,
    NULL::integer                                                 AS product_id,
    NULL::numeric                                                 AS price_unit,
    rcu.name::text                                                AS currency,
    ap.company_id::integer                                        AS company_id
FROM account_payment ap
JOIN res_partner rp    ON rp.id = ap.partner_id
LEFT JOIN res_users pu ON pu.id = ap.create_uid
LEFT JOIN account_move bill
       ON bill.name = ap.memo
      AND bill.move_type = 'in_invoice'
LEFT JOIN purchase_order po ON po.name = bill.invoice_origin
LEFT JOIN pol_agg a    ON a.order_id = po.id
LEFT JOIN res_currency rcu ON rcu.id = ap.currency_id
WHERE ap.payment_type = 'outbound'
  AND ap.partner_type = 'supplier'
  AND ap.date IS NOT NULL
  AND ap.company_id = (SELECT id FROM single_co)

ORDER BY 1, 3;
