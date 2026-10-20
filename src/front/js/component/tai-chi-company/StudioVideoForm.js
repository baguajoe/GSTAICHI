import React, { useEffect, useRef, useState } from "react";
import { useTcc } from "./TccContext";
import { apiFetch } from "./api";
import FormField, { FormMessage } from "./FormField";
import { uploadVideoFile, uploadPicture, formatBytes, MAX_BYTES } from "./uploader";

const CATEGORY_SUGGESTIONS = ["Fundamentals", "Forms", "Weapons", "Push Hands", "Qigong", "Standing Exercises"];

// Server dates are UTC without a "Z"; the form shows local time.
export const toLocalInput = (iso) => {
    const d = iso ? new Date(iso.endsWith("Z") ? iso : `${iso}Z`) : new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
};
export const fromLocalInput = (value) => (value ? new Date(value).toISOString() : null);

const toSeconds = (text) => {
    const parts = String(text).trim().split(":").map(Number);
    if (parts.some(isNaN)) return null;
    return parts.reduce((total, n) => total * 60 + n, 0);
};
const toClock = (seconds) => {
    const s = Math.max(0, Math.floor(seconds));
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = String(s % 60).padStart(2, "0");
    return h ? `${h}:${String(m).padStart(2, "0")}:${sec}` : `${m}:${sec}`;
};

const ProgressBar = ({ progress }) => {
    const percent = progress.total ? Math.floor((progress.sent / progress.total) * 100) : 0;
    return (
        <div className="tcc-progress-wrap" role="status" aria-live="polite">
            <p className="tcc-progress-label">{progress.status} <strong>{percent}%</strong></p>
            <div className="tcc-progress" aria-hidden="true"><div className="tcc-progress-bar" style={{ width: `${percent}%` }} /></div>
            <p>{formatBytes(progress.sent)} of {formatBytes(progress.total)}. Please keep this page open until it says Done.</p>
        </div>
    );
};

// mode: "new" (details + file), "edit" (details only) or "file" (upload a file for an existing video)
const StudioVideoForm = ({ mode, video, defaults = {}, questionId, onDone, onCancel }) => {
    const { settings } = useTcc();
    const editing = mode !== "new";
    const [form, setForm] = useState(() => ({
        title: video ? video.title : defaults.title || "",
        short_description: video ? video.short_description : "",
        long_description: video ? video.long_description : "",
        section: video ? video.section : defaults.section || "",
        category: video ? video.category || "" : defaults.category || "",
        publish_at: toLocalInput(video ? video.publish_at : null),
        is_free_sample: video ? video.is_free_sample : false,
        chapters: (video ? video.chapters : []).map(c => ({ time: toClock(c.start), label: c.label }))
    }));
    const [file, setFile] = useState(null);
    const [error, setError] = useState(null);
    const [busy, setBusy] = useState(false);
    const [progress, setProgress] = useState(null);
    const [thumbnail, setThumbnail] = useState(video ? video.thumbnail_path : null);
    const [customThumb, setCustomThumb] = useState(video ? video.custom_thumbnail_path : null);
    const control = useRef({});
    const recordInput = useRef(null);
    const chooseInput = useRef(null);

    // Warn before leaving the page while a file is uploading
    useEffect(() => {
        if (!progress) return undefined;
        const warn = (e) => {
            e.preventDefault();
            e.returnValue = "";
        };
        window.addEventListener("beforeunload", warn);
        return () => window.removeEventListener("beforeunload", warn);
    }, [progress]);

    const set = (field) => (e) => setForm({ ...form, [field]: e.target.type === "checkbox" ? e.target.checked : e.target.value });
    const isCorner = form.section === settings.corner_section;
    const pickFile = (e) => {
        const chosen = e.target.files && e.target.files[0];
        e.target.value = "";
        if (!chosen) return;
        if (chosen.size > MAX_BYTES) {
            setError("This file is bigger than 10 GB. Please make it shorter or smaller and try again.");
            return;
        }
        setError(null);
        setFile(chosen);
    };
    const setChapter = (i, field, value) => {
        const chapters = form.chapters.map((c, j) => (j === i ? { ...c, [field]: value } : c));
        setForm({ ...form, chapters });
    };

    const details = () => ({
        title: form.title,
        short_description: form.short_description,
        long_description: form.long_description,
        section: form.section,
        category: form.category,
        publish_at: fromLocalInput(form.publish_at),
        is_free_sample: form.is_free_sample,
        chapters: form.chapters.map(c => ({ start: toSeconds(c.time), label: c.label })).filter(c => c.start !== null && c.label.trim())
    });

    const submit = async (e) => {
        e.preventDefault();
        setError(null);
        if (mode !== "file" && (!form.title.trim() || !form.section)) {
            setError("Please fill in the title and choose a section.");
            return;
        }
        if (mode !== "edit" && !file) {
            setError("Please record or choose the video file.");
            return;
        }
        setBusy(true);
        try {
            let saved = video;
            if (mode === "new") {
                saved = await apiFetch("/api/tcc/studio/videos", { method: "POST", body: { ...details(), question_id: questionId } });
            } else if (mode === "edit") {
                const body = details();
                if (customThumb !== video.custom_thumbnail_path) body.custom_thumbnail_path = customThumb;
                else if (thumbnail !== video.thumbnail_path && !customThumb) body.thumbnail_path = thumbnail;
                saved = await apiFetch(`/api/tcc/studio/videos/${video.id}`, { method: "PUT", body });
            }
            if (mode !== "edit") {
                setProgress({ sent: 0, total: file.size, status: "Starting…" });
                saved = await uploadVideoFile({ videoId: saved.id, file, onProgress: setProgress, control: control.current });
                setProgress(null);
            }
            onDone(saved, mode === "edit"
                ? "Your changes are saved."
                : "Done! The video is uploaded and is now being prepared. This usually takes 10 to 30 minutes. You will get an email when it is ready.");
        } catch (err) {
            setProgress(null);
            setError(err.message === "cancelled" ? "The upload was stopped. Choose the same file again to continue where it stopped."
                : err.message === "network" || err.message === "timeout"
                    ? "The internet connection was lost. Choose the same file again to continue where it stopped."
                    : err.message);
        }
        setBusy(false);
    };

    const useOwnPicture = async (e) => {
        const picture = e.target.files && e.target.files[0];
        e.target.value = "";
        if (!picture) return;
        setError(null);
        try {
            const { path } = await uploadPicture(picture, `/api/tcc/studio/videos/${video.id}/thumbnail-upload`);
            setCustomThumb(path);
        } catch (err) {
            setError(err.message);
        }
    };

    if (progress) {
        return (
            <div className="tcc-studio-panel">
                <h2>Uploading "{form.title || (video && video.title)}"</h2>
                <ProgressBar progress={progress} />
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => control.current.cancel && control.current.cancel()}>
                    Stop the upload
                </button>
            </div>
        );
    }

    return (
        <form className="tcc-studio-panel tcc-form-wide" onSubmit={submit} noValidate>
            <h2>{mode === "new" ? "Add a new video" : mode === "edit" ? `Edit "${video.title}"` : `Upload the video file for "${video.title}"`}</h2>

            {mode !== "edit" && (
                <div className="tcc-field">
                    <span className="tcc-label">The video file</span>
                    <div className="tcc-button-row tcc-left">
                        <button type="button" className="custom-btn1 tcc-btn" onClick={() => recordInput.current.click()}>Record a video now</button>
                        <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => chooseInput.current.click()}>Choose a video</button>
                    </div>
                    <input ref={recordInput} type="file" accept="video/*" capture="environment" hidden onChange={pickFile} aria-label="Record a video" />
                    <input ref={chooseInput} type="file" accept="video/*" hidden onChange={pickFile} aria-label="Choose a video file" />
                    {file && <p className="tcc-success">Chosen: {file.name} ({formatBytes(file.size)})</p>}
                    {mode === "file" && video.studio_status === "Uploading" && (
                        <p className="tcc-field-hint">If an earlier upload of this video stopped, choose the same file and it will continue where it stopped.</p>
                    )}
                </div>
            )}

            {mode !== "file" && (
                <>
                    <FormField id="v-title" label="Title" value={form.title} onChange={set("title")} required />
                    <div className="tcc-field">
                        <label htmlFor="v-section">Section</label>
                        <select id="v-section" className="tcc-input" value={form.section} onChange={set("section")}>
                            <option value="">Choose a section…</option>
                            {(settings.video_sections || []).map(s => <option key={s.key} value={s.key}>{s.label}</option>)}
                        </select>
                    </div>
                    <div className="tcc-field">
                        <label htmlFor="v-category">{isCorner ? "Type of video" : "Category"}</label>
                        {isCorner ? (
                            <select id="v-category" className="tcc-input" value={form.category} onChange={set("category")}>
                                <option value="">Choose…</option>
                                {(settings.corner_categories || []).map(c => <option key={c} value={c}>{c}</option>)}
                            </select>
                        ) : (
                            <>
                                <input id="v-category" className="tcc-input" list="v-category-list" value={form.category} onChange={set("category")} />
                                <datalist id="v-category-list">{CATEGORY_SUGGESTIONS.map(c => <option key={c} value={c} />)}</datalist>
                            </>
                        )}
                    </div>
                    <div className="tcc-field">
                        <label htmlFor="v-short">Short description (shown on the video card)</label>
                        <textarea id="v-short" className="tcc-input tcc-textarea" rows={3} value={form.short_description} onChange={set("short_description")} />
                    </div>
                    <div className="tcc-field">
                        <label htmlFor="v-long">About this form (longer text; leave a blank line between paragraphs)</label>
                        <textarea id="v-long" className="tcc-input tcc-textarea" rows={8} value={form.long_description} onChange={set("long_description")} />
                    </div>
                    <FormField id="v-publish" label="Show to members from" type="datetime-local" value={form.publish_at}
                        onChange={set("publish_at")} hint="Leave as it is to show it as soon as it is ready." />
                    <label className="tcc-checkbox">
                        <input type="checkbox" checked={form.is_free_sample} onChange={set("is_free_sample")} />
                        Free sample (anyone with a free account can watch it)
                    </label>

                    <fieldset className="tcc-field tcc-chapters-edit">
                        <legend>Chapters (optional)</legend>
                        <p className="tcc-field-hint">For example 0:00 Opening, 2:30 Single Whip. Members can tap a chapter to jump to it.</p>
                        {form.chapters.map((c, i) => (
                            <div key={i} className="tcc-chapter-row">
                                <input className="tcc-input tcc-time-input" aria-label={`Chapter ${i + 1} time`} placeholder="0:00"
                                    value={c.time} onChange={(e) => setChapter(i, "time", e.target.value)} />
                                <input className="tcc-input" aria-label={`Chapter ${i + 1} name`} placeholder="Name of this part"
                                    value={c.label} onChange={(e) => setChapter(i, "label", e.target.value)} />
                                <button type="button" className="tcc-btn tcc-btn-outline"
                                    onClick={() => setForm({ ...form, chapters: form.chapters.filter((_, j) => j !== i) })}>Remove</button>
                            </div>
                        ))}
                        <button type="button" className="tcc-btn tcc-btn-outline"
                            onClick={() => setForm({ ...form, chapters: [...form.chapters, { time: "", label: "" }] })}>Add a chapter</button>
                    </fieldset>
                </>
            )}

            {mode === "edit" && video.thumbnail_options.length > 0 && (
                <fieldset className="tcc-field">
                    <legend>Picture on the video card</legend>
                    <div className="tcc-thumb-picker">
                        {video.thumbnail_options.map(o => (
                            <button type="button" key={o.path} aria-pressed={!customThumb && thumbnail === o.path}
                                className={`tcc-thumb-choice${!customThumb && thumbnail === o.path ? " active" : ""}`}
                                onClick={() => { setThumbnail(o.path); setCustomThumb(null); }}>
                                <img src={o.url} alt={`Picture from ${o.percent}% of the way through`} />
                                <span>{!customThumb && thumbnail === o.path ? "Chosen" : "Choose"}</span>
                            </button>
                        ))}
                    </div>
                    <label className="tcc-btn tcc-btn-outline tcc-file-label">
                        Use my own picture
                        <input type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={useOwnPicture} />
                    </label>
                    {customThumb && <p className="tcc-success">Your own picture will be used.</p>}
                </fieldset>
            )}

            <FormMessage error={error} />
            <div className="tcc-button-row tcc-left">
                <button type="submit" className="custom-btn1 tcc-btn tcc-btn-big" disabled={busy}>
                    {mode === "edit" ? "Save changes" : "Save and upload"}
                </button>
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={onCancel} disabled={busy}>Cancel</button>
            </div>
        </form>
    );
};

export default StudioVideoForm;
