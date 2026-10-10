# Deploying Sokan (Frappe + Nuxt)

Assumes: a Frappe v16 bench already running in production (`bench setup production` done, nginx and supervisor managing it) under the `frappe` user, and you're adding the `sokan` app and its Nuxt frontend to it.

Layout:

| Host | Serves |
|---|---|
| `https://www.sokan.app` | **The public site** (canonical). Nuxt for pages; `/api`, `/files` and `/private/files` go straight to Frappe on the same origin. |
| `https://sokan.app` | 301 → `https://www.sokan.app` |
| `https://app.sokan.app` | The Frappe site itself (bench site name). Kept out of search engines. Managers never need it: they work in `/admin` on the public site. |

**No CORS.** The browser only ever talks to `www.sokan.app`. nginx forwards `/api` and `/files` on that domain to Frappe, so the session cookie is first-party and there's no cross-origin request to allow. Don't set `allow_cors` in `site_config.json`. If you ever do point the browser at `app.sokan.app` directly, client-side calls (login, quote forms, the admin portal) will fail silently in the console while server-rendered pages still look fine.

Requirements: Node **22 or 24 LTS** (Nuxt 4 doesn't support Node 25), Python per Frappe v16, MariaDB and Redis as the bench already has them.

## 1. Get the `sokan` app onto the server

The app lives at `git@github.com:alirezaemami/sokan.git`. It's private, so add the server's SSH key (`~frappe/.ssh/id_ed25519.pub`) to the repository as a read-only deploy key first. Then, as `frappe`:

```bash
cd ~/frappe-bench
bench get-app sokan git@github.com:alirezaemami/sokan.git
```

Create the site, on its final name, and install the app. Use a **fresh site**, not a copy of a development database:

```bash
bench new-site app.sokan.app --install-app sokan
bench --site app.sokan.app set-config developer_mode 0
bench --site app.sokan.app set-config host_name "https://app.sokan.app"
bench --site app.sokan.app enable-scheduler
bench --site app.sokan.app migrate
```

`install-app` creates the roles, the 8 transport modes, the 3 plans and default settings. `migrate` also schedules the daily jobs (request expiry, the managers' 08:00 summary) and the monthly plan renewal.

Create the first manager. Use an address that already has an account on this site, or set up email (step 6) before running this, since a new account is created without a password and gets its set-password link by email:

```bash
bench --site app.sokan.app sokan-add-manager you@yourcompany.com --name "Your Name"
```

Further managers are added from the website: `https://www.sokan.app/admin/settings` → Managers.

## 2. Put Frappe on its own subdomain

```bash
bench setup add-domain app.sokan.app --site app.sokan.app
bench setup nginx
sudo supervisorctl restart all
```

DNS: `app.sokan.app` → the server's IP.

Check which port gunicorn listens on. Step 4 proxies `/api` there:

```bash
grep webserver_port ~/frappe-bench/sites/common_site_config.json   # usually 8000
```

## 3. Build and run the Nuxt frontend

```bash
cd ~/frappe-bench/apps/sokan/frontend
node -v                     # must be v22.x or v24.x
cp .env.example .env
```

Edit `.env`:

```bash
# Frappe's own web server on this machine. Loopback is right here: the site is
# chosen by the X-Frappe-Site-Name header below, not by the Host header.
NUXT_PUBLIC_FRAPPE_API_BASE=http://127.0.0.1:8000
NUXT_FRAPPE_SITE_NAME=app.sokan.app
# Canonical origin: canonical tags, hreflang, og:image and the sitemap use it.
NUXT_PUBLIC_SITE_URL=https://www.sokan.app
```

Then build:

```bash
npm ci
npm run build
```

**Set `.env` before building.** `nuxt.config.ts` reads these values when the config loads, and the `/api` proxy target and the canonical domain end up in the build. Changing the environment afterwards does not move them. If you change any of the three, rebuild.

The build produces a self-contained server at `.output/server/index.mjs`. Check the port is free (several Node apps on one box is common):

```bash
sudo ss -ltnp | grep -E ':(3000|3001|3002)\b'
```

`/etc/supervisor/conf.d/sokan-frontend.conf`:

```ini
[program:sokan-frontend]
command=/usr/bin/node /home/frappe/frappe-bench/apps/sokan/frontend/.output/server/index.mjs
directory=/home/frappe/frappe-bench/apps/sokan/frontend
environment=NUXT_PUBLIC_FRAPPE_API_BASE="http://127.0.0.1:8000",NUXT_FRAPPE_SITE_NAME="app.sokan.app",NUXT_PUBLIC_SITE_URL="https://www.sokan.app",PORT="3000",HOST="127.0.0.1",NODE_ENV="production"
autostart=true
autorestart=true
startsecs=5
user=frappe
stdout_logfile=/home/frappe/frappe-bench/logs/sokan-frontend.log
stderr_logfile=/home/frappe/frappe-bench/logs/sokan-frontend.error.log
```

If `which node` shows an nvm path (for example `/home/frappe/.nvm/versions/node/v22.x/bin/node`), put that absolute path in `command=`. supervisor runs with a minimal PATH and won't find a shell-managed node.

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status sokan-frontend   # RUNNING
curl -sI http://127.0.0.1:3000/ | head -1  # HTTP/1.1 200 OK
```

## 4. nginx for the public site

Create `/etc/nginx/conf.d/sokan.conf`. Don't edit the generated Frappe config for `app.sokan.app`; this is a separate file for the public domains. It already includes the `sokan.app` → `www` redirect, so it is the only nginx config for those two hosts.

Bootstrap order: certbot needs to reach both hosts over plain http before the https blocks can load. So the **first time**, start with just the two port-80 blocks (the redirect block and the `www` http block below), run step 5, then add the rest. Later edits use the file as shown.

```nginx
# Frappe's gunicorn (see webserver_port in step 2).
upstream sokan_frappe   { server 127.0.0.1:8000 fail_timeout=0; }
upstream sokan_frontend { server 127.0.0.1:3000 fail_timeout=0; }

# sokan.app (http and https) -> https://www.sokan.app
server {
    listen 80;
    listen 443 ssl http2;
    server_name sokan.app;

    ssl_certificate     /etc/letsencrypt/live/www.sokan.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.sokan.app/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    # Let certbot renew without the redirect swallowing the challenge.
    location ^~ /.well-known/acme-challenge/ { root /var/www/html; }

    location / { return 301 https://www.sokan.app$request_uri; }
}

# www: http -> https
server {
    listen 80;
    server_name www.sokan.app;

    location ^~ /.well-known/acme-challenge/ { root /var/www/html; }

    location / { return 301 https://www.sokan.app$request_uri; }
}

# www: the site
server {
    listen 443 ssl http2;
    server_name www.sokan.app;

    ssl_certificate     /etc/letsencrypt/live/www.sokan.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.sokan.app/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    # Forwarder receipts and logos are uploaded through /api/method/upload_file.
    client_max_body_size 25m;

    # API and files go straight to Frappe on this same origin: no CORS, a
    # first-party session cookie, and Frappe sees the visitor's real IP for its
    # rate limits. X-Frappe-Site-Name picks the site, since Host is www.sokan.app.
    location ~ ^/(api|files|private/files)/ {
        proxy_pass http://sokan_frappe;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Frappe-Site-Name app.sokan.app;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120;
    }

    # Everything else is the Nuxt site.
    location / {
        proxy_pass http://sokan_frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo nginx -t
sudo systemctl reload nginx
```

DNS: `www.sokan.app` and `sokan.app` → the server's IP. For the apex, use an A/AAAA record; most DNS hosts don't allow a CNAME there.

## 5. SSL

The two public hostnames share one certificate, and the Frappe subdomain gets its own:

```bash
sudo certbot --nginx -d www.sokan.app -d sokan.app
sudo certbot --nginx -d app.sokan.app
sudo certbot certificates      # confirm the www.sokan.app cert path used above
```

Certbot files a combined certificate under the first `-d` name, which is why the nginx blocks point at `/etc/letsencrypt/live/www.sokan.app/`. If `certbot certificates` shows a different path, update `ssl_certificate` in both blocks to match. Then test renewal; the acme-challenge exceptions above are what make it work:

```bash
sudo certbot renew --dry-run
```

### Redirect checks

```bash
curl -sI http://sokan.app          | grep -iE '^(HTTP|location)'   # 301 -> https://www.sokan.app/
curl -sI https://sokan.app         | grep -iE '^(HTTP|location)'   # 301 -> https://www.sokan.app/
curl -sI http://www.sokan.app      | grep -iE '^(HTTP|location)'   # 301 -> https://www.sokan.app/
curl -sI https://sokan.app/pricing | grep -iE '^(HTTP|location)'   # path kept: -> https://www.sokan.app/pricing
curl -sI https://www.sokan.app     | head -1                        # 200
```

## 6. Configure Sokan before anyone signs up

Sign in at `https://www.sokan.app/login` as the manager from step 1, then work through these.

**Email** (nothing is sent without it): sign in to Desk at `https://app.sokan.app/app/email-account/new` as Administrator. Create an account with *Enable Outgoing* and *Default Outgoing* ticked, sending from something like `no-reply@sokan.app`. Add SPF, DKIM and DMARC records for that domain at your DNS host, or password-reset and booking emails will land in spam.

**Sokan settings**: `https://www.sokan.app/admin/settings`

| Setting | Value |
|---|---|
| Website address | `https://www.sokan.app` (every email link and the email logo use it) |
| Support email / phone | your support contacts (shown in emails; managers get alerts there) |
| Top-up instructions | your bank details: where forwarders send money |
| Fees, welcome credit, low-balance warning, approval and matching rules | as you want them on day one |

Also check **Plans** and **Transport modes** in the same page.

**Currency**: in Desk, *System Settings → Currency* must match Sokan's currency (USD unless you change it in Sokan settings).

Then run the go-live check. It exits non-zero while anything still needs fixing:

```bash
bench --site app.sokan.app sokan-check
```

## 7. Keep the backend out of Google

`app.sokan.app` is publicly reachable, and it shouldn't compete with the public site in search results:

```bash
bench --site app.sokan.app set-config robots_txt "User-agent: *\nDisallow: /"
```

The public site serves its own `robots.txt` and `sitemap.xml`. Both exclude the portals (`/account`, `/partner`, `/admin`) and the sign-in pages.

## 8. Verify

- `https://www.sokan.app` and `https://www.sokan.app/fa` load. The home page shows transport modes and stats, which come from the API, so blank sections mean `/api` routing is broken.
- `curl -s https://www.sokan.app/api/method/sokan.api.public.list_countries | head -c 80` returns JSON with countries, not HTML.
- Sign up as a shipper, sign out, sign in. A welcome email arrives in the language you used on the site.
- **Forgot password:** the email arrives, and its link opens `https://www.sokan.app/reset-password?key=…` (not `app.sokan.app`). Setting a new password signs you in.
- Register a test forwarder, approve it in `/admin/forwarders`, post a request as the shipper. The forwarder gets a lead email, and its portal lists the lead.
- As the forwarder, request a top-up with a receipt. The manager can open the receipt from `/admin/topups` (this exercises `/private/files` through nginx).
- Open a forwarder profile from the directory, then hard-refresh the same URL. Both should render identically.
- `https://www.sokan.app/sitemap.xml` lists `https://www.sokan.app/...` URLs, including `/fa/` alternates. `curl -s https://www.sokan.app | grep og:image` shows `https://www.sokan.app/og-default.jpg`.
- Paste the home URL into a WhatsApp or Telegram chat: the share card shows the Sokan image.
- All the redirect checks in step 5 pass.
- `sudo supervisorctl status`: Frappe web, workers, scheduler and `sokan-frontend` all show RUNNING.
- `bench --site app.sokan.app sokan-check` reports nothing to fix.

Then delete the test accounts and records, or start over on a fresh site, before announcing.

## Redeploying after future changes

```bash
# backend changes
cd ~/frappe-bench/apps/sokan
git pull
cd ~/frappe-bench
bench --site app.sokan.app migrate
sudo supervisorctl restart all

# frontend changes (same repo)
cd ~/frappe-bench/apps/sokan/frontend
npm ci && npm run build
sudo supervisorctl restart sokan-frontend
```

A change to `frontend/.env` also needs `npm run build`, for the reason given in step 3.

Settings and content changed in `/admin` need no rebuild. The home page data is cached for 2 minutes in Frappe, and forwarder profiles for 5 minutes in Nuxt (`swr` route rules, held in memory). A `sokan-frontend` restart clears the Nuxt cache. If a profile still looks stale, check for a `.output/cache` or `.data` directory under `frontend/` and remove it.
