import { apiFetch } from "./api";

// Uploads a video file straight from the browser (or phone) to private storage, in 16 MB pieces.
// Pieces are retried if the connection drops, and if the page is reloaded, choosing the same file
// again continues from where it stopped (the server remembers which pieces arrived).

export const MAX_BYTES = 10 * 1024 ** 3;
const PARALLEL = 3;
const URL_BATCH = 20;
const MAX_TRIES = 8;

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const waitUntilOnline = () => new Promise(resolve => {
    if (navigator.onLine !== false) return resolve();
    window.addEventListener("online", () => resolve(), { once: true });
});

const putPart = (url, blob, onProgress, isCancelled) => new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", url);
    xhr.upload.onprogress = (e) => onProgress(e.loaded);
    xhr.onload = () => {
        const etag = xhr.getResponseHeader("ETag");
        if (xhr.status >= 200 && xhr.status < 300 && etag) resolve(etag);
        else reject(Object.assign(new Error(`Upload piece failed (${xhr.status})`), { status: xhr.status }));
    };
    xhr.onerror = () => reject(new Error("network"));
    xhr.ontimeout = () => reject(new Error("timeout"));
    xhr.timeout = 10 * 60 * 1000;
    if (isCancelled()) return reject(new Error("cancelled"));
    xhr.send(blob);
});

export const formatBytes = (bytes) => {
    if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
    return `${Math.max(1, Math.round(bytes / 1024 ** 2))} MB`;
};

// onProgress({ sent, total, status }) ; returns the updated studio video. control.cancel() stops it.
export const uploadVideoFile = async ({ videoId, file, onProgress, control = {} }) => {
    if (file.size > MAX_BYTES) throw new Error("This file is bigger than 10 GB. Please make it shorter or smaller and try again.");
    let cancelled = false;
    control.cancel = () => { cancelled = true; };
    const isCancelled = () => cancelled;

    let wakeLock = null;
    try {
        if (navigator.wakeLock) wakeLock = await navigator.wakeLock.request("screen"); // keep the phone awake
    } catch (e) {
        wakeLock = null;
    }

    try {
        const start = await apiFetch(`/api/tcc/studio/videos/${videoId}/upload/start`, {
            method: "POST", body: { filename: file.name, size: file.size, content_type: file.type || "video/mp4" }
        });
        const partSize = start.part_size;
        const totalParts = Math.ceil(file.size / partSize);
        const done = new Map(start.parts.map(p => [p.part_number, p.etag]));
        const sizeOf = (n) => Math.min(partSize, file.size - (n - 1) * partSize);
        let finishedBytes = [...done.keys()].reduce((sum, n) => sum + sizeOf(n), 0);
        const inFlight = new Map();
        const report = (status) => onProgress({
            sent: finishedBytes + [...inFlight.values()].reduce((a, b) => a + b, 0), total: file.size, status
        });
        report(start.resumed ? "Continuing where the upload stopped…" : "Uploading…");

        const todo = [];
        for (let n = 1; n <= totalParts; n++) if (!done.has(n)) todo.push(n);
        const urls = {};
        const urlFor = async (n) => {
            if (!urls[n]) {
                const batch = todo.filter(x => !urls[x] && x >= n).slice(0, URL_BATCH);
                const result = await apiFetch(`/api/tcc/studio/videos/${videoId}/upload/parts`, {
                    method: "POST", body: { part_numbers: batch.length ? batch : [n] }
                });
                Object.assign(urls, result.urls);
            }
            return urls[n];
        };

        const uploadOne = async (n) => {
            for (let attempt = 1; ; attempt++) {
                if (cancelled) throw new Error("cancelled");
                await waitUntilOnline();
                try {
                    const blob = file.slice((n - 1) * partSize, (n - 1) * partSize + sizeOf(n));
                    const etag = await putPart(await urlFor(n), blob, (loaded) => {
                        inFlight.set(n, loaded);
                        report("Uploading…");
                    }, isCancelled);
                    inFlight.delete(n);
                    done.set(n, etag);
                    finishedBytes += sizeOf(n);
                    report("Uploading…");
                    return;
                } catch (e) {
                    inFlight.delete(n);
                    if (cancelled || attempt >= MAX_TRIES) throw e;
                    if (e.status === 403) delete urls[n]; // address expired: get a fresh one
                    report("The connection dropped. Trying again…");
                    await sleep(Math.min(30000, 1000 * 2 ** attempt));
                }
            }
        };

        const queue = [...todo];
        const workers = Array.from({ length: Math.min(PARALLEL, queue.length) }, async () => {
            try {
                while (queue.length) await uploadOne(queue.shift());
            } catch (e) {
                cancelled = true; // stop the other pieces too; choosing the file again continues from here
                throw e;
            }
        });
        await Promise.all(workers);

        report("Finishing…");
        return await apiFetch(`/api/tcc/studio/videos/${videoId}/upload/complete`, {
            method: "POST", body: { parts: [...done.entries()].map(([part_number, etag]) => ({ part_number, etag })) }
        });
    } finally {
        if (wakeLock) wakeLock.release().catch(() => {});
    }
};

// One picture (article picture, cover or video thumbnail) straight to storage. Returns { path, url }.
export const uploadPicture = async (file, endpoint = "/api/tcc/studio/images") => {
    if (!/^image\/(jpeg|png|webp|gif)$/.test(file.type)) throw new Error("Please choose a JPG or PNG picture.");
    const target = await apiFetch(endpoint, { method: "POST", body: { content_type: file.type, size: file.size } });
    const response = await fetch(target.upload_url, { method: "PUT", body: file, headers: { "Content-Type": file.type } });
    if (!response.ok) throw new Error("The picture could not be uploaded. Please try again.");
    return { path: target.path, url: target.url };
};
