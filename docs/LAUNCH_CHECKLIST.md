# Tai Chi Company: launch checklist

Do these in order. Each step says where to click and what to copy. Keep every key in a password manager
as you go. **Never** paste a secret into a chat, an email, GitHub, or a "Front-End" variable.

Where things run:

| Part | Where | Address |
| --- | --- | --- |
| Website (React pages) | HostGator | https://gstaichi.org |
| API, /admin | Render web service `gstaichi-api` | e.g. https://api.gstaichi.org |
| Video worker (prepares uploads) | Render background worker `tai-chi-company-worker` | none |
| Database | Render PostgreSQL | none |
| Video files | Cloudflare R2: `taichi-masters` (originals), `taichi-streams` (encrypted) | private |
| Video delivery | Cloudflare Worker | https://media.gstaichi.org |
| Payments | PayPal Subscriptions | none |

---

## 1. Make the two secret keys (5 minutes)

In the Codespaces terminal:

```bash
python -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"   # KEY_ENCRYPTION_SECRET
python -c "import secrets; print(secrets.token_urlsafe(48))"                              # MEDIA_TOKEN_SECRET
```

- **KEY_ENCRYPTION_SECRET** locks the video keys in the database. Save it somewhere safe **now**. If it is
  lost or changed, every uploaded video stops playing and has to be uploaded again.
- **MEDIA_TOKEN_SECRET** must be the same on Render and in the Cloudflare Worker.

## 2. Cloudflare: domain and R2 storage (20 minutes)

1. Sign in at https://dash.cloudflare.com. If `gstaichi.org` is not on Cloudflare yet, click
   **Add a domain** and follow the steps (Cloudflare tells you which two nameservers to set at your
   domain registrar). The Worker in step 5 needs this.
2. Left menu: **R2 Object Storage** → **Create bucket**. Name `taichi-masters`, location Automatic,
   **Create**. Repeat for `taichi-streams`.
3. For **each** bucket: **Settings** → make sure **Public access** is **Disabled** (no r2.dev URL, no
   custom domain). The Worker is the only way in.
4. Each bucket → **Settings** → **CORS policy** → **Add CORS policy**, paste this and **Save**
   (it lets the Studio upload straight from the browser; it does not make anything public):

   ```json
   [
     {
       "AllowedOrigins": ["https://gstaichi.org", "https://www.gstaichi.org"],
       "AllowedMethods": ["PUT", "GET", "HEAD"],
       "AllowedHeaders": ["*"],
       "ExposeHeaders": ["ETag"],
       "MaxAgeSeconds": 3600
     }
   ]
   ```

5. `taichi-masters` → **Settings** → **Object lifecycle rules** → **Add rule**: name `clean up`,
   **Abort incomplete multipart uploads after 7 days**. (Uploads that were never finished stop costing money.)
6. **R2 Object Storage** → **Manage R2 API Tokens** → **Create API token**: name `gstaichi-api`,
   permission **Object Read & Write**, **Apply to specific buckets only**: both buckets. **Create**.
   Copy **Access Key ID** → `R2_ACCESS_KEY_ID`, **Secret Access Key** → `R2_SECRET_ACCESS_KEY` (shown once).
   Your **Account ID** is on the R2 overview page → `R2_ACCOUNT_ID`.

## 3. Gmail for sending email (5 minutes)

1. Sign in to the Gmail account that should send the emails.
2. https://myaccount.google.com/security → turn on **2-Step Verification** if it is off.
3. https://myaccount.google.com/apppasswords → name it `gstaichi` → **Create**. Copy the 16-letter
   password → `GMAIL_PASSWORD`. The address → `GMAIL`.

## 4. Render: API and worker (30 minutes)

You need a paid Render plan for the background worker (Starter is enough to begin with).

1. Sign in at https://dashboard.render.com.
2. **Database**: if the site already has a Render PostgreSQL database, open it and copy the
   **Internal Database URL** → `DATABASE_URL`. Otherwise **New** → **PostgreSQL**, name `gstaichi-db`,
   same region as below, **Create**, then copy its Internal Database URL.
3. **New** → **Blueprint** → connect the GitHub repository `baguajoe/GSTAICHI`, branch
   `tai-chi-company` (or `main` once merged). Render reads `render.yaml` and shows the API, the worker
   and the shared settings group. Fill in every value it asks for:
   - `DATABASE_URL` (step 4.2), `KEY_ENCRYPTION_SECRET` and `MEDIA_TOKEN_SECRET` (step 1)
   - `BACKEND_URL` = `https://api.gstaichi.org`, `FRONTEND_URL` = `https://gstaichi.org`
   - `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` (step 2), `GMAIL`, `GMAIL_PASSWORD` (step 3)
   - PayPal values: leave empty for now (step 6)
   - `REDIS_URL`: leave empty

   **Apply**. The first build takes about 10 minutes. The build runs `flask setup-database`, which brings
   the database up to date.
   *If the API already exists in Render from before*, you can instead add the missing variables to it by
   hand (Environment tab) and create only the worker: **New** → **Background Worker** → this repository →
   Runtime **Docker**, Dockerfile path `./Dockerfile.worker`, same variables as the shared group.
4. API service → **Settings** → **Custom Domains** → add `api.gstaichi.org`. Render shows a CNAME
   record; add it in Cloudflare (**DNS** → **Add record**, type CNAME, name `api`, target as shown,
   proxy status **DNS only**). Wait for the green check.
5. API service → **Shell**, and run once (creates tiers, plans, settings and the 21 placeholder videos):

   ```bash
   pipenv run flask seed-tcc
   pipenv run flask seed-video-descriptions
   pipenv run flask seed-tcc-articles
   ```

6. Worker → **Logs** should say `Worker started`.

## 5. Cloudflare Worker for media.gstaichi.org (15 minutes)

Follow `cloudflare-worker/README.md` (Deploy). In `wrangler.toml` set `BACKEND_URL = "https://api.gstaichi.org"`.
Use the same `MEDIA_TOKEN_SECRET` as on Render.

## 6. PayPal in sandbox (test) mode (30 minutes)

1. https://developer.paypal.com → sign in with the school's PayPal account → **Apps & Credentials**,
   switch at the top to **Sandbox** → **Create App** (name `Tai Chi Company`, type Merchant).
   Copy **Client ID** → `PAYPAL_SANDBOX_CLIENT_ID` and **Secret** → `PAYPAL_SANDBOX_CLIENT_SECRET`.
   (The `PAYPAL_SANDBOX_*` names keep the shop's live `PAYPAL_CLIENT_ID` working while you test.)
2. In that app → **Add Webhook**: URL `https://api.gstaichi.org/api/tcc/paypal/webhook`, events:
   `Billing subscription activated`, `cancelled`, `expired`, `re-activated`, `suspended`, `updated`, and
   `Payment sale completed`. **Save**, then copy the **Webhook ID** → `PAYPAL_SANDBOX_WEBHOOK_ID`.
3. Render → API → **Environment**: set `PAYPAL_MODE=sandbox`, `PAYPAL_SANDBOX_CLIENT_ID`,
   `PAYPAL_SANDBOX_CLIENT_SECRET`, `PAYPAL_SANDBOX_WEBHOOK_ID`. Save (the API restarts).
4. Render → API → **Shell**: create the PayPal product and 6 sandbox plans from the prices in /admin
   (saved as the sandbox plan IDs):

   ```bash
   pipenv run python scripts/create_paypal_plans.py
   ```

5. developer.paypal.com → **Testing Tools** → **Sandbox Accounts**: use the **Personal** account's
   email and password to "pay" when you test.

## 7. Build and upload the website to HostGator (15 minutes)

1. In Codespaces, set these in `.env`: `BACKEND_URL=https://api.gstaichi.org`, `PAYPAL_MODE=sandbox`,
   `PAYPAL_SANDBOX_CLIENT_ID=` the sandbox Client ID (keep the shop's live `PAYPAL_CLIENT_ID`). Then:

   ```bash
   npm run build
   ```

2. Upload the **contents** of the `public/` folder to the site's folder on HostGator (cPanel →
   **File Manager** → `public_html`), the same way the site is updated today. Keep the existing
   `.htaccess` so addresses like `/tai-chi-company/library` open the app.

## 8. Your admin account and Vincent's teacher account (5 minutes)

1. On https://gstaichi.org/tai-chi-company/join create your own account, and have Vincent create his.
2. Render → API → **Shell**:

   ```bash
   pipenv run flask set-role you@example.com admin
   pipenv run flask set-role vincent@example.com teacher
   ```

3. Sign in at https://api.gstaichi.org/admin with your email and password.

## 9. Check the settings in /admin (10 minutes)

- **Tai Chi Company → Site Settings**: phone, email, address, notification email (gets new-subscriber,
  cancellation and question emails), copyright line, Terms of Use text, teacher name, corner name.
- **Founding member end date**: members who join before it keep their price for life. Leave it empty
  until you decide; set it before announcing the end of the offer.
- **Plans and Prices**: 6 plans, each with a PayPal plan ID starting with `P-`.

## 10. Upload the video library

- **The existing 21 videos (bulk)**: on your Windows PC follow `tools/README.md`. Start with one or two
  videos, check they play, then run the rest (it skips videos already done).
- **New videos**: Vincent uses **Studio** on the site (computer or phone). The worker prepares them
  (about the length of the video); he gets an email when each is Ready.

## 11. Final tests (sandbox)

Work through the page-by-page test list (the one delivered with Phase 9, also in the commit history).
At minimum:

- [ ] Free account: watch the free sample; other videos show a lock; articles show "Subscribe to read".
- [ ] Subscribe with the PayPal sandbox Personal account; the library unlocks; the notification email arrives.
- [ ] Play a video on a computer and a phone; the moving watermark shows your email; a third device is refused.
- [ ] Upgrade, then cancel, from Account; access continues until the date shown.
- [ ] Vincent uploads a short phone video in Studio; it becomes Ready and plays; he gets the email.
- [ ] Ask Vincent a question as a member; answer it in Studio; the member gets the email.
- [ ] /admin dashboard shows the test subscriber and the most-watched video.

## 12. Switch PayPal to live (launch day, 20 minutes)

1. developer.paypal.com → switch to **Live** → **Create App** (or open the live app the shop uses) →
   copy the **Live Client ID** and **Secret**.
2. In the live app → **Add Webhook** with the same URL and events as step 6.2 → copy the **Live Webhook ID**.
3. Render → API → **Environment**: `PAYPAL_MODE=live`, and the live `PAYPAL_CLIENT_ID`,
   `PAYPAL_CLIENT_SECRET`, `PAYPAL_WEBHOOK_ID`. Save.
4. Render → API → **Shell**: make live PayPal plans (saved next to the sandbox ones, which are kept):

   ```bash
   pipenv run python scripts/create_paypal_plans.py --dry-run   # check: 6 plans, right prices
   pipenv run python scripts/create_paypal_plans.py
   ```

5. In `/admin` → **Users**, remove the plan from test accounts that "paid" in sandbox (set Paid level 0,
   status none) or delete those accounts, so nobody keeps access from a test payment.
6. Rebuild the website with `PAYPAL_MODE=live` in `.env` (`npm run build`) and upload
   `public/` to HostGator again (step 7). **The website and Render must use the same mode.**
7. Make one real subscription with your own card at the lowest price, check it in /admin, then cancel it.

## 13. After launch

- Check **/admin** (Dashboard) every few days: accounts to check, failed videos, unanswered questions.
- To change a price: in **Plans and Prices** untick **Is Active** on the old plan, add a new plan with the
  new price, run `scripts/create_paypal_plans.py`. Members already subscribed keep their price.
- Back up `KEY_ENCRYPTION_SECRET` and turn on Render's database backups.
