# Task 3 spec and quality review

Reviewed `2ef994b..fd74521` against the Task 3 brief, binding project specification, and `docs/event-contract.md` on 2026-10-26. This is a source and targeted-behavior review, not an Odoo execution audit.

## Verdict

- **Spec: needs one fix.** The adapter does not reject an explicitly identified reversal when it is encoded under an otherwise allowed activity. The binding contract requires returns/reversals to be rejected, not silently accepted. Other reviewed Task 3 requirements are substantially met.
- **Quality: needs one fix before calling the CSV boundary strict.** The implementation is otherwise small, deterministic and fail closed on the tested invalid inputs. The synthetic example is clearly labeled and live ERP claims remain unverified.

## Finding

**Moderate — unsupported reversal passes the strict adapter** (`src/validate_erp_export.py:47-48`, `:53-64`, `:69-79`; `tests/test_erp_export.py:77-85`). The activity allowlist rejects a distinct `Credit Note` activity, but `source_action` is checked only for nonblank content. A row with `activity=Vendor Invoice`, `source_action=reverse posted vendor bill / credit note`, and a positive `qty_invoiced` passes. The input schema also forbids separate reversal flags, so an exporter cannot provide a structured signal that the validator checks. I changed only fixture event E6's `source_action` in a temporary CSV to that string; `validate_export` accepted all 14 rows. This could count a reversal as a positive invoice delta and change R3. Define a constrained source-action mapping or an explicit action direction/type with rejected reversal values; add a test for an allowed activity carrying reversal evidence. The boundary still cannot establish that a source record is authentic, as correctly disclosed in the docs.

## Reviewed evidence

- `src/validate_erp_export.py:33-86` requires the source IDs and recorded, timezone-aware datetime; normalizes UTC; checks same product/UoM grain, event-delta receipt/invoice quantities, distinct event/source keys, and same-case invoice links for payments. Invalid CLI input is validated before `write_export` (`:113-117`); replacement output is created atomically (`:89-105`). Existing tests cover invalid output preservation and the synthetic checker outcomes. I did not rerun the reported 55-test suite.
- `sql/odoo_extract.sql:1-12` raises an exception without extraction; the older SQL is archived. `docker-compose.yml:14-15` binds the UI to loopback, and `docs/03-odoo-setup.md:7-8` uses the Compose PostgreSQL service instead of a nonexistent host port.
- `docs/erp-pilot.md:3-11,20-28` requests recorded action audit proof, exact item/UoM and invoice mapping, attempted-action outcomes, control checks, arm denominators, and an explicit stop on missing history. It labels the fixture synthetic and live Odoo execution unverified. These are instructions, not observed runtime evidence.

## Declined to judge / next integration boundary

- No live Odoo schema, instrumentation, configured permissions, control behavior, source-action authenticity, or payment allocation was inspected. Docker had no daemon in the reported check and the previous Colima startup was denied; I did not retry it.
- The old `README.md:45` command still targets host PostgreSQL and the retired SQL; `docs/04-odoo-execution-protocol.md:45,55` still names the old extraction path. Their supersession is explicitly assigned to Task 4 and is not a Task 3 defect; root integration must retire these newcomer paths before completion.
- I did not independently verify the report's entire RED/GREEN chronology, full-suite count, or the archived SQL byte-for-byte hash. The targeted reproduction above is the only test run in this review.
