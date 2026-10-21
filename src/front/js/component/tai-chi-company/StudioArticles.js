import React, { useRef, useState, useEffect } from "react";
import { useTcc } from "./TccContext";
import { apiFetch } from "./api";
import FormField, { FormMessage } from "./FormField";
import { uploadPhoto } from "./photos";
import { useTextSize } from "./TextSize";
import { StatusBadge } from "./StudioVideos";
import { toLocalInput, fromLocalInput } from "./StudioVideoForm";
import RichEditor from "./RichEditor";
import ArticleView from "./ArticleView";

// Tap (or click) the part of the cover photo that must always stay visible; the cover is cropped around it
const CoverPosition = ({ url, position, onChange }) => {
    const [x, y] = (position || "50% 50%").split(" ").map(v => parseInt(v, 10));
    const pick = (e) => {
        const box = e.currentTarget.getBoundingClientRect();
        const px = Math.round(Math.min(100, Math.max(0, ((e.clientX - box.left) / box.width) * 100)));
        const py = Math.round(Math.min(100, Math.max(0, ((e.clientY - box.top) / box.height) * 100)));
        onChange(`${px}% ${py}%`);
    };
    const nudge = (dx, dy) => onChange(`${Math.min(100, Math.max(0, x + dx))}% ${Math.min(100, Math.max(0, y + dy))}%`);
    return (
        <div className="tcc-cover-position">
            <p className="tcc-field-hint">Tap the most important part of the photo. The cover is trimmed around it on every screen.</p>
            <div className="tcc-cover-frame" onClick={pick} role="presentation">
                <img src={url} alt="" style={{ objectPosition: position || "50% 50%" }} />
                <span className="tcc-cover-dot" style={{ left: `${x}%`, top: `${y}%` }} aria-hidden="true" />
            </div>
            <div className="tcc-button-row tcc-left" role="group" aria-label="Move the cover focus">
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => nudge(0, -10)}>Show more of the top</button>
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => nudge(0, 10)}>Show more of the bottom</button>
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => onChange("50% 50%")}>Back to the middle</button>
            </div>
        </div>
    );
};

const ArticleForm = ({ article, onDone, onCancel }) => {
    const { settings, user } = useTcc();
    const size = useTextSize();
    const [form, setForm] = useState(() => ({
        title: article ? article.title : "",
        author: article ? article.author : (user.name || ""),
        category: article ? article.category || "" : "",
        summary: article ? article.summary : "",
        is_free: article ? !!article.is_free : false,
        cover_image_path: article ? article.cover_image_path : null,
        cover_image_url: article ? article.cover_image_url : null,
        cover_position: article ? article.cover_position : "50% 50%",
        publish_at: toLocalInput(article ? article.publish_at : null)
    }));
    const [error, setError] = useState(null);
    const [busy, setBusy] = useState(false);
    const [coverBusy, setCoverBusy] = useState(false);
    const [preview, setPreview] = useState(null);
    const editor = useRef(null);
    const set = (field) => (e) => setForm({ ...form, [field]: e.target.type === "checkbox" ? e.target.checked : e.target.value });
    const body = (action) => ({ ...form, action, content: editor.current.getHTML(), publish_at: fromLocalInput(form.publish_at) });

    useEffect(() => { if (preview) window.scrollTo(0, 0); }, [!!preview]);

    const save = async (action) => {
        setError(null);
        if (editor.current.isBusy()) {
            setError("Please wait until the photos or the video have finished uploading, then save again.");
            return;
        }
        setBusy(true);
        try {
            const saved = article
                ? await apiFetch(`/api/tcc/studio/articles/${article.id}`, { method: "PUT", body: body(action) })
                : await apiFetch("/api/tcc/studio/articles", { method: "POST", body: body(action) });
            onDone(saved.status === "Draft" ? "Saved as a draft. Members cannot see it yet."
                : saved.status === "Scheduled" ? "Saved. It will appear on the date you chose."
                    : saved.is_free ? "Published. Anyone can read it now." : "Published. Members can read it now.");
            return; // the form has closed
        } catch (e) {
            setError(e.message);
        }
        setBusy(false);
    };

    const showPreview = async () => {
        setError(null);
        try {
            setPreview(await apiFetch("/api/tcc/studio/articles/preview", { method: "POST", body: { ...body("draft"), id: article && article.id } }));
        } catch (e) {
            setError(e.message);
        }
    };

    const addCover = async (e) => {
        const file = e.target.files && e.target.files[0];
        e.target.value = "";
        if (!file) return;
        setError(null);
        setCoverBusy(true);
        try {
            const { path, url } = await uploadPhoto(file, { cover: true });
            setForm(f => ({ ...f, cover_image_path: path, cover_image_url: url, cover_position: "50% 50%" }));
        } catch (err) {
            setError(err.message);
        }
        setCoverBusy(false);
    };

    const future = form.publish_at && new Date(form.publish_at) > new Date();
    return (
        <div className="tcc-studio-panel tcc-form-wide">
            <div hidden={!preview}>
                <div className="tcc-notice tcc-preview-banner">
                    <p><strong>Preview.</strong> This is exactly how {form.is_free ? "everyone" : "members"} will see the article. Nothing is saved yet.</p>
                    <button type="button" className="custom-btn1 tcc-btn" onClick={() => setPreview(null)}>Back to editing</button>
                </div>
                {preview && (
                    <div className="tcc-preview-page">
                        <ArticleView article={preview} size={size} schoolName={settings.school_name || settings.app_name} />
                    </div>
                )}
                <button type="button" className="custom-btn1 tcc-btn" onClick={() => setPreview(null)}>Back to editing</button>
            </div>

            <div hidden={!!preview}>
                <h2>{article ? `Edit "${article.title}"` : "Write a new article"}</h2>
                <FormField id="a-title" label="Title" value={form.title} onChange={set("title")} />
                <FormField id="a-author" label="Author" value={form.author} onChange={set("author")} />
                <div className="tcc-field">
                    <label htmlFor="a-category">Category</label>
                    <select id="a-category" className="tcc-input" value={form.category} onChange={set("category")}>
                        <option value="">Choose…</option>
                        {(settings.article_categories || []).map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                </div>
                <div className="tcc-field">
                    <label htmlFor="a-summary">Summary (two or three sentences; everyone can see this)</label>
                    <textarea id="a-summary" className="tcc-input tcc-textarea" rows={3} value={form.summary} onChange={set("summary")} />
                </div>
                <label className="tcc-checkbox">
                    <input type="checkbox" checked={form.is_free} onChange={set("is_free")} />
                    Free for everyone (anyone can read the whole article, without logging in)
                </label>
                <div className="tcc-field">
                    <span className="tcc-label">Cover photo (optional)</span>
                    {form.cover_image_url && (
                        <CoverPosition url={form.cover_image_url} position={form.cover_position}
                            onChange={(cover_position) => setForm(f => ({ ...f, cover_position }))} />
                    )}
                    <div className="tcc-button-row tcc-left">
                        <label className="tcc-btn tcc-btn-outline tcc-file-label">
                            {coverBusy ? "Uploading the cover…" : form.cover_image_path ? "Change the cover photo" : "Add a cover photo"}
                            <input type="file" accept="image/*" hidden onChange={addCover} disabled={coverBusy} />
                        </label>
                        {form.cover_image_path && (
                            <button type="button" className="tcc-btn tcc-btn-outline"
                                onClick={() => setForm({ ...form, cover_image_path: null, cover_image_url: null })}>Remove the cover</button>
                        )}
                    </div>
                </div>
                <div className="tcc-field">
                    <span className="tcc-label" id="a-content-label">The article</span>
                    <p className="tcc-field-hint">Type, or paste from Word or Google Docs. Pasted plain text? Press Auto-format to make the headings.</p>
                    <RichEditor ref={editor} initialHtml={article ? article.content : ""} kind="article" labelledBy="a-content-label" />
                </div>
                <FormField id="a-publish" label="Publish date" type="datetime-local" value={form.publish_at} onChange={set("publish_at")}
                    hint="Leave as it is to publish straight away, or pick a later date." />
                <FormMessage error={error} />
                <div className="tcc-button-row tcc-left">
                    <button type="button" className="custom-btn1 tcc-btn tcc-btn-big" disabled={busy} onClick={() => save("publish")}>
                        {future ? "Schedule" : "Publish"}
                    </button>
                    <button type="button" className="tcc-btn tcc-btn-outline" disabled={busy} onClick={() => save("draft")}>Save draft</button>
                    <button type="button" className="tcc-btn tcc-btn-outline" disabled={busy} onClick={showPreview}>Preview</button>
                    <button type="button" className="tcc-btn tcc-btn-outline" disabled={busy} onClick={onCancel}>Cancel</button>
                </div>
            </div>
        </div>
    );
};

const StudioArticles = () => {
    const [articles, setArticles] = useState(null);
    const [editing, setEditing] = useState(null); // null | "new" | article
    const [message, setMessage] = useState(null);
    const [error, setError] = useState(null);
    const [confirmId, setConfirmId] = useState(null);

    const load = () => apiFetch("/api/tcc/studio/articles").then(setArticles).catch(e => setError(e.message));
    useEffect(() => { load(); }, []);

    if (editing) {
        return (
            <ArticleForm article={editing === "new" ? null : editing} onCancel={() => setEditing(null)}
                onDone={(msg) => { setEditing(null); setMessage(msg); load(); window.scrollTo(0, 0); }} />
        );
    }

    const remove = async (a) => {
        try {
            setMessage((await apiFetch(`/api/tcc/studio/articles/${a.id}`, { method: "DELETE" })).msg);
            setConfirmId(null);
            load();
        } catch (e) {
            setError(e.message);
        }
    };

    return (
        <section>
            <FormMessage error={error} success={message} />
            <button type="button" className="custom-btn1 tcc-btn tcc-btn-big" onClick={() => setEditing("new")}>Write a new article</button>
            <h2 className="tcc-section">Member articles</h2>
            {!articles && !error && <p>Loading…</p>}
            {articles && articles.length === 0 && <p className="tcc-notice">No member articles yet.</p>}
            <ul className="tcc-studio-list">
                {(articles || []).map(a => (
                    <li key={a.id} className="tcc-studio-item">
                        <h3>{a.title}</h3>
                        <p className="tcc-badges">
                            <StatusBadge status={a.status} />
                            {a.category && <span className="tcc-badge tcc-badge-soon">{a.category}</span>}
                            {a.is_free && <span className="tcc-badge tcc-badge-free">Free for everyone</span>}
                        </p>
                        <p>{a.author} · {a.reading_minutes} min read · read {a.read_count} times</p>
                        <div className="tcc-button-row tcc-left">
                            <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => setEditing(a)}>Edit</button>
                            {confirmId !== a.id
                                ? <button type="button" className="tcc-btn tcc-btn-outline tcc-btn-danger" onClick={() => setConfirmId(a.id)}>Delete</button>
                                : (
                                    <div className="tcc-notice tcc-confirm">
                                        <p>Delete "{a.title}" for good? This cannot be undone.</p>
                                        <div className="tcc-button-row tcc-left">
                                            <button type="button" className="custom-btn1 tcc-btn" onClick={() => remove(a)}>Yes, delete it</button>
                                            <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => setConfirmId(null)}>No, keep it</button>
                                        </div>
                                    </div>
                                )}
                        </div>
                    </li>
                ))}
            </ul>
        </section>
    );
};

export default StudioArticles;
