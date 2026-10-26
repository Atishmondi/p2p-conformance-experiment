# Isolated Odoo 17 demo setup (pilot only)

**Read [ERP pilot](erp-pilot.md) before running.** No Odoo experiment has been executed or verified here. The database credentials in this demo compose are local examples; never reuse them in production. No public port is exposed: the UI binds to `127.0.0.1:8069`.

1. On a machine with a working Docker daemon, run `docker compose up -d` from the repository root and open <http://127.0.0.1:8069>. Create a disposable database `p2p-exp` and install Purchase, Inventory, and Invoicing. Docker Compose pulls the Odoo 17 and PostgreSQL 15 images; pin image digests and record them in the run record before collecting evidence.
2. Restrict the pilot to one company, 3 fictional vendors, 5 comparable purchased products, and distinct requester, approver, buyer, warehouse, and accountant actors. No production credentials or data. Confirm controls and permissions in the actual installed instance before deciding which actions are testable.
3. PostgreSQL is reachable inside the Compose network, not on the host. If inspecting the **demo** database is needed, use `docker compose exec db psql -U odoo -d p2p-exp` after verifying the DB name. There is no host `psql -h localhost` access in this Compose file.
4. An SQL snapshot is insufficient to prove the recorded action histories required by the checker. [The retired SQL entry point](../sql/odoo_extract.sql) deliberately raises an error. Follow the source instrumentation and independent audit in [ERP pilot](erp-pilot.md), then validate the explicit CSV with `python3 src/validate_erp_export.py INPUT.csv --out VALIDATED.csv`.

The current environment has no Docker daemon. A previous bounded Colima start was denied while writing `~/.colima/default/colima.yaml`; the pilot protocol is ready, but ERP execution is unverified. Do not infer Odoo control behavior from the synthetic fixture.
