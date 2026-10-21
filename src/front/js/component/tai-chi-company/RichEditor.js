import React, { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import Quill from "quill";
import "quill/dist/quill.core.css";
import { useTcc } from "./TccContext";
import { apiFetch } from "./api";
import { uploadPhoto } from "./photos";
import { uploadVideoFile, formatBytes, MAX_BYTES } from "./uploader";
import { autoFormatPlan } from "./autoFormat";
import Overlay from "./Overlay";

// Rich text editor for member articles and video "About This Form" descriptions (Quill), with big
// labelled buttons. The HTML it produces is cleaned again on the server (src/api/rich_text.py), which
// also explains the three special blocks: photo, photo gallery and video.

const Delta = Quill.import("delta");
const BlockEmbed = Quill.import("blots/block/embed");

export const PHOTO_SIZES = [
    ["full", "Full width"],
    ["medium", "Medium, centered"],
    ["small-left", "Small, photo on the left (text wraps on the right)"],
    ["small-right", "Small, photo on the right (text wraps on the left)"]
];

const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

const el = (tag, attrs = {}, text) => {
    const node = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => { if (v != null && v !== "") node.setAttribute(k, v); });
    if (text) node.textContent = text;
    return node;
};
const ownCaption = (node) => [...node.children].find(c => c.tagName === "FIGCAPTION");

class PhotoBlot extends BlockEmbed {
    static create(value) {
        const node = super.create();
        node.setAttribute("contenteditable", "false");
        node.setAttribute("data-size", PHOTO_SIZES.some(([k]) => k === value.size) ? value.size : "full");
        node.appendChild(el("img", { src: value.src, alt: value.alt || "" }));
        if (value.caption) node.appendChild(el("figcaption", {}, value.caption));
        return node;
    }

    static value(node) {
        const img = node.querySelector("img");
        if (!img) return null;
        const caption = ownCaption(node);
        return { src: img.getAttribute("src") || "", alt: img.getAttribute("alt") || "",
            caption: caption ? caption.textContent : "", size: node.getAttribute("data-size") || "full" };
    }

    html() {
        const v = PhotoBlot.value(this.domNode);
        return `<figure class="tcc-photo" data-size="${esc(v.size)}"><img src="${esc(v.src)}" alt="${esc(v.alt)}">`
            + `${v.caption ? `<figcaption>${esc(v.caption)}</figcaption>` : ""}</figure>`;
    }
}
PhotoBlot.blotName = "photo";
PhotoBlot.tagName = "FIGURE";
PhotoBlot.className = "tcc-photo";

class GalleryBlot extends BlockEmbed {
    static create(value) {
        const node = super.create();
        node.setAttribute("contenteditable", "false");
        const images = value.images || [];
        node.setAttribute("data-count", String(Math.min(images.length, 4)));
        images.forEach(image => node.appendChild(el("img", { src: image.src, alt: image.alt || "" })));
        if (value.caption) node.appendChild(el("figcaption", {}, value.caption));
        return node;
    }

    static value(node) {
        const images = [...node.querySelectorAll("img")].map(img => ({ src: img.getAttribute("src") || "", alt: img.getAttribute("alt") || "" }));
        if (!images.length) return null;
        const caption = ownCaption(node);
        return { images, caption: caption ? caption.textContent : "" };
    }

    html() {
        const v = GalleryBlot.value(this.domNode);
        return `<figure class="tcc-gallery">${v.images.map(i => `<img src="${esc(i.src)}" alt="${esc(i.alt)}">`).join("")}`
            + `${v.caption ? `<figcaption>${esc(v.caption)}</figcaption>` : ""}</figure>`;
    }
}
GalleryBlot.blotName = "gallery";
GalleryBlot.tagName = "FIGURE";
GalleryBlot.className = "tcc-gallery";

// In the editor a video shows as a card with its title and status; only the slug and caption are saved.
class VideoBlot extends BlockEmbed {
    static create(value) {
        const node = super.create();
        node.setAttribute("contenteditable", "false");
        node.setAttribute("data-video", value.slug);
        ["title", "status", "thumb"].forEach(k => { if (value[k]) node.setAttribute(`data-${k}`, value[k]); });
        const card = el("div", { class: "tcc-editor-video" });
        if (value.thumb) card.appendChild(el("img", { src: value.thumb, alt: "" }));
        const text = el("div");
        text.appendChild(el("strong", {}, `Video: ${value.title || value.slug}`));
        text.appendChild(el("span", {}, value.status || ""));
        card.appendChild(text);
        node.appendChild(card);
        if (value.caption) node.appendChild(el("figcaption", {}, value.caption));
        return node;
    }

    static value(node) {
        const slug = node.getAttribute("data-video");
        if (!slug) return null;
        const caption = ownCaption(node);
        return { slug, caption: caption ? caption.textContent : "", title: node.getAttribute("data-title") || "",
            status: node.getAttribute("data-status") || "", thumb: node.getAttribute("data-thumb") || "" };
    }

    html() {
        const v = VideoBlot.value(this.domNode);
        return `<figure class="tcc-video-block" data-video="${esc(v.slug)}">${v.caption ? `<figcaption>${esc(v.caption)}</figcaption>` : ""}</figure>`;
    }
}
VideoBlot.blotName = "video";
VideoBlot.tagName = "FIGURE";
VideoBlot.className = "tcc-video-block";

class DividerBlot extends BlockEmbed {}
DividerBlot.blotName = "divider";
DividerBlot.tagName = "HR";

Quill.register({ "formats/photo": PhotoBlot, "formats/gallery": GalleryBlot, "formats/video": VideoBlot, "formats/divider": DividerBlot }, true);

const TEXT_FORMATS = ["header", "bold", "italic", "link", "list", "blockquote", "divider", "photo"];
const FORMATS = { article: [...TEXT_FORMATS, "gallery", "video"], description: TEXT_FORMATS };
const BUSY_STATUSES = ["Uploading", "Processing"];

// Word and Google Docs headings: Heading 1 becomes our Heading, Heading 3-6 our Subheading
const fixPastedHeadings = (node, delta) => {
    delta.ops.forEach(op => {
        const level = op.attributes && op.attributes.header;
        if (level === 1) op.attributes.header = 2;
        else if (level > 3) op.attributes.header = 3;
    });
    return delta;
};

const ToolButton = ({ icon, label, active, onClick, disabled }) => (
    <button type="button" className={`tcc-tool${active ? " active" : ""}`} aria-pressed={active === undefined ? undefined : !!active}
        disabled={disabled} onMouseDown={(e) => e.preventDefault()} onClick={onClick}>
        <i className={`fas ${icon}`} aria-hidden="true"></i><span>{label}</span>
    </button>
);

const Dialog = ({ title, children, onClose }) => {
    const box = useRef(null);
    useEffect(() => {
        const first = box.current && box.current.querySelector("input, select, button");
        if (first) first.focus();
        const onKey = (e) => { if (e.key === "Escape") onClose(); };
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, []);
    return (
        <Overlay>
            <div className="tcc-dialog-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
                <div className="tcc-dialog" role="dialog" aria-modal="true" aria-label={title} ref={box}>
                    <h3>{title}</h3>
                    {children}
                </div>
            </div>
        </Overlay>
    );
};

const MoveButtons = ({ onMove, onDelete, deleteLabel }) => (
    <div className="tcc-button-row tcc-left">
        <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => onMove(-1)}>Move up</button>
        <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => onMove(1)}>Move down</button>
        <button type="button" className="tcc-btn tcc-btn-outline tcc-btn-danger" onClick={onDelete}>{deleteLabel}</button>
    </div>
);

const PhotoDialog = ({ value, onSave, onMove, onDelete, onClose }) => {
    const [photo, setPhoto] = useState(value);
    const set = (field) => (e) => setPhoto({ ...photo, [field]: e.target.value });
    return (
        <Dialog title="Photo" onClose={onClose}>
            <img src={photo.src} alt="" className="tcc-dialog-photo" />
            <div className="tcc-field">
                <label htmlFor="p-caption">Caption (shown under the photo, optional)</label>
                <input id="p-caption" className="tcc-input" value={photo.caption} onChange={set("caption")} />
            </div>
            <div className="tcc-field">
                <label htmlFor="p-alt">Short description for people who cannot see the photo</label>
                <input id="p-alt" className="tcc-input" value={photo.alt} onChange={set("alt")}
                    placeholder="For example: Vincent Chu in the Single Whip posture" />
                <p className="tcc-field-hint">Screen readers read this out loud for blind and partially sighted members.</p>
            </div>
            <fieldset className="tcc-field">
                <legend>Size</legend>
                {PHOTO_SIZES.map(([key, label]) => (
                    <label key={key} className="tcc-checkbox">
                        <input type="radio" name="p-size" checked={photo.size === key} onChange={() => setPhoto({ ...photo, size: key })} />
                        {label}
                    </label>
                ))}
            </fieldset>
            <div className="tcc-button-row tcc-left">
                <button type="button" className="custom-btn1 tcc-btn" onClick={() => onSave(photo)}>Save</button>
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={onClose}>Cancel</button>
            </div>
            <MoveButtons onMove={onMove} onDelete={onDelete} deleteLabel="Delete this photo" />
        </Dialog>
    );
};

const GalleryDialog = ({ value, onSave, onMove, onDelete, onClose, onAddPhotos }) => {
    const [gallery, setGallery] = useState(value);
    const [dragging, setDragging] = useState(null);
    const [adding, setAdding] = useState(null);
    const images = gallery.images;
    const setImages = (next) => setGallery({ ...gallery, images: next });
    const move = (from, to) => {
        if (to < 0 || to >= images.length) return;
        const next = [...images];
        next.splice(to, 0, next.splice(from, 1)[0]);
        setImages(next);
    };
    const add = async (e) => {
        const files = [...(e.target.files || [])];
        e.target.value = "";
        if (!files.length) return;
        try {
            const added = await onAddPhotos(files, setAdding);
            setGallery(g => ({ ...g, images: [...g.images, ...added] }));
        } catch (err) {
            setAdding(err.message);
            return;
        }
        setAdding(null);
    };
    return (
        <Dialog title="Photo gallery" onClose={onClose}>
            <p className="tcc-field-hint">Drag the photos, or use the arrows, to change the order.</p>
            <ol className="tcc-gallery-editor">
                {images.map((image, i) => (
                    <li key={`${image.src}-${i}`} draggable onDragStart={() => setDragging(i)} onDragEnd={() => setDragging(null)}
                        onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); if (dragging !== null) move(dragging, i); }}
                        className={dragging === i ? "dragging" : ""}>
                        <span className="tcc-drag-handle" aria-hidden="true"><i className="fas fa-grip-vertical"></i></span>
                        <img src={image.src} alt="" />
                        <div className="tcc-gallery-editor-fields">
                            <label htmlFor={`g-alt-${i}`}>Short description for screen readers</label>
                            <input id={`g-alt-${i}`} className="tcc-input" value={image.alt}
                                onChange={(e) => setImages(images.map((im, j) => (j === i ? { ...im, alt: e.target.value } : im)))} />
                            <div className="tcc-button-row tcc-left">
                                <button type="button" className="tcc-btn tcc-btn-outline" disabled={i === 0} onClick={() => move(i, i - 1)}
                                    aria-label={`Move photo ${i + 1} earlier`}>&uarr;</button>
                                <button type="button" className="tcc-btn tcc-btn-outline" disabled={i === images.length - 1}
                                    onClick={() => move(i, i + 1)} aria-label={`Move photo ${i + 1} later`}>&darr;</button>
                                <button type="button" className="tcc-btn tcc-btn-outline tcc-btn-danger"
                                    onClick={() => setImages(images.filter((_, j) => j !== i))}>Remove</button>
                            </div>
                        </div>
                    </li>
                ))}
            </ol>
            <label className="tcc-btn tcc-btn-outline tcc-file-label">
                <i className="fas fa-plus" aria-hidden="true"></i>&nbsp;Add more photos
                <input type="file" accept="image/*" multiple hidden onChange={add} />
            </label>
            {adding && <p role="status">{adding}</p>}
            <div className="tcc-field">
                <label htmlFor="g-caption">Caption for the gallery (optional)</label>
                <input id="g-caption" className="tcc-input" value={gallery.caption}
                    onChange={(e) => setGallery({ ...gallery, caption: e.target.value })} />
            </div>
            <div className="tcc-button-row tcc-left">
                <button type="button" className="custom-btn1 tcc-btn" disabled={!images.length} onClick={() => onSave(gallery)}>Save</button>
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={onClose}>Cancel</button>
            </div>
            <MoveButtons onMove={onMove} onDelete={onDelete} deleteLabel="Delete the whole gallery" />
        </Dialog>
    );
};

const VideoDialog = ({ value, info, onSave, onMove, onDelete, onClose, onLibraryChange }) => {
    const [caption, setCaption] = useState(value.caption);
    return (
        <Dialog title={`Video: ${value.title || value.slug}`} onClose={onClose}>
            <p>Status: <strong>{(info && info.studio_status) || value.status || "Unknown"}</strong></p>
            <div className="tcc-field">
                <label htmlFor="vd-caption">Caption (shown under the video, optional)</label>
                <input id="vd-caption" className="tcc-input" value={caption} onChange={(e) => setCaption(e.target.value)} />
            </div>
            {info && (
                <label className="tcc-checkbox">
                    <input type="checkbox" checked={info.show_in_library} onChange={(e) => onLibraryChange(info, e.target.checked)} />
                    Also show this video in the Video Library
                </label>
            )}
            <div className="tcc-button-row tcc-left">
                <button type="button" className="custom-btn1 tcc-btn" onClick={() => onSave({ ...value, caption })}>Save</button>
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={onClose}>Cancel</button>
            </div>
            <MoveButtons onMove={onMove} onDelete={onDelete} deleteLabel="Remove from the article" />
        </Dialog>
    );
};

const AddVideoDialog = ({ videos, onUpload, onPick, onClose }) => {
    const { settings } = useTcc();
    const [tab, setTab] = useState("upload");
    const [form, setForm] = useState({ title: "", section: "", show_in_library: false });
    const [file, setFile] = useState(null);
    const [search, setSearch] = useState("");
    const [error, setError] = useState(null);
    const found = (videos || []).filter(v => v.title.toLowerCase().includes(search.trim().toLowerCase()));
    const submit = () => {
        if (!form.title.trim() || !form.section) return setError("Please give the video a title and choose a section.");
        if (!file) return setError("Please choose the video file.");
        if (file.size > MAX_BYTES) return setError("This file is bigger than 10 GB. Please make it shorter or smaller and try again.");
        return onUpload(form, file);
    };
    return (
        <Dialog title="Add a video" onClose={onClose}>
            <div className="tcc-tabs" role="tablist" aria-label="How to add the video">
                <button type="button" role="tab" aria-selected={tab === "upload"} className={`tcc-tab${tab === "upload" ? " active" : ""}`}
                    onClick={() => setTab("upload")}>Upload a new video</button>
                <button type="button" role="tab" aria-selected={tab === "library"} className={`tcc-tab${tab === "library" ? " active" : ""}`}
                    onClick={() => setTab("library")}>Insert a library video</button>
            </div>
            {tab === "upload" ? (
                <>
                    <div className="tcc-field">
                        <label htmlFor="av-title">Title</label>
                        <input id="av-title" className="tcc-input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
                    </div>
                    <div className="tcc-field">
                        <label htmlFor="av-section">Section (decides which plans can watch it)</label>
                        <select id="av-section" className="tcc-input" value={form.section} onChange={(e) => setForm({ ...form, section: e.target.value })}>
                            <option value="">Choose a section…</option>
                            {(settings.video_sections || []).map(s => <option key={s.key} value={s.key}>{s.label}</option>)}
                        </select>
                    </div>
                    <label className="tcc-checkbox">
                        <input type="checkbox" checked={form.show_in_library} onChange={(e) => setForm({ ...form, show_in_library: e.target.checked })} />
                        Also show this video in the Video Library
                    </label>
                    <label className="tcc-btn tcc-btn-outline tcc-file-label">
                        <i className="fas fa-film" aria-hidden="true"></i>&nbsp;{file ? `Chosen: ${file.name} (${formatBytes(file.size)})` : "Choose the video file"}
                        <input type="file" accept="video/*" hidden onChange={(e) => { setFile(e.target.files && e.target.files[0]); e.target.value = ""; }} />
                    </label>
                    {error && <p className="tcc-error" role="alert">{error}</p>}
                    <div className="tcc-button-row tcc-left">
                        <button type="button" className="custom-btn1 tcc-btn" onClick={submit}>Upload and add to the article</button>
                        <button type="button" className="tcc-btn tcc-btn-outline" onClick={onClose}>Cancel</button>
                    </div>
                </>
            ) : (
                <>
                    <div className="tcc-field">
                        <label htmlFor="av-search">Find a video</label>
                        <input id="av-search" className="tcc-input" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Type part of the title" />
                    </div>
                    {!videos && <p>Loading…</p>}
                    <ul className="tcc-video-picker">
                        {found.map(v => (
                            <li key={v.id}>
                                {v.thumbnail_url ? <img src={v.thumbnail_url} alt="" /> : <span className="tcc-video-picker-thumb" aria-hidden="true" />}
                                <span><strong>{v.title}</strong><br />{v.studio_status}</span>
                                <button type="button" className="custom-btn1 tcc-btn" onClick={() => onPick(v)}>Add</button>
                            </li>
                        ))}
                    </ul>
                    {videos && !found.length && <p>No videos match.</p>}
                </>
            )}
        </Dialog>
    );
};

// kind: "article" (all buttons) or "description" (no gallery or video). The parent reads the result with
// ref.current.getHTML() and should check ref.current.isBusy() before saving.
const RichEditor = forwardRef(({ initialHtml, kind = "article", labelledBy }, ref) => {
    const holder = useRef(null);
    const quillRef = useRef(null);
    const photoInput = useRef(null);
    const galleryInput = useRef(null);
    const uploadControl = useRef({});
    const alive = useRef(true); // false once the editor is closed, so late answers are ignored
    const [formats, setFormats] = useState({});
    const [dialog, setDialog] = useState(null); // { type, index, value }
    const [busy, setBusy] = useState(null);
    const [error, setError] = useState(null);
    const [autoResult, setAutoResult] = useState(null);
    const [upload, setUpload] = useState(null);
    const [videos, setVideos] = useState(null);
    const [hasBusyVideos, setHasBusyVideos] = useState(false);
    const isArticle = kind === "article";

    useImperativeHandle(ref, () => ({
        getHTML: () => {
            const q = quillRef.current;
            return q && q.getLength() > 1 ? q.getSemanticHTML() : "";
        },
        isBusy: () => !!busy || !!upload
    }));

    const q = () => quillRef.current;

    const refreshVideos = async () => {
        if (!isArticle) return;
        let list;
        try {
            list = await apiFetch("/api/tcc/studio/videos");
        } catch (e) {
            return;
        }
        if (!alive.current) return;
        setVideos(list);
        const quill = q();
        if (!quill) return;
        const bySlug = Object.fromEntries(list.map(v => [v.slug, v]));
        let anyBusy = false;
        quill.root.querySelectorAll("figure.tcc-video-block").forEach(node => {
            const blot = Quill.find(node);
            const info = bySlug[node.getAttribute("data-video")];
            if (!blot || !info) return;
            const value = VideoBlot.value(node);
            const next = { ...value, title: info.title, status: info.studio_status, thumb: info.thumbnail_url || "" };
            if (BUSY_STATUSES.includes(next.status)) anyBusy = true;
            if (next.title !== value.title || next.status !== value.status || next.thumb !== value.thumb) {
                quill.updateContents(new Delta().retain(quill.getIndex(blot)).delete(1).insert({ video: next }), "silent");
            }
        });
        setHasBusyVideos(anyBusy);
    };

    useEffect(() => {
        const quill = new Quill(holder.current, {
            formats: FORMATS[kind] || FORMATS.article,
            modules: {
                toolbar: false,
                history: { delay: 800, maxStack: 200, userOnly: true },
                // Typing "1. " must not start a list: "1. Softness Controls Hardness" is a heading (see Auto-format)
                keyboard: { bindings: { "list autofill": null } }
            },
            placeholder: "Type or paste the text here…"
        });
        quill.clipboard.addMatcher(Node.ELEMENT_NODE, fixPastedHeadings);
        if (initialHtml) quill.setContents(quill.clipboard.convert({ html: initialHtml }), "silent");
        quill.history.clear();
        if (labelledBy) quill.root.setAttribute("aria-labelledby", labelledBy);
        quill.root.setAttribute("aria-multiline", "true");
        quill.root.setAttribute("role", "textbox");
        quill.on("editor-change", () => {
            const range = quill.getSelection();
            if (range) setFormats(quill.getFormat(range));
        });
        const onClick = (e) => {
            const node = e.target.closest("figure.tcc-photo, figure.tcc-gallery, figure.tcc-video-block");
            const blot = node && Quill.find(node);
            if (!blot) return;
            setDialog({ type: blot.statics.blotName, index: quill.getIndex(blot), value: blot.statics.value(node) });
        };
        quill.root.addEventListener("click", onClick);
        quillRef.current = quill;
        refreshVideos();
        return () => {
            alive.current = false;
            quill.root.removeEventListener("click", onClick);
        };
    }, []);

    // Keep video statuses up to date while something is uploading or being prepared
    useEffect(() => {
        if (!hasBusyVideos && !upload) return undefined;
        const timer = setInterval(refreshVideos, 20000);
        return () => clearInterval(timer);
    }, [hasBusyVideos, upload]);

    // Warn before leaving while a video is still uploading
    useEffect(() => {
        if (!upload) return undefined;
        const warn = (e) => { e.preventDefault(); e.returnValue = ""; };
        window.addEventListener("beforeunload", warn);
        return () => window.removeEventListener("beforeunload", warn);
    }, [upload]);

    const toggle = (name, value = true) => {
        const quill = q();
        const range = quill.getSelection(true);
        const current = quill.getFormat(range)[name];
        quill.format(name, current === value ? false : value, "user");
        setFormats(quill.getFormat(quill.getSelection(true)));
    };

    // Where a block (photo, video, divider) goes: on an empty line at the cursor, otherwise after its line
    const insertBlock = (type, value) => {
        const quill = q();
        const range = quill.getSelection(true) || { index: quill.getLength() - 1 };
        const [line, offset] = quill.getLine(range.index);
        const start = range.index - offset;
        const empty = line && !(line instanceof BlockEmbed) && line.length() <= 1;
        let at = !line ? quill.getLength() - 1 : empty ? start : start + line.length();
        if (at >= quill.getLength()) {
            quill.updateContents(new Delta().retain(quill.getLength() - 1).insert("\n").insert({ [type]: value }), "user");
            at = quill.getLength() - 2;
        } else {
            quill.updateContents(new Delta().retain(at).insert({ [type]: value }), "user");
        }
        quill.setSelection(at + 1, 0, "silent");
        return at;
    };

    const replaceAt = (index, type, value) => {
        q().updateContents(new Delta().retain(index).delete(1).insert({ [type]: value }), "user");
        setDialog(null);
    };

    const removeAt = (index) => {
        q().deleteText(index, 1, "user");
        setDialog(null);
    };

    const moveAt = (index, type, direction) => {
        const quill = q();
        const node = quill.getLine(index)[0];
        const value = node.statics.value(node.domNode);
        let target;
        if (direction < 0) {
            if (index === 0) return;
            const [prev] = quill.getLine(index - 1);
            target = quill.getIndex(prev);
            quill.updateContents(new Delta().retain(target).insert({ [type]: value }).retain(index - target).delete(1), "user");
        } else {
            const [next] = quill.getLine(index + 1);
            if (!next || index + 1 >= quill.getLength() - 1) return;
            const after = quill.getIndex(next) + next.length();
            target = after - 1;
            quill.updateContents(new Delta().retain(index).delete(1).retain(after - index - 1).insert({ [type]: value }), "user");
        }
        setDialog(d => (d ? { ...d, index: target } : d));
    };

    const uploadPhotos = async (files, report) => {
        const done = [];
        for (let i = 0; i < files.length; i++) {
            report(files.length > 1 ? `Preparing and uploading photo ${i + 1} of ${files.length}…` : "Preparing and uploading the photo…");
            const { url } = await uploadPhoto(files[i]);
            done.push({ src: url, alt: "" });
        }
        return done;
    };

    const addPhotos = async (e, asGallery) => {
        const files = [...(e.target.files || [])];
        e.target.value = "";
        if (!files.length) return;
        setError(null);
        try {
            const photos = await uploadPhotos(files, setBusy);
            if (asGallery) {
                const at = insertBlock("gallery", { images: photos, caption: "" });
                setDialog({ type: "gallery", index: at, value: { images: photos, caption: "" } });
            } else {
                const first = insertBlock("photo", { ...photos[0], size: "full", caption: "" });
                photos.slice(1).forEach((photo, i) => {
                    q().updateContents(new Delta().retain(first + 1 + i).insert({ photo: { ...photo, size: "full", caption: "" } }), "user");
                });
                if (photos.length === 1) setDialog({ type: "photo", index: first, value: { ...photos[0], size: "full", caption: "" } });
            }
        } catch (err) {
            setError(err.message);
        }
        setBusy(null);
    };

    const addLink = () => {
        const quill = q();
        const range = quill.getSelection(true);
        const current = quill.getFormat(range).link;
        const answer = window.prompt("The web address for the link (for example gstaichi.org):", current || "");
        if (answer === null) return;
        const address = answer.trim();
        if (!address) {
            quill.format("link", false, "user");
            return;
        }
        const href = /^(https?:|mailto:)/i.test(address) ? address : `https://${address}`;
        if (range.length === 0) {
            const words = (window.prompt("The words to show for the link:", address) || address).trim();
            quill.insertText(range.index, words, { link: href }, "user");
            quill.setSelection(range.index + words.length, 0, "silent");
        } else {
            quill.format("link", href, "user");
        }
    };

    const autoFormat = () => {
        const quill = q();
        const lines = quill.getLines().map(line => {
            const embed = line instanceof BlockEmbed;
            const lineFormats = !embed && line.formats ? line.formats() : {};
            return { line, text: embed ? "" : quill.getText(quill.getIndex(line), line.length()).replace(/\n$/, ""),
                formatted: embed || ["header", "list", "blockquote"].some(k => lineFormats[k]) };
        });
        const plan = autoFormatPlan(lines);
        const counts = { heading: 0, subheading: 0, quote: 0 };
        if (plan.length) {
            quill.history.cutoff();
            plan.forEach(({ index, kind: what }) => {
                counts[what] += 1;
                quill.formatLine(quill.getIndex(lines[index].line), 1,
                    what === "quote" ? { blockquote: true } : { header: what === "heading" ? 2 : 3 }, "user");
            });
            quill.history.cutoff();
        }
        setAutoResult({ ...counts, total: plan.length });
    };

    const startVideoUpload = async (form, file) => {
        setDialog(null);
        setError(null);
        try {
            const created = await apiFetch("/api/tcc/studio/videos", { method: "POST", body: { ...form, publish_at: new Date().toISOString() } });
            insertBlock("video", { slug: created.slug, title: created.title, status: "Uploading", caption: "" });
            setUpload({ title: created.title, sent: 0, total: file.size, status: "Starting…" });
            await uploadVideoFile({ videoId: created.id, file, control: uploadControl.current,
                onProgress: (p) => setUpload({ title: created.title, ...p }) });
            setUpload(null);
            setHasBusyVideos(true);
            refreshVideos();
        } catch (err) {
            setUpload(null);
            setError(err.message === "cancelled" || err.message === "network" || err.message === "timeout"
                ? "The video upload stopped. Open the Videos tab and choose the same file again to continue where it stopped."
                : err.message);
            refreshVideos();
        }
    };

    const setInLibrary = async (info, show) => {
        try {
            await apiFetch(`/api/tcc/studio/videos/${info.id}`, { method: "PUT", body: { show_in_library: show } });
            await refreshVideos();
        } catch (err) {
            setError(err.message);
        }
    };

    const percent = upload && upload.total ? Math.floor((upload.sent / upload.total) * 100) : 0;
    const videoInfo = dialog && dialog.type === "video" && videos ? videos.find(v => v.slug === dialog.value.slug) : null;

    return (
        <div className="tcc-rich-editor">
            <div className="tcc-toolbar" role="toolbar" aria-label="Formatting">
                <ToolButton icon="fa-heading" label="Heading" active={formats.header === 2} onClick={() => toggle("header", 2)} />
                <ToolButton icon="fa-heading tcc-small-icon" label="Subheading" active={formats.header === 3} onClick={() => toggle("header", 3)} />
                <ToolButton icon="fa-bold" label="Bold" active={!!formats.bold} onClick={() => toggle("bold")} />
                <ToolButton icon="fa-italic" label="Italic" active={!!formats.italic} onClick={() => toggle("italic")} />
                <ToolButton icon="fa-list-ul" label="Bullet list" active={formats.list === "bullet"} onClick={() => toggle("list", "bullet")} />
                <ToolButton icon="fa-list-ol" label="Numbered list" active={formats.list === "ordered"} onClick={() => toggle("list", "ordered")} />
                <ToolButton icon="fa-quote-left" label="Quote" active={!!formats.blockquote} onClick={() => toggle("blockquote")} />
                <ToolButton icon="fa-link" label="Link" active={!!formats.link} onClick={addLink} />
                <ToolButton icon="fa-image" label="Photo" onClick={() => photoInput.current.click()} disabled={!!busy} />
                {isArticle && <ToolButton icon="fa-images" label="Photo gallery" onClick={() => galleryInput.current.click()} disabled={!!busy} />}
                {isArticle && <ToolButton icon="fa-video" label="Video" disabled={!!upload}
                    onClick={() => { setDialog({ type: "addVideo" }); if (!videos) refreshVideos(); }} />}
                <ToolButton icon="fa-minus" label="Divider" onClick={() => insertBlock("divider", true)} />
                <ToolButton icon="fa-magic" label="Auto-format" onClick={autoFormat} />
                <ToolButton icon="fa-undo" label="Undo" onClick={() => q().history.undo()} />
                <ToolButton icon="fa-redo" label="Redo" onClick={() => q().history.redo()} />
            </div>
            <input ref={photoInput} type="file" accept="image/*" multiple hidden onChange={(e) => addPhotos(e, false)} />
            <input ref={galleryInput} type="file" accept="image/*" multiple hidden onChange={(e) => addPhotos(e, true)} />

            <div className="tcc-editor-status" role="status" aria-live="polite">
                {busy && <p>{busy}</p>}
                {autoResult && (
                    <div className="tcc-notice tcc-auto-result">
                        <p>{autoResult.total
                            ? `Auto-format made ${autoResult.heading} heading${autoResult.heading === 1 ? "" : "s"}, `
                              + `${autoResult.subheading} subheading${autoResult.subheading === 1 ? "" : "s"} and `
                              + `${autoResult.quote} quote${autoResult.quote === 1 ? "" : "s"}. Please check them.`
                            : "Auto-format found no short numbered lines or quoted lines to change."}</p>
                        <div className="tcc-button-row tcc-left">
                            {autoResult.total > 0 && (
                                <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => { q().history.undo(); setAutoResult(null); }}>
                                    Undo auto-format
                                </button>
                            )}
                            <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => setAutoResult(null)}>OK</button>
                        </div>
                    </div>
                )}
                {upload && (
                    <div className="tcc-progress-wrap">
                        <p className="tcc-progress-label">Uploading the video "{upload.title}": {upload.status} <strong>{percent}%</strong></p>
                        <div className="tcc-progress" aria-hidden="true"><div className="tcc-progress-bar" style={{ width: `${percent}%` }} /></div>
                        <p>{formatBytes(upload.sent)} of {formatBytes(upload.total)}. Keep this page open until the upload is done.
                            You can keep writing, and save the article once the upload is done; the video is prepared after that.</p>
                        <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => uploadControl.current.cancel && uploadControl.current.cancel()}>
                            Stop the upload
                        </button>
                    </div>
                )}
                {error && <p className="tcc-error" role="alert">{error}</p>}
            </div>

            <div ref={holder} className={`tcc-editor-area tcc-mag-flow${isArticle ? "" : " tcc-editor-short"}`} />
            <p className="tcc-field-hint">Tap a photo{isArticle ? ", gallery or video" : ""} in the text to change its caption, size or place, or to delete it.</p>

            {dialog && dialog.type === "photo" && (
                <PhotoDialog value={dialog.value} onClose={() => setDialog(null)} onSave={(v) => replaceAt(dialog.index, "photo", v)}
                    onMove={(d) => moveAt(dialog.index, "photo", d)} onDelete={() => removeAt(dialog.index)} />
            )}
            {dialog && dialog.type === "gallery" && (
                <GalleryDialog value={dialog.value} onClose={() => setDialog(null)} onSave={(v) => replaceAt(dialog.index, "gallery", v)}
                    onMove={(d) => moveAt(dialog.index, "gallery", d)} onDelete={() => removeAt(dialog.index)} onAddPhotos={uploadPhotos} />
            )}
            {dialog && dialog.type === "video" && (
                <VideoDialog value={dialog.value} info={videoInfo} onClose={() => setDialog(null)} onSave={(v) => replaceAt(dialog.index, "video", v)}
                    onMove={(d) => moveAt(dialog.index, "video", d)} onDelete={() => removeAt(dialog.index)} onLibraryChange={setInLibrary} />
            )}
            {dialog && dialog.type === "addVideo" && (
                <AddVideoDialog videos={videos} onClose={() => setDialog(null)} onUpload={startVideoUpload}
                    onPick={(v) => {
                        insertBlock("video", { slug: v.slug, title: v.title, status: v.studio_status, thumb: v.thumbnail_url || "", caption: "" });
                        setDialog(null);
                        if (BUSY_STATUSES.includes(v.studio_status)) setHasBusyVideos(true);
                    }} />
            )}
        </div>
    );
});

export default RichEditor;
