# Launching a copy of Tai Chi Company for another teacher

This app was built so another teacher can run their own copy: every name, phone number, email, address,
color, price, section and text that members see comes from the database (**/admin → Site Settings**,
**Tiers**, **Plans and Prices**), not from the code. Each teacher gets **their own** database, storage,
video delivery, PayPal plans and keys. Nothing is shared between schools.

Allow about half a day. A developer is helpful for steps 1 and 9 but not required.
`docs/LAUNCH_CHECKLIST.md` has the detailed clicks for each service; this page says what to do
**differently** for the new teacher. In the examples the new school is **Lotus Tai Chi** at
`lotustaichi.com`. Replace those with the real names.

## What you need from the teacher

- [ ] School name, app name (what members see, e.g. "Lotus Tai Chi Online"), teacher's first name
      (used in "Ask Lotus", "Latest from ..."), name for the short-video corner (e.g. "Master Lin's Corner")
- [ ] Phone, contact email, address, an email for notices, copyright line, brand color (hex, e.g. `#1d4e89`)
- [ ] Their own domain name, with access to its DNS
- [ ] Prices for each level (monthly and yearly), and whether to offer founding-member prices
- [ ] A PayPal **Business** account in the teacher's name (payments go to them)
- [ ] A Gmail address to send emails from
- [ ] A square logo, at least 512 × 512 pixels, for the phone home-screen icon

## 1. A copy of the code

1. On GitHub, open `baguajoe/GSTAICHI` → **Fork** (or create a new private repository and push this
   code to it). Name it e.g. `lotus-taichi`.
2. Open it in Codespaces. All changes below are made in this new copy only.

## 2. Change the few teacher-specific files

| File | Change |
| --- | --- |
| `src/api/seed_data/tcc_catalog.py` | `DEFAULT_SITE_SETTINGS` (names, phone, email, address, color, terms), `TIERS` (level names, descriptions, prices). These are only the starting values; everything can be edited later in /admin. |
| `cloudflare-worker/wrangler.toml` | `name` (e.g. `lotus-taichi-media`), `routes` pattern (`media.lotustaichi.com`), `bucket_name` (`lotus-streams`), `ALLOWED_ORIGINS` (`https://lotustaichi.com,https://www.lotustaichi.com`), `BACKEND_URL` (`https://api.lotustaichi.com`) |
| `render.yaml` | Service names (`lotus-api`, `lotus-worker`), group name, `MEDIA_BASE_URL` (`https://media.lotustaichi.com`), `R2_MASTERS_BUCKET` / `R2_STREAMS_BUCKET` |
| `public/tcc-icons/` | Replace the 4 icons with the teacher's logo at the same sizes (192, 512, 512 maskable, 180 apple-touch) |
| `tools/videos.csv` | Replace with the teacher's own video list (only if bulk-uploading existing videos) |

Commit the changes.

The rest of the original gstaichi.org pages (classes, books, history, workshops) come along in the copy.
The app itself lives entirely under `/tai-chi-company`. Either point the new domain's home page at
`/tai-chi-company`, or ask a developer to remove the old pages. The web address of the corner page stays
`/tai-chi-company/vincents-corner`; the name members see comes from Site Settings.

## 3. New keys (never reuse another school's)

Make a new `KEY_ENCRYPTION_SECRET` and `MEDIA_TOKEN_SECRET` (LAUNCH_CHECKLIST step 1). Save them in the
teacher's password manager.

## 4. New storage

In the **teacher's** Cloudflare account (LAUNCH_CHECKLIST step 2): add their domain, create two private
buckets (e.g. `lotus-masters` and `lotus-streams`), add the CORS policy with **their** website addresses,
the lifecycle rule, and an R2 API token limited to those two buckets.

## 5. New database, API and worker

In the teacher's Render account (LAUNCH_CHECKLIST step 4):

1. **New PostgreSQL** database (never point two schools at one database).
2. **New Blueprint** from the new repository. Fill in the new database URL, the new keys, the new R2 values,
   `BACKEND_URL=https://api.lotustaichi.com`, `FRONTEND_URL=https://lotustaichi.com`, the teacher's Gmail.
3. The first deploy runs `flask setup-database`, which sees the empty database and creates all tables.
4. Custom domain `api.lotustaichi.com` on the API service.
5. API → **Shell**. Use `--no-videos` so the Gin Soon video list is **not** created:

   ```bash
   pipenv run flask seed-tcc --no-videos
   ```

   Do **not** run `seed-video-descriptions` or `seed-tcc-articles` (those add Gin Soon's own content).

## 6. Video delivery

Deploy the Worker from the new copy (`cloudflare-worker/README.md`) while logged in to the **teacher's**
Cloudflare account, with the new `MEDIA_TOKEN_SECRET`.

## 7. PayPal

Using the **teacher's** PayPal account (LAUNCH_CHECKLIST step 6): sandbox app, webhook to
`https://api.lotustaichi.com/api/tcc/paypal/webhook`, set the three PayPal values on Render. Check the
prices in **/admin → Plans and Prices** first (step 8), then run `scripts/create_paypal_plans.py`.

## 8. Fill in /admin

1. Website: create the teacher's account and yours at `https://lotustaichi.com/tai-chi-company/join`
   (after step 9), then in the Render Shell:
   `pipenv run flask set-role you@example.com admin` and `pipenv run flask set-role teacher@example.com teacher`.
2. `https://api.lotustaichi.com/admin` → **Site Settings**: check every field. App name, school name,
   teacher name, corner name, color, contact details, notification email, copyright line, Terms of Use
   text, article categories, video sections (labels may change; keep the `key` values as they are).
3. **Tiers**: names and descriptions. **Plans and Prices**: prices (before creating PayPal plans).
4. **Founding member end date**: empty while the founding offer is open.

## 9. Website

In `.env`: `BACKEND_URL=https://api.lotustaichi.com` and the teacher's `PAYPAL_CLIENT_ID`. Run
`npm run build` and upload `public/` to the teacher's web host (LAUNCH_CHECKLIST step 7).

## 10. Videos and articles

The teacher signs in and opens **Studio**: **Add a new video** (from a computer or straight from the phone)
and **Write a new article**. For a large existing library, use `tools/README.md` with the teacher's
R2 token and their own `videos.csv`.

## 11. Test, then go live

Run the final tests and switch PayPal to live exactly as in LAUNCH_CHECKLIST steps 11 and 12, using the
teacher's accounts.

## Keeping copies up to date

Improvements made to the original can be brought into a copy with GitHub's **Sync fork** (or `git pull`
from the original). The files changed in step 2 are the only ones that should differ between schools;
if a sync touches them, keep the teacher's values.
