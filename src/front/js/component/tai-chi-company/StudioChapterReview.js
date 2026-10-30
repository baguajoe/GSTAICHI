import React, { useRef, useState } from "react";
import { apiFetch } from "./api";
import ProtectedPlayer from "./ProtectedPlayer";
import { FormMessage } from "./FormField";

// "Review chapters" on the Studio's edit page: the draft chapters made by tools/draft_chapters.py.
// Members do not see them until the teacher presses "Publish chapters".

export const toSeconds = (text) => {
    const parts = String(text).trim().split(":").map(Number);
    if (parts.some(isNaN)) return null;
    return parts.reduce((total, n) => total * 60 + n, 0);
};
export const toClock = (seconds) => {
    const s = Math.max(0, Math.floor(seconds));
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = String(s % 60).padStart(2, "0");
    return h ? `${h}:${String(m).padStart(2, "0")}:${sec}` : `${m}:${sec}`;
};

const SOURCES = {
    marker: "From the video file",
    title: "Title card on screen",
    speech: "Said in the narration",
    scene: "Change of scene",
    even: "Added to fill a long gap",
    teacher: "Added by you"
};

const rowsFrom = (draft) => ((draft && draft.chapters) || []).map((c, i) => ({
    key: i, time: toClock(c.start), label: c.label || "", source: c.source, detail: c.detail || ""
}));

const timeOf = (row) => (row.time.trim() ? toSeconds(row.time) : null);
const byTime = (rows) => [...rows].sort((a, b) => (timeOf(a) ?? Infinity) - (timeOf(b) ?? Infinity));

const StudioChapterReview = ({ video, onChange }) => {
    const player = useRef(null);
    const [rows, setRows] = useState(() => rowsFrom(video.chapters_draft));
    const nextKey = useRef(rows.length);
    const [current, setCurrent] = useState(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const draft = video.chapters_draft || {};

    const update = (key, field, value) => {
        setSuccess(null);
        setRows(rows.map(r => (r.key === key ? { ...r, [field]: value } : r)));
    };
    const jump = (row) => {
        const seconds = timeOf(row);
        if (seconds === null) {
            setError(`"${row.time}" is not a time. Please write it like 2:30.`);
            return;
        }
        setError(null);
        setCurrent(row.key);
        player.current.seek(seconds);
    };
    const setToNow = (key) => update(key, "time", toClock(player.current.currentTime()));
    const add = () => {
        const seconds = player.current && player.current.isPlaying() ? player.current.currentTime() : 0;
        const row = { key: nextKey.current++, time: toClock(seconds), label: "", source: "teacher", detail: "" };
        setRows(byTime([...rows, row]));
        setCurrent(row.key);
    };
    const remove = (key) => setRows(rows.filter(r => r.key !== key));

    const chapters = () => {
        const bad = rows.find(r => timeOf(r) === null);
        if (bad) throw new Error(`"${bad.time || "(empty)"}" is not a time. Please write it like 2:30.`);
        return byTime(rows).map(r => ({ start: timeOf(r), label: r.label.trim(), source: r.source, detail: r.detail }));
    };

    // action: "saved", "published" or "discarded"
    const send = async (doIt, action, done) => {
        setError(null);
        setSuccess(null);
        setBusy(true);
        try {
            const saved = await doIt();
            onChange(saved, action);
            if (done) setSuccess(done);
        } catch (err) {
            setError(err.message);
        }
        setBusy(false);
    };
    const saveDraft = () => send(() => apiFetch(`/api/tcc/studio/videos/${video.id}/chapters-draft`,
        { method: "PUT", body: { chapters: chapters() } }), "saved", "The draft is saved. Members cannot see it yet.");
    const publish = () => {
        const unnamed = rows.filter(r => !r.label.trim()).length;
        if (unnamed) {
            setError(unnamed === 1 ? "One chapter has no name yet. Give it a name or delete it."
                : `${unnamed} chapters have no name yet. Give them a name or delete them.`);
            return;
        }
        send(() => apiFetch(`/api/tcc/studio/videos/${video.id}/chapters-draft/publish`,
            { method: "POST", body: { chapters: chapters() } }), "published");
    };
    const discard = () => {
        if (!window.confirm("Throw away these draft chapters? The chapters members see now will not change.")) return;
        send(() => apiFetch(`/api/tcc/studio/videos/${video.id}/chapters-draft`, { method: "DELETE" }), "discarded");
    };

    return (
        // Enter in a box should not save the whole video form
        <section className="tcc-field tcc-chapter-review" aria-labelledby="chapter-review-title"
            onKeyDown={(e) => { if (e.key === "Enter" && e.target.tagName === "INPUT") e.preventDefault(); }}>
            <h3 id="chapter-review-title">Review chapters <span className="tcc-badge tcc-badge-soon">Draft: members cannot see these yet</span></h3>
            <p className="tcc-field-hint">
                These chapters were made automatically from the title cards and the narration. Press a time to jump the
                video there and check it. Change the times and names as needed, then press <strong>Publish chapters</strong>.
                {(video.chapters || []).length > 0 && " Publishing replaces the chapters members see now."}
            </p>
            {draft.notes && <p className="tcc-field-hint">{draft.notes}</p>}

            {video.status === "ready" ? (
                <div className="tcc-chapter-review-player"><ProtectedPlayer ref={player} video={video} showChapters={false} /></div>
            ) : (
                <p className="tcc-field-hint">The video can be watched here once it is ready.</p>
            )}

            <ol className="tcc-chapter-review-list">
                {rows.map((r, i) => (
                    <li key={r.key} className={`tcc-chapter-review-row${current === r.key ? " current" : ""}${r.label.trim() ? "" : " needs-name"}`}>
                        <button type="button" className="tcc-chapter-jump" onClick={() => jump(r)} disabled={video.status !== "ready"}
                            aria-label={`Play from ${r.time}`}>
                            ▶ {r.time || "?"}
                        </button>
                        <div className="tcc-chapter-review-fields">
                            <div className="tcc-chapter-row">
                                <input className="tcc-input tcc-time-input" aria-label={`Chapter ${i + 1} time`} placeholder="0:00"
                                    value={r.time} onChange={(e) => update(r.key, "time", e.target.value)}
                                    onBlur={() => setRows(byTime(rows))} />
                                <input className="tcc-input" aria-label={`Chapter ${i + 1} name`} placeholder="Name this chapter"
                                    value={r.label} onChange={(e) => update(r.key, "label", e.target.value)} />
                            </div>
                            <p className="tcc-chapter-source">
                                <strong>{SOURCES[r.source] || SOURCES.teacher}</strong>{r.detail ? `: ${r.detail}` : ""}
                            </p>
                        </div>
                        <div className="tcc-chapter-review-buttons">
                            <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => setToNow(r.key)}
                                disabled={video.status !== "ready"} title="Use the time the video is at now">Use video time</button>
                            <button type="button" className="tcc-btn tcc-btn-outline tcc-btn-danger" onClick={() => remove(r.key)}>Delete</button>
                        </div>
                    </li>
                ))}
            </ol>
            <button type="button" className="tcc-btn tcc-btn-outline" onClick={add}>Add a chapter here</button>

            <FormMessage error={error} success={success} />
            <div className="tcc-button-row tcc-left">
                <button type="button" className="custom-btn1 tcc-btn" onClick={publish} disabled={busy || rows.length === 0}>Publish chapters</button>
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={saveDraft} disabled={busy}>Save draft</button>
                <button type="button" className="tcc-btn tcc-btn-outline tcc-btn-danger" onClick={discard} disabled={busy}>Throw away draft</button>
            </div>
        </section>
    );
};

export default StudioChapterReview;
