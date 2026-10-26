# Task 3 scoped re-review

Reviewed `fd74521..0aad3e9` against the sole moderate finding in `task-3-review.md` on 2026-10-26. Scope: `source_action` mapping, updated fixture/test, pilot wording, and affected consumers.

## Verdict

- **Spec: addressed.** The explicit reversal and mismatched action cases now fail validation. No open finding from the previous Task 3 review.
- **Quality: pass for this scoped fix.** No new regression found in changed code or the fixture consumer search. Live ERP source authenticity still requires the independent audit described in the pilot; this is not an execution verdict.

## Finding disposition

**Addressed — reversal encoded as a positive invoice.** `src/validate_erp_export.py:20-29,54-58` now permits exactly one normalized `source_action` code per supported activity; a credit-note reversal phrase or a receipt action on `Vendor Invoice` raises `ValueError`. `tests/test_erp_export.py:94-100` pins both rejection cases. `docs/erp-pilot.md:11-24` defines the eight codes, requires source-transition and direction checks before mapping, and explicitly warns that a dishonest permitted code cannot prove source authenticity. The synthetic fixture uses these codes; the fixture's only direct consumer found in `src/`, `tests/`, `docs/`, `README.md` and `examples/` is the focused ERP test.

Focused verification: `python3 -S -m unittest tests.test_erp_export -q` passed 8/8. I also reran the original temporary-fixture reversal reproduction; it failed validation at line 7 with `unsupported or mismatched source_action`. The full suite was not rerun after this change, as the task report correctly states.

## Open / declined to judge

- No open issue within this re-review scope; no new regression found.
- The adapter cannot independently verify real Odoo action direction, actor, immutable history or payment allocation. No live runtime or source audit was available, and I did not retry Docker/Colima.
- README and `docs/04-odoo-execution-protocol.md` supersession remains the separately assigned Task 4 integration item, unchanged by this fix.
