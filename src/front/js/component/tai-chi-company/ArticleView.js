import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useTcc } from "./TccContext";
import ProtectedPlayer from "./ProtectedPlayer";
import { TextSizeButtons } from "./TextSize";
import Overlay from "./Overlay";

// The magazine-style article page body, used by the member reader and by the Studio preview, so the
// preview is exactly what members see. content_html comes from the server, already cleaned
// (src/api/rich_text.py); video blocks are replaced here by the protected player.

export const formatArticleDate = (iso) => iso
    ? new Date(iso.endsWith("Z") ? iso : `${iso}Z`).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })
    : "";

// Faint repeated member email behind the text, so screenshots and photos can be traced
export const ArticleWatermark = ({ text }) => (
    <div className="tcc-article-watermark" aria-hidden="true">
        {Array.from({ length: 40 }, (_, i) => <span key={i}>{text}</span>)}
    </div>
);

// Splits the article into plain HTML pieces and video blocks, keeping the order
const splitContent = (html) => {
    const doc = new DOMParser().parseFromString(`<body>${html || ""}</body>`, "text/html");
    const pieces = [];
    let buffer = "";
    [...doc.body.childNodes].forEach(node => {
        if (node.nodeType === 1 && node.matches("figure.tcc-video-block")) {
            if (buffer) pieces.push({ html: buffer });
            buffer = "";
            const caption = node.querySelector("figcaption");
            pieces.push({ video: node.getAttribute("data-video"), caption: caption ? caption.textContent : "" });
        } else {
            buffer += node.nodeType === 1 ? node.outerHTML : node.textContent;
        }
    });
    if (buffer) pieces.push({ html: buffer });
    return pieces;
};

const ArticleVideo = ({ info, caption }) => {
    const { user, tierName } = useTcc();
    let body;
    if (!info) {
        body = <div className="tcc-video-note"><p>This video is no longer available.</p></div>;
    } else if (info.locked || info.coming_soon || info.processing || !user) {
        const needed = tierName(info.tier_rank);
        body = (
            <div className="tcc-video-locked">
                {info.thumbnail_url ? <img src={info.thumbnail_url} alt="" /> : <div className="tcc-thumb-placeholder" aria-hidden="true" />}
                <div className="tcc-video-locked-message" role="note">
                    <p className="tcc-player-title">{info.title}</p>
                    {info.locked ? (
                        <>
                            <p>Upgrade to watch. This video is part of the {needed ? `${needed} plan` : "member library"}.</p>
                            <Link to={user ? "/tai-chi-company/account" : "/tai-chi-company/join"} className="custom-btn1 tcc-btn">See the plans</Link>
                        </>
                    ) : info.coming_soon || info.processing ? (
                        <p>Coming soon. This video is still being prepared.</p>
                    ) : (
                        <>
                            <p>Please log in to watch this video.</p>
                            <Link to="/tai-chi-company/login" className="custom-btn1 tcc-btn">Log in</Link>
                        </>
                    )}
                </div>
            </div>
        );
    } else {
        body = <ProtectedPlayer video={info} />;
    }
    return (
        <figure className="tcc-article-video">
            {body}
            {caption && <figcaption>{caption}</figcaption>}
        </figure>
    );
};

// Full-size photo viewer for photos and galleries
const Lightbox = ({ images, start, watermark, onClose }) => {
    const [index, setIndex] = useState(start);
    const closeRef = useRef(null);
    const many = images.length > 1;
    const go = (step) => setIndex(i => (i + step + images.length) % images.length);
    useEffect(() => {
        const opener = document.activeElement;
        if (closeRef.current) closeRef.current.focus();
        const onKey = (e) => {
            if (e.key === "Escape") onClose();
            if (e.key === "ArrowRight" && many) go(1);
            if (e.key === "ArrowLeft" && many) go(-1);
        };
        document.addEventListener("keydown", onKey);
        return () => {
            document.removeEventListener("keydown", onKey);
            if (opener && opener.focus) opener.focus();
        };
    }, []);
    const image = images[index];
    return (
        <Overlay>
            <div className="tcc-lightbox" role="dialog" aria-modal="true" aria-label="Photo" onContextMenu={(e) => e.preventDefault()}
                onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
                <ArticleWatermark text={watermark} />
                <figure>
                    <img src={image.src} alt={image.alt} draggable="false" />
                    {(image.caption || many) && <figcaption>{image.caption}{many && ` (${index + 1} of ${images.length})`}</figcaption>}
                </figure>
                <div className="tcc-lightbox-buttons">
                    {many && <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => go(-1)}>&larr; Previous</button>}
                    <button type="button" className="custom-btn1 tcc-btn" ref={closeRef} onClick={onClose}>Close</button>
                    {many && <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => go(1)}>Next &rarr;</button>}
                </div>
            </div>
        </Overlay>
    );
};

export const ArticleContent = ({ html, videos = {}, watermark }) => {
    const pieces = useMemo(() => splitContent(html), [html]);
    const [lightbox, setLightbox] = useState(null);
    const open = (e) => {
        const img = e.target.closest && e.target.closest("figure.tcc-photo img, figure.tcc-gallery img");
        if (!img) return;
        const figure = img.closest("figure");
        const caption = figure.querySelector("figcaption");
        const all = [...figure.querySelectorAll("img")];
        setLightbox({
            start: all.indexOf(img),
            images: all.map(i => ({ src: i.getAttribute("src"), alt: i.getAttribute("alt") || "", caption: caption ? caption.textContent : "" }))
        });
    };
    const onKey = (e) => { if (e.key === "Enter" || e.key === " ") { open(e); if (e.target.tagName === "IMG") e.preventDefault(); } };
    // Photos open full size with a tap, or with Enter for keyboard users
    const ref = useRef(null);
    useEffect(() => {
        ref.current.querySelectorAll("figure.tcc-photo img, figure.tcc-gallery img").forEach(img => {
            img.setAttribute("tabindex", "0");
            img.setAttribute("role", "button");
            img.setAttribute("draggable", "false");
            img.setAttribute("loading", "lazy");
        });
    }, [pieces]);
    return (
        <div ref={ref} className="tcc-mag-content" onClick={open} onKeyDown={onKey}>
            {pieces.map((piece, i) => (piece.video
                ? <ArticleVideo key={i} info={videos[piece.video]} caption={piece.caption} />
                : <div key={i} className="tcc-mag-flow" dangerouslySetInnerHTML={{ __html: piece.html }} />))}
            {lightbox && <Lightbox {...lightbox} watermark={watermark} onClose={() => setLightbox(null)} />}
        </div>
    );
};

export const ArticleCoverPhoto = ({ article, className = "" }) => (
    article.cover_image_url
        ? <img src={article.cover_image_url} alt="" className={`tcc-article-cover ${className}`} loading="lazy"
            style={{ objectPosition: article.cover_position || "50% 50%" }} />
        : <div className={`tcc-article-cover tcc-thumb-placeholder ${className}`} aria-hidden="true"><span>{article.category || "Article"}</span></div>
);

export const ArticleHeader = ({ article }) => (
    <header className="tcc-mag-header">
        <p className="tcc-badges">
            {article.category && <span className="tcc-badge tcc-badge-soon">{article.category}</span>}
            {article.is_free && <span className="tcc-badge tcc-badge-free">Free for everyone</span>}
        </p>
        <h1 className="tcc-mag-title">{article.title}</h1>
        {article.summary && <p className="tcc-mag-dek">{article.summary}</p>}
        <p className="tcc-mag-meta">
            {article.author && <span>By <strong>{article.author}</strong></span>}
            {article.published_at && <span>{formatArticleDate(article.published_at)}</span>}
            <span>{article.reading_minutes} min read</span>
        </p>
    </header>
);

// The readable article: header, cover, text size buttons and the protected text
const ArticleView = ({ article, size, schoolName }) => {
    const onCopy = (e) => {
        const selected = window.getSelection ? String(window.getSelection()) : "";
        e.preventDefault();
        const licence = article.licensed_to ? `, licensed to ${article.licensed_to}` : "";
        e.clipboardData.setData("text/plain", `${selected}\n\n(c) ${schoolName}${licence}`.trim());
    };
    return (
        <article className="tcc-mag">
            <ArticleHeader article={article} />
            {article.cover_image_url && <ArticleCoverPhoto article={article} className="tcc-mag-cover" />}
            <div className="tcc-mag-tools">
                <TextSizeButtons size={size} />
            </div>
            <div className="tcc-article-protected" onCopy={onCopy} onContextMenu={(e) => e.preventDefault()}>
                <ArticleWatermark text={article.watermark_text} />
                <div className="tcc-article-body tcc-mag-body" style={{ fontSize: `${size.fontSize}px` }}>
                    <ArticleContent html={article.content_html} videos={article.videos} watermark={article.watermark_text} />
                </div>
                <p className="tcc-print-notice">This article is for reading on the website only and cannot be printed.</p>
            </div>
            <p className="tcc-article-licence">
                &copy; {schoolName}.{article.licensed_to ? ` Licensed to ${article.licensed_to}.` : ""} Please do not copy or share.
            </p>
        </article>
    );
};

export default ArticleView;
