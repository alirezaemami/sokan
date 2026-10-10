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
bench start                                     # web server on :8000
```

The frontend selects the site with an `X-Frappe-Site-Name` header, so it
works on a multi-site bench whatever `default_site` is.

#### Management

Managers run Sokan from the website at `/admin`, never from Desk. Create the
first one from the command line; add the rest in **Settings → Managers**:

```bash
bench --site sokan.local sokan-add-manager you@example.com --name "Your Name"
```

The admin portal covers: overview, forwarder approval (approve / reject /
suspend, verified and featured flags, plan, wallet adjustments), requests,
top-up approval, customers (block / unblock), review moderation, contact
messages, the wallet ledger with CSV export, reports (funnel, revenue, lanes,
modes, top forwarders) and settings (platform rules, plans, transport modes,
managers).

All of it goes through `sokan/api/admin.py`. Every endpoint checks the
**Sokan Admin** role (or System Manager) first, writes are POST-only with the
CSRF token, editable fields are allowlisted, and money only moves through the
wallet ledger. The Sokan Admin role has no Desk access, so managers are
Website Users.

Reviews start as *Pending* and are public, and counted in ratings, only once a
manager approves them. Editing a review sends it back to Pending.

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
