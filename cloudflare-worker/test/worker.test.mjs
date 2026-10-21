// Run with: cd cloudflare-worker && npm test   (Node 18+; no packages needed)
import { test } from "node:test";
import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import worker, { verifyToken, rewritePlaylist, checkOrigin } from "../src/index.js";

const SECRET = "test-secret-that-is-long-enough-1234567890";
const env = {
  MEDIA_TOKEN_SECRET: SECRET,
  ALLOWED_ORIGINS: "https://gstaichi.org,https://www.gstaichi.org",
  CAST_ORIGINS: "https://www.gstatic.com",
};

// Same algorithm as src/api/media_tokens.py
function sign(slug, session, expires) {
  const sig = createHmac("sha256", SECRET).update(`${expires}.${session}.${slug}`).digest("base64url");
  return `${expires}.${session}.${sig}`;
}

const files = {
  "fundamentals/master.m3u8": "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1\n720p/index.m3u8\n",
  "fundamentals/720p/index.m3u8":
    '#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI="https://gstaichi.org/api/tcc/key/fundamentals",IV=0x01\n#EXTINF:6.0,\nseg_0000.ts\n#EXT-X-ENDLIST\n',
  "fundamentals/720p/seg_0000.ts": "0123456789",
  "fundamentals/thumbs/thumb_30_480.jpg": "jpg",
  "article-private/0123456789abcdef01234567.webp": "photo",
  "article-private/fedcba9876543210fedcba98.webp": "other photo",
};
const bucket = {
  async get(key, opts = {}) {
    if (!(key in files)) return null;
    const data = new TextEncoder().encode(files[key]);
    let range;
    const header = opts.range && opts.range.get && opts.range.get("Range");
    if (header) {
      const [, a, b] = /bytes=(\d+)-(\d*)/.exec(header);
      range = { offset: +a, length: (b ? +b : data.length - 1) - +a + 1 };
    }
    const slice = range ? data.slice(range.offset, range.offset + range.length) : data;
    return { size: data.length, range, httpEtag: '"e"', body: slice, text: async () => files[key] };
  },
};
const ctx = { waits: [], waitUntil(p) { this.waits.push(p); } };
const get = (path, headers = {}) => worker.fetch(new Request(`https://media.gstaichi.org/${path}`, { headers }), { ...env, STREAMS: bucket }, ctx);
const future = Math.floor(Date.now() / 1000) + 3600;

test("valid token opens the video's files", async () => {
  const t = sign("fundamentals", "sess-1", future);
  const res = await get(`fundamentals/master.m3u8?t=${t}`, { Origin: "https://gstaichi.org" });
  assert.equal(res.status, 200);
  assert.equal(res.headers.get("Access-Control-Allow-Origin"), "https://gstaichi.org");
  assert.match(await res.text(), new RegExp(`720p/index.m3u8\\?t=${t.replace(/\./g, "\\.")}`));
});

test("playlist rewriting adds the token to pieces and the key address", async () => {
  const t = sign("fundamentals", "sess-1", future);
  const text = await (await get(`fundamentals/720p/index.m3u8?t=${t}`)).text();
  assert.ok(text.includes(`seg_0000.ts?t=${encodeURIComponent(t)}`));
  assert.ok(text.includes(`URI="https://gstaichi.org/api/tcc/key/fundamentals?t=${encodeURIComponent(t)}"`));
});

test("missing, expired, forged or other-video tokens are refused", async () => {
  assert.equal((await get("fundamentals/master.m3u8")).status, 403);
  assert.equal((await get(`fundamentals/master.m3u8?t=${sign("fundamentals", "s", 1000)}`)).status, 403);
  assert.equal((await get(`fundamentals/master.m3u8?t=${sign("other-video", "s", future)}`)).status, 403);
  const t = sign("fundamentals", "s", future);
  assert.equal((await get(`fundamentals/master.m3u8?t=${t.slice(0, -2)}xx`)).status, 403);
});

test("other websites are refused; TVs with no Origin/Referer are allowed", async () => {
  const t = sign("fundamentals", "s", future);
  assert.equal((await get(`fundamentals/master.m3u8?t=${t}`, { Origin: "https://evil.example" })).status, 403);
  assert.equal((await get(`fundamentals/master.m3u8?t=${t}`, { Referer: "https://evil.example/page" })).status, 403);
  assert.equal((await get(`fundamentals/master.m3u8?t=${t}`, { Referer: "https://www.gstaichi.org/tai-chi-company/watch/x" })).status, 200);
  assert.equal((await get(`fundamentals/master.m3u8?t=${t}`, { Origin: "https://www.gstatic.com" })).status, 200);
  assert.equal((await get(`fundamentals/master.m3u8?t=${t}`)).status, 200);
});

test("thumbnails are public; unknown paths and path tricks are 404", async () => {
  const res = await get("fundamentals/thumbs/thumb_30_480.jpg");
  assert.equal(res.status, 200);
  assert.equal(res.headers.get("Content-Type"), "image/jpeg");
  assert.equal((await get("fundamentals/../secret.ts?t=x")).status, 404);
  assert.equal((await get("fundamentals/master.mp4")).status, 404);
});

test("pieces support Range requests and are reported", async () => {
  ctx.waits = [];
  const t = sign("fundamentals", "sess-9", future);
  const res = await get(`fundamentals/720p/seg_0000.ts?t=${t}`, { Range: "bytes=2-5" });
  assert.equal(res.status, 206);
  assert.equal(res.headers.get("Content-Range"), "bytes 2-5/10");
  assert.equal(await res.text(), "2345");
  assert.equal(ctx.waits.length, 1);
});

test("helpers", async () => {
  assert.equal(await verifyToken(sign("a", "s1", future), "a", SECRET), "s1");
  assert.equal(rewritePlaylist("#EXTM3U\nx.ts", "T"), "#EXTM3U\nx.ts?t=T");
  assert.equal(checkOrigin(new Request("https://m/x", { headers: { Origin: "https://gstaichi.org/" } }), env).ok, false);
});

test("article photos need a token for that exact photo", async () => {
  const photo = "article-private/0123456789abcdef01234567.webp";
  const other = "article-private/fedcba9876543210fedcba98.webp";
  const t = sign(photo, "article-1", future);
  const ok = await get(`${photo}?t=${t}`, { Origin: "https://gstaichi.org" });
  assert.equal(ok.status, 200);
  assert.equal(ok.headers.get("Content-Type"), "image/webp");
  assert.equal(ok.headers.get("Cache-Control"), "private, max-age=3600");
  assert.equal((await get(photo)).status, 403);
  assert.equal((await get(`${other}?t=${t}`)).status, 403);
  assert.equal((await get(`${photo}?t=${sign(photo, "article-1", 1000)}`)).status, 403);
  assert.equal((await get(`fundamentals/master.m3u8?t=${t}`)).status, 403);
});
