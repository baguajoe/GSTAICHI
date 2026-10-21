/*
 * Tai Chi Company media Worker (media.<your domain>), bound to the private taichi-streams R2 bucket.
 *
 * - Video files (.m3u8 playlists, .ts pieces, chapters.vtt) are served only with a valid signed token:
 *     ?t=<expiry>.<playback session id>.<signature>
 *   signature = base64url(HMAC-SHA256(MEDIA_TOKEN_SECRET, "<expiry>.<session id>.<slug>")), made by the
 *   backend (src/api/media_tokens.py). A token only opens files in its own video's folder.
 * - Playlists are rewritten so every piece, and the key address, carries the token. Safari, AirPlay and
 *   Chromecast then work without extra headers. The pieces are AES-128 encrypted; the key only comes
 *   from the backend for an active, paid-up playback session.
 * - Requests whose Origin or Referer is another website are refused. Requests with neither header are
 *   allowed because Apple TV (AirPlay), Chromecast and iPhone's player do not send them; they still need the token.
 * - Thumbnails (<slug>/thumbs/*.jpg) and cover pictures (article-images/*) are not secret and need no token.
 * - Photos inside articles and video descriptions (article-private/*) need a token signed for that one
 *   photo: the signature covers the photo's whole path instead of a video slug.
 * - Each piece served is reported to the backend in the background (BACKEND_URL), so downloading much
 *   faster than real-time playback can be flagged.
 */

const TYPES = {
  m3u8: "application/vnd.apple.mpegurl",
  ts: "video/mp2t",
  vtt: "text/vtt; charset=utf-8",
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  png: "image/png",
  webp: "image/webp",
  gif: "image/gif",
};

const PUBLIC_PATH = /^(?:[a-z0-9][a-z0-9-]*\/thumbs\/[\w.-]+\.(?:jpg|jpeg|png|webp)|article-images\/[\w.-]+\.(?:jpg|jpeg|png|webp|gif))$/;
const PROTECTED_PATH = /^[a-z0-9][a-z0-9-]*\/[\w./-]+\.(?:m3u8|ts|vtt)$/;
const PRIVATE_PHOTO_PATH = /^article-private\/[a-f0-9]{24}\.(?:jpg|png|webp|gif)$/;

const encoder = new TextEncoder();

function base64url(bytes) {
  let s = "";
  for (const b of new Uint8Array(bytes)) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromBase64url(s) {
  const padded = s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4);
  return Uint8Array.from(atob(padded), (c) => c.charCodeAt(0));
}

async function hmacKey(secret) {
  return crypto.subtle.importKey("raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);
}

// Returns the playback session id, or null if the token is missing, expired, forged or for another video.
export async function verifyToken(token, slug, secret, now = Date.now() / 1000) {
  const parts = (token || "").split(".");
  if (parts.length !== 3) return null;
  const [expires, sessionId, signature] = parts;
  if (!/^\d+$/.test(expires) || Number(expires) < now) return null;
  let sig;
  try {
    sig = fromBase64url(signature);
  } catch {
    return null;
  }
  const key = await hmacKey(secret);
  const ok = await crypto.subtle.verify("HMAC", key, sig, encoder.encode(`${expires}.${sessionId}.${slug}`));
  return ok ? sessionId : null;
}

function withToken(uri, token) {
  return uri + (uri.includes("?") ? "&" : "?") + "t=" + encodeURIComponent(token);
}

// Adds the token to every piece/playlist line and to URI="..." attributes (the key address included).
export function rewritePlaylist(text, token) {
  return text
    .split("\n")
    .map((line) => {
      const trimmed = line.trim();
      if (!trimmed) return line;
      if (trimmed.startsWith("#")) {
        return line.replace(/URI="([^"]+)"/g, (_m, uri) => `URI="${withToken(uri, token)}"`);
      }
      return withToken(trimmed, token);
    })
    .join("\n");
}

function allowedOrigins(env) {
  return `${env.ALLOWED_ORIGINS || ""},${env.CAST_ORIGINS || ""}`
    .split(",")
    .map((o) => o.trim().replace(/\/$/, ""))
    .filter(Boolean);
}

// { ok, corsOrigin }: refuse other websites; allow requests with no Origin/Referer (TVs, native players).
export function checkOrigin(request, env) {
  const allowed = allowedOrigins(env);
  const origin = request.headers.get("Origin");
  if (origin) {
    return allowed.includes(origin) ? { ok: true, corsOrigin: origin } : { ok: false };
  }
  const referer = request.headers.get("Referer");
  if (referer) {
    let refOrigin;
    try {
      refOrigin = new URL(referer).origin;
    } catch {
      return { ok: false };
    }
    return allowed.includes(refOrigin) ? { ok: true, corsOrigin: null } : { ok: false };
  }
  return { ok: true, corsOrigin: null };
}

function corsHeaders(corsOrigin) {
  const h = new Headers();
  if (corsOrigin) {
    h.set("Access-Control-Allow-Origin", corsOrigin);
    h.set("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS");
    h.set("Access-Control-Allow-Headers", "Range");
    h.set("Access-Control-Expose-Headers", "Content-Length, Content-Range, Accept-Ranges");
    h.set("Access-Control-Max-Age", "86400");
  }
  h.set("Vary", "Origin");
  return h;
}

function deny(status, message, cors) {
  const h = corsHeaders(cors);
  h.set("Content-Type", "text/plain; charset=utf-8");
  h.set("Cache-Control", "no-store");
  return new Response(message, { status, headers: h });
}

async function reportPiece(env, sessionId, slug) {
  if (!env.BACKEND_URL) return;
  const body = JSON.stringify({ session: sessionId, slug, count: 1 });
  const key = await hmacKey(env.MEDIA_TOKEN_SECRET);
  const sig = await crypto.subtle.sign("HMAC", key, encoder.encode(body));
  const hex = [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
  try {
    await fetch(`${env.BACKEND_URL.replace(/\/$/, "")}/api/tcc/media/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Report-Signature": hex },
      body,
    });
  } catch {
    // Reporting must never break playback
  }
}

export default {
  async fetch(request, env, ctx) {
    const { ok, corsOrigin } = checkOrigin(request, env);
    if (!ok) return deny(403, "Not allowed from this website.");
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders(corsOrigin) });
    if (request.method !== "GET" && request.method !== "HEAD") return deny(405, "Method not allowed.", corsOrigin);

    const url = new URL(request.url);
    let path;
    try {
      path = decodeURIComponent(url.pathname.replace(/^\/+/, ""));
    } catch {
      return deny(404, "Not found.", corsOrigin);
    }
    if (path.includes("..") || path.includes("//")) return deny(404, "Not found.", corsOrigin);
    const ext = path.split(".").pop().toLowerCase();

    let sessionId = null;
    let token = null;
    const slug = path.split("/")[0];
    if (PUBLIC_PATH.test(path)) {
      // thumbnails and cover pictures: no token needed
    } else if (PRIVATE_PHOTO_PATH.test(path)) {
      token = url.searchParams.get("t");
      sessionId = await verifyToken(token, path, env.MEDIA_TOKEN_SECRET);
      if (!sessionId) return deny(403, "This link has expired. Please reload the page.", corsOrigin);
    } else if (PROTECTED_PATH.test(path)) {
      token = url.searchParams.get("t");
      sessionId = await verifyToken(token, slug, env.MEDIA_TOKEN_SECRET);
      if (!sessionId) return deny(403, "This link has expired. Please press Play again.", corsOrigin);
    } else {
      return deny(404, "Not found.", corsOrigin);
    }

    const isPlaylist = ext === "m3u8";
    const object = await env.STREAMS.get(path, isPlaylist ? {} : { range: request.headers });
    if (!object) return deny(404, "Not found.", corsOrigin);

    const headers = corsHeaders(corsOrigin);
    headers.set("Content-Type", TYPES[ext] || "application/octet-stream");
    headers.set("X-Content-Type-Options", "nosniff");
    if (object.httpEtag) headers.set("ETag", object.httpEtag);

    if (isPlaylist) {
      headers.set("Cache-Control", "private, no-store");
      const text = rewritePlaylist(await object.text(), token);
      return new Response(request.method === "HEAD" ? null : text, { status: 200, headers });
    }

    headers.set("Cache-Control", sessionId ? "private, max-age=3600" : "public, max-age=86400");
    headers.set("Accept-Ranges", "bytes");
    let status = 200;
    if (object.range && request.headers.get("Range")) {
      const { offset = 0, length = object.size - offset } = object.range;
      headers.set("Content-Range", `bytes ${offset}-${offset + length - 1}/${object.size}`);
      headers.set("Content-Length", String(length));
      status = 206;
    } else {
      headers.set("Content-Length", String(object.size));
    }
    if (ext === "ts" && sessionId && request.method === "GET") {
      ctx.waitUntil(reportPiece(env, sessionId, slug));
    }
    return new Response(request.method === "HEAD" ? null : object.body, { status, headers });
  },
};
