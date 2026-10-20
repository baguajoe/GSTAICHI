# Media Worker (media.gstaichi.org)

This small Cloudflare Worker is the only way into the private `taichi-streams` bucket. It:

- serves video files only with a valid, short-lived signed link created by the site for a signed-in member,
- adds that link's token to every piece of the video and to the key address, so iPhone, iPad, Mac Safari,
  AirPlay and Chromecast work too,
- refuses requests coming from other websites,
- serves thumbnails and article pictures without a token (they are not secret),
- tells the site about each piece it serves, so downloading faster than anyone could watch is flagged
  in **/admin → Security Events**.

The video pieces are encrypted. Even with a link, a piece is useless without the key, and the site gives the
key only to an active, paid-up playback session.

## Deploy (about 15 minutes, one time)

You need: a Cloudflare account with **gstaichi.org** added to it, the two R2 buckets created
(see docs/LAUNCH_CHECKLIST.md), Node.js 18 or newer, and the `MEDIA_TOKEN_SECRET` value from Render.

1. Open a terminal in this folder:

   ```bash
   cd cloudflare-worker
   ```

2. Log in to Cloudflare (a browser window opens; click **Allow**):

   ```bash
   npx wrangler login
   ```

3. Check the settings in `wrangler.toml`:
   - `routes`: your media address (`media.gstaichi.org`).
   - `bucket_name`: `taichi-streams`.
   - `ALLOWED_ORIGINS`: the site addresses members use, for example `https://gstaichi.org,https://www.gstaichi.org`.
   - `BACKEND_URL`: the site's API address (the same as `BACKEND_URL` on Render).

4. Store the token secret. Paste **exactly** the same value as `MEDIA_TOKEN_SECRET` on Render when asked:

   ```bash
   npx wrangler secret put MEDIA_TOKEN_SECRET
   ```

5. Deploy:

   ```bash
   npx wrangler deploy
   ```

   Cloudflare creates the `media.gstaichi.org` address and its certificate automatically (it can take a
   few minutes the first time).

6. Check it is answering. This should say **Not found.** (which is correct: no file was asked for):

   ```bash
   curl https://media.gstaichi.org/
   ```

7. On Render, set `MEDIA_BASE_URL=https://media.gstaichi.org`.

## Test it

```bash
npm test
```

runs the automated checks in `test/worker.test.mjs` (no extra packages needed).

After deploying, sign in to the site as a member with a plan, open a Ready video and press Play. In the
browser's developer tools (Network tab) the video pieces come from `media.gstaichi.org` with `?t=...`.
Copying one of those addresses into another website's page, or waiting more than 6 hours, gives
"This link has expired".

## Changing things later

- **New site address**: update `ALLOWED_ORIGINS` and `BACKEND_URL`, then `npx wrangler deploy` again.
- **New MEDIA_TOKEN_SECRET**: change it on Render and with `npx wrangler secret put MEDIA_TOKEN_SECRET`
  at the same time. Videos already playing stop and members press Play again.
- **Logs**: `npx wrangler tail` shows requests live.
