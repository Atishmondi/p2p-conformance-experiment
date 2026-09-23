# Odoo Setup (Mac arm64, Docker path)

1. Install Docker Desktop:
   brew install --cask docker
   Open Docker app once to complete setup.
2. Start stack from `p2p-conformance-experiment/`:
   docker compose up -d
   Open http://localhost:8069, create DB `p2p-exp`, install Purchase, Inventory, Invoicing.
3. Master data (fixed for comparability):
   3 vendors, 5 products (storable, purchaseable), 1 purchase team, 2 approvers.
4. No multi-company, no custom valuation. Keep P2P only.
