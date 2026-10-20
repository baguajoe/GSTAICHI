import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch } from "../../component/tai-chi-company/api";
import { useTextSize, TextSizeButtons, RichText } from "../../component/tai-chi-company/TextSize";
import { ArticleCover, formatDate } from "./Articles";

const BackLink = () => (
    <p><Link to="/tai-chi-company/articles" className="tcc-text-link">&larr; Back to Articles</Link></p>
);

// Faint repeated member email behind the text, so screenshots and photos can be traced
const ArticleWatermark = ({ text }) => (
    <div className="tcc-article-watermark" aria-hidden="true">
        {Array.from({ length: 40 }, (_, i) => <span key={i}>{text}</span>)}
    </div>
);

const ArticleReader = () => {
    const { id } = useParams();
    const { settings, user, userLoaded } = useTcc();
    const size = useTextSize();
    const [article, setArticle] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!userLoaded) return;
        setArticle(null);
        apiFetch(`/api/tcc/articles/${encodeURIComponent(id)}`).then(setArticle).catch(e => setError(e.message));
        window.scrollTo(0, 0);
    }, [id, userLoaded, user && user.id]);

    if (error) {
        return <div className="tcc-page tcc-narrow"><BackLink /><p className="tcc-error" role="alert">{error}</p></div>;
    }
    if (!article) return <p className="tcc-page tcc-center">Loading…</p>;

    // Copying adds the copyright and licence line
    const onCopy = (e) => {
        const selected = window.getSelection ? String(window.getSelection()) : "";
        e.preventDefault();
        e.clipboardData.setData("text/plain",
            `${selected}\n\n(c) ${settings.school_name || settings.app_name}, licensed to ${article.licensed_to || ""}`.trim());
    };

    return (
        <div className="tcc-page tcc-article-page">
            <BackLink />
            <article className="tcc-article">
                <header>
                    {article.category && <p className="tcc-badges"><span className="tcc-badge tcc-badge-soon">{article.category}</span></p>}
                    <h1>{article.title}</h1>
                    <p className="tcc-article-meta">
                        {article.author && <>By {article.author} · </>}{formatDate(article.published_at)} · {article.reading_minutes} min read
                    </p>
                </header>

                {article.locked ? (
                    <>
                        <ArticleCover article={article} />
                        {article.summary && <p className="tcc-lead tcc-section">{article.summary}</p>}
                        <div className="tcc-upgrade" role="note">
                            <p className="tcc-player-title">Subscribe to read</p>
                            <p>Every plan includes all member articles.</p>
                            <div className="tcc-button-row">
                                <Link to={user ? "/tai-chi-company/account" : "/tai-chi-company/join"} className="custom-btn1 tcc-btn">See the plans</Link>
                                {!user && <Link to="/tai-chi-company/login" className="tcc-btn tcc-btn-outline">Log in</Link>}
                            </div>
                        </div>
                    </>
                ) : (
                    <>
                        <div className="tcc-about-header">
                            <span />
                            <TextSizeButtons size={size} />
                        </div>
                        {article.cover_image_url && <ArticleCover article={article} />}
                        <div className="tcc-article-protected" onCopy={onCopy} onContextMenu={(e) => e.preventDefault()}>
                            <ArticleWatermark text={article.watermark_text} />
                            <div className="tcc-article-body" style={{ fontSize: `${size.fontSize}px` }}>
                                <RichText text={article.content} />
                            </div>
                            <p className="tcc-print-notice">
                                This article is for members to read on the website only and cannot be printed.
                            </p>
                        </div>
                        <p className="tcc-article-licence">
                            &copy; {settings.school_name || settings.app_name}. Licensed to {article.licensed_to}. Please do not copy or share.
                        </p>
                    </>
                )}
            </article>
            <BackLink />
        </div>
    );
};

export default ArticleReader;
