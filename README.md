### Sokan

Freight marketplace. Shippers post one request; every matching, verified
forwarder receives it and competes with a priced quote. Forwarders pay per
lead from a prepaid wallet; shippers never pay.

```
sokan/              Frappe app (DocTypes, billing, API)
frontend/           Nuxt 4 SSR site + customer and forwarder portals
```

#### How it works

| Step | Who | What happens | Billing |
|---|---|---|---|
| Publish | Customer | `Freight Request` → status *Open* | free |
| Distribute | System | one `Freight Request Lead` per active forwarder matching mode (+ country coverage) | free |
| Preview | Forwarder | sees route, cargo summary, dates, competition | free |
| Unlock | Forwarder | sees addresses, packing list, notes, attachment, customer contact | **unlock fee** (or monthly free allowance) |
| Quote | Forwarder | itemised `Freight Quote`; revisions free | **quote fee** (or free allowance) |
| Book | Customer | accepts one quote; others auto-rejected; both sides see each other's contact | free |

Fees come from the forwarder's `Sokan Plan` (falling back to `Sokan Settings`).
Every balance change is an immutable `Sokan Wallet Transaction`; its controller
row-locks the forwarder, so concurrent charges can't overspend. Top-ups are
`Sokan Top Up` records an admin approves in Desk.

Scheduled: daily expiry of requests/quotes, monthly plan fees (unpaid → default plan).

#### Backend setup

```bash
bench new-site sokan.local
bench --site sokan.local install-app sokan     # creates roles, transport modes, 3 plans, settings
bench --site sokan.local set-config developer_mode 1
bench --site sokan.local serve --port 8002
```

Then in Desk: **Sokan Settings** (website URL, fees, auto-approve), and approve
forwarders by setting **Sokan Forwarder → Status = Active**.

#### Frontend

```bash
cd frontend
cp .env.example .env      # NUXT_PUBLIC_FRAPPE_API_BASE, NUXT_PUBLIC_SITE_URL
npm install
npm run dev               # http://localhost:3000
npm run build && node .output/server/index.mjs
```

Use Node 22 / 24 LTS. English is the default locale; Persian (RTL) lives under `/fa`.
`/api` and `/files` are proxied to Frappe, so the session cookie is first-party.
In production nginx should route `/api` and `/files` to Frappe and everything else to Nuxt.

#### License

mit
