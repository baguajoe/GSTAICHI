import React, { useEffect, useRef, useState } from "react";
import { apiFetch } from "./api";

// Members' practice videos on "Ask Vincent" questions: the picker on the Ask page, and the player everywhere else.
// The server checks the plan, the limits and the real file size at every step; the checks here only give a
// friendlier message sooner, before a long upload.

const ALLOWED_EXTENSION = /\.(mp4|mov|webm)$/i;
const ALLOWED_TYPES = ["video/mp4", "video/quicktime", "video/webm"];
const HAS_EXTENSION = /\.[^./]+$/;

const minutes = (seconds) => `${Math.floor(seconds / 60)}:${String(Math.round(seconds % 60)).padStart(2, "0")}`;

// Phones often report no type for a video, so a file's own extension decides, as it does on the server
const isAllowedType = (file) => HAS_EXTENSION.test(file.name)
    ? ALLOWED_EXTENSION.test(file.name)
    : ALLOWED_TYPES.includes(file.type);

// The length in seconds, or null if this browser cannot read it (for example a phone format a computer can't play).
// iPhones only start reading after load() is called.
const readSeconds = (file) => new Promise((resolve) => {
    const video = document.createElement("video");
    const address = URL.createObjectURL(file);
    let timer = null;
    const finish = (seconds) => {
        clearTimeout(timer);
        video.removeAttribute("src");
        URL.revokeObjectURL(address);
        resolve(seconds);
    };
    timer = setTimeout(() => finish(null), 15000);
    video.preload = "metadata";
    video.muted = true;
    video.setAttribute("playsinline", "");
    video.onloadedmetadata = () => finish(Number.isFinite(video.duration) && video.duration > 0 ? video.duration : null);
    video.onerror = () => finish(null);
    video.src = address;
    video.load();
});

const sendFile = (url, file, contentType, onProgress, xhrRef) => new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhrRef.current = xhr;
    xhr.open("PUT", url);
    xhr.setRequestHeader("Content-Type", contentType);
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) onProgress(Math.floor((e.loaded / e.total) * 100)); };
    xhr.onload = () => (xhr.status >= 200 && xhr.status < 300 ? resolve() : reject(new Error("failed")));
    xhr.onerror = () => reject(new Error("failed"));
    xhr.onabort = () => reject(new Error("cancelled"));
    xhr.send(file);
});

// Up to one video on a question. Tells the form through onChange({ token, busy }).
export const QuestionVideoPicker = ({ allowance, teacher, onChange }) => {
    const [phase, setPhase] = useState("empty"); // empty, checking, uploading, saved
    const [percent, setPercent] = useState(0);
    const [error, setError] = useState(null);
    const [preview, setPreview] = useState(null);
    const [token, setToken] = useState(null);
    const xhrRef = useRef(null);
    const maxMb = Math.floor(allowance.video_max_bytes / 1024 ** 2);
    const maxMinutes = Math.floor(allowance.video_max_seconds / 60);

    useEffect(() => { onChange({ token, busy: phase === "checking" || phase === "uploading" }); }, [token, phase]);
    useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);
    useEffect(() => () => { if (xhrRef.current) xhrRef.current.abort(); }, []);

    const reset = () => {
        setPhase("empty");
        setPercent(0);
        setPreview(null);
        setToken(null);
    };

    const choose = async (e) => {
        const file = e.target.files && e.target.files[0];
        e.target.value = ""; // so choosing the same file again still works
        if (!file) return;
        setError(null);
        if (!isAllowedType(file)) return setError("Please choose an MP4, MOV or WebM video.");
        if (file.size > allowance.video_max_bytes) {
            return setError(`This video is ${Math.ceil(file.size / 1024 ** 2)} MB, and videos can be up to ${maxMb} MB. `
                + "Try a shorter clip, or record in 1080p instead of 4K.");
        }
        setPhase("checking");
        const seconds = await readSeconds(file);
        if (seconds !== null && Math.round(seconds) > allowance.video_max_seconds) {
            setPhase("empty");
            return setError(`This video is ${minutes(seconds)} long. Please choose one of ${maxMinutes} minutes or less. `
                + "You can trim it in your phone's Photos or Gallery app first.");
        }
        let upload = null;
        try {
            upload = await apiFetch("/api/tcc/questions/video/upload-url", {
                method: "POST",
                body: { filename: file.name, content_type: file.type, size: file.size, seconds: seconds === null ? null : Math.round(seconds) }
            });
            setPhase("uploading");
            await sendFile(upload.upload_url, file, upload.content_type, setPercent, xhrRef);
            xhrRef.current = null;
            await apiFetch("/api/tcc/questions/video/confirm", { method: "POST", body: { upload_token: upload.upload_token } });
            setPreview(URL.createObjectURL(file));
            setToken(upload.upload_token);
            setPhase("saved");
        } catch (err) {
            xhrRef.current = null;
            reset();
            if (err.message === "cancelled") return null;
            setError(err.message === "failed"
                ? "The upload stopped. Please check your internet connection and try again."
                : err.message);
        }
        return null;
    };

    const remove = async () => {
        const old = token;
        reset();
        setError(null);
        try {
            await apiFetch("/api/tcc/questions/video/remove", { method: "POST", body: { upload_token: old } });
        } catch (e) {
            // Nothing the member can do about this: a file left behind is cleaned up automatically
        }
    };

    if (allowance.videos_per_month <= 0) return null;

    const nextMonth = new Date(allowance.videos_next_at).toLocaleDateString(undefined, { month: "long", day: "numeric", timeZone: "UTC" });

    return (
        <div className="tcc-field tcc-question-video-picker">
            <label htmlFor="ask-video">Add a video (optional, up to {maxMinutes} minutes)</label>
            {allowance.videos_remaining <= 0 ? (
                <p className="tcc-field-hint">
                    You have sent {allowance.videos_per_month} video{allowance.videos_per_month === 1 ? "" : "s"} this month.
                    You can send your next video on {nextMonth}. You can still send your question without one.
                </p>
            ) : (
                <>
                    <p className="tcc-field-hint">
                        Show {teacher} your practice. On a phone you can choose a saved video or record a new one. MP4, MOV or
                        WebM, up to {maxMb} MB. You have {allowance.videos_remaining} left this month. Only you, {teacher} and
                        our staff can watch it, and it is deleted automatically 90 days after he answers.
                    </p>
                    {phase === "empty" && (
                        <label className="tcc-btn tcc-btn-outline tcc-file-label">
                            <span><i className="fas fa-video" aria-hidden="true"></i> Choose a video</span>
                            {/* video/* with no "capture", so phones offer both the camera and saved videos */}
                            <input id="ask-video" type="file" accept="video/*" className="tcc-visually-hidden" onChange={choose} />
                        </label>
                    )}
                    {phase === "checking" && <p role="status">Checking your video…</p>}
                    {phase === "uploading" && (
                        <div className="tcc-progress-wrap" role="status" aria-live="polite">
                            <p className="tcc-progress-label">Uploading <strong>{percent}%</strong></p>
                            <div className="tcc-progress" aria-hidden="true"><div className="tcc-progress-bar" style={{ width: `${percent}%` }} /></div>
                            <p>Please keep this page open until it finishes.</p>
                            <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => xhrRef.current && xhrRef.current.abort()}>Cancel</button>
                        </div>
                    )}
                    {phase === "saved" && (
                        <div className="tcc-member-video">
                            <p className="tcc-success" role="status">Your video is ready. It will be sent with your question.</p>
                            <video controls playsInline preload="metadata" src={preview} />
                            <button type="button" className="tcc-btn tcc-btn-outline" onClick={remove}>Remove and choose another</button>
                        </div>
                    )}
                    {error && <p className="tcc-error" role="alert">{error}</p>}
                </>
            )}
        </div>
    );
};

// A sent video. Watch addresses last about an hour, so a page left open asks for a new one once if playing fails.
export const QuestionVideoPlayer = ({ questionId, video, title }) => {
    const [current, setCurrent] = useState(video);
    const [tries, setTries] = useState(0);
    const [failed, setFailed] = useState(false);

    const retry = async () => {
        if (tries > 0) return setFailed(true);
        try {
            setCurrent(await apiFetch(`/api/tcc/questions/${questionId}/video`));
            setTries(1); // a new key starts a new player: one that failed stays failed even with a new address
        } catch (e) {
            setFailed(true);
        }
        return null;
    };

    const length = current.seconds ? ` (${minutes(current.seconds)})` : "";
    return (
        <div className="tcc-member-video">
            <p className="tcc-answer-title">{title}{length}</p>
            {current.watch_url && !failed && <video key={tries} controls playsInline preload="metadata" src={current.watch_url} onError={retry} />}
            {current.watch_url && failed && <p>We could not play this video just now. Please reload the page and try again.</p>}
            {!current.watch_url && <p>{current.note || "We could not load this video just now. Please reload the page."}</p>}
            {current.download_url && (
                <p className="tcc-field-hint">Does it not play? <a href={current.download_url}>Save the video</a> and open it on your computer.</p>
            )}
        </div>
    );
};
