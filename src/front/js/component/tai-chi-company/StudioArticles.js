import React, { useEffect, useRef, useState } from "react";
import { useTcc } from "./TccContext";
import { apiFetch } from "./api";
import FormField, { FormMessage } from "./FormField";
import { uploadPicture } from "./uploader";
import { RichText } from "./TextSize";
import { StatusBadge } from "./StudioVideos";
import { toLocalInput, fromLocalInput } from "./StudioVideoForm";

const ArticleForm = ({ article, onDone, onCancel }) => {
    const { settings, user } = useTcc();
    const [form, setForm] = useState(() => ({
        title: article ? article.title : "",
        author: article ? article.author : (user.name || ""),
        category: article ? article.category || "" : "",
        summary: article ? article.summary : "",
        content: article ? article.content : "",
        cover_image_path: article ? article.cover_image_path : null,
        cover_image_url: article ? article.cover_image_url : null,
        publish_at: toLocalInput(article ? article.publish_at : null)
    }));
    const [error, setError] = useState(null);
    const [busy, setBusy] = useState(false);
    const [preview, setPreview] = useState(false);
    const textRef = useRef(null);
    const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

    const save = async (action) => {
        setError(null);
        setBusy(true);
        try {
            const body = { ...form, action, publish_at: fromLocalInput(form.publish_at) };
            const saved = article
                ? await apiFetch(`/api/tcc/studio/articles/${article.id}`, { method: "PUT", body })
                : await apiFetch("/api/tcc/studio/articles", { method: "POST", body });
            onDone(saved.status === "Draft" ? "Saved as a draft. Members cannot see it yet."
                : saved.status === "Scheduled" ? "Saved. It will appear for members on the date you chose."
                    : "Published. Members can read it now.");
        } catch (e) {
            setError(e.message);
        }
        setBusy(false);
    };

    const addCover = async (e) => {
        const file = e.target.files && e.target.files[0];
        e.target.value = "";
        if (!file) return;
        setError(null);
        try {
            const { path, url } = await uploadPicture(file);
            setForm(f => ({ ...f, cover_image_path: path, cover_image_url: url }));
        } catch (err) {
            setError(err.message);
        }
    };

    // Inserts the picture as its own paragraph where the cursor is in the text
    const addPicture = async (e) => {
        const file = e.target.files && e.target.files[0];
        e.target.value = "";
        if (!file) return;
        setError(null);
        try {
            const { url } = await uploadPicture(file);
            const caption = (window.prompt("A few words about the picture (optional):") || "").replace(/[[\]]/g, "");
            const at = textRef.current ? textRef.current.selectionStart : form.content.length;
            const before = form.content.slice(0, at).replace(/\s*$/, "");
            const after = form.content.slice(at).replace(/^\s*/, "");
            setForm(f => ({ ...f, content: `${before}${before ? "\n\n" : ""}![${caption}](${url})${after ? "\n\n" : ""}${after}` }));
        } catch (err) {
            setError(err.message);
        }
    };

    const future = form.publish_at && new Date(form.publish_at) > new Date();
    return (
        <div className="tcc-studio-panel tcc-form-wide">
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
            <div className="tcc-field">
                <span className="tcc-label">Cover picture</span>
                {form.cover_image_url && <img src={form.cover_image_url} alt="" className="tcc-cover-preview" />}
                <div className="tcc-button-row tcc-left">
                    <label className="tcc-btn tcc-btn-outline tcc-file-label">
                        {form.cover_image_path ? "Change the cover picture" : "Add a cover picture"}
                        <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" hidden onChange={addCover} />
                    </label>
                    {form.cover_image_path && (
                        <button type="button" className="tcc-btn tcc-btn-outline"
                            onClick={() => setForm({ ...form, cover_image_path: null, cover_image_url: null })}>Remove the cover</button>
                    )}
                </div>
            </div>
            <div className="tcc-field">
                <label htmlFor="a-content">The article</label>
                <p className="tcc-field-hint">Type or paste the article. Leave an empty line between paragraphs.</p>
                <div className="tcc-button-row tcc-left">
                    <label className="tcc-btn tcc-btn-outline tcc-file-label">
                        Add a picture where the cursor is
                        <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" hidden onChange={addPicture} />
                    </label>
                    <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => setPreview(!preview)}>
                        {preview ? "Back to writing" : "Preview"}
                    </button>
                </div>
                {preview
                    ? <div className="tcc-article-body tcc-preview"><RichText text={form.content} /></div>
                    : <textarea id="a-content" ref={textRef} className="tcc-input tcc-textarea tcc-article-editor" rows={18}
                        value={form.content} onChange={set("content")} />}
            </div>
            <FormField id="a-publish" label="Publish date" type="datetime-local" value={form.publish_at} onChange={set("publish_at")}
                hint="Leave as it is to publish straight away, or pick a later date." />
            <FormMessage error={error} />
            <div className="tcc-button-row tcc-left">
                <button type="button" className="custom-btn1 tcc-btn tcc-btn-big" disabled={busy} onClick={() => save("publish")}>
                    {future ? "Schedule" : "Publish"}
                </button>
                <button type="button" className="tcc-btn tcc-btn-outline" disabled={busy} onClick={() => save("draft")}>Save draft</button>
                <button type="button" className="tcc-btn tcc-btn-outline" disabled={busy} onClick={onCancel}>Cancel</button>
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
