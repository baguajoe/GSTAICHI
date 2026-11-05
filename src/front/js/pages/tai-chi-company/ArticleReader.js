import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch } from "../../component/tai-chi-company/api";
import { useTextSize } from "../../component/tai-chi-company/TextSize";
import ArticleView, { ArticleHeader, ArticleCoverPhoto } from "../../component/tai-chi-company/ArticleView";
import { usePageMeta } from "../../component/tai-chi-company/pageMeta";

// Title, description and link-preview tags. Free articles can be listed by search engines, with a description
// of the article for them; members-only articles show search engines only the teaser, so they are not listed.
const articleMeta = (article, settings) => {
    if (!article) return null;
    const siteName = settings.app_name || settings.school_name || "";
    const url = `${window.location.origin}/tai-chi-company/articles/${article.id}`;
    const description = (article.summary || "").slice(0, 300);
    return {
        title: siteName ? `${article.title} | ${siteName}` : article.title,
        description,
        url,
        image: article.cover_image_url || null,
        indexable: !!article.is_free,
        structuredData: article.is_free ? {
            "@context": "https://schema.org",
            "@type": "Article",
            headline: article.title,
            description,
            author: article.author ? { "@type": "Person", name: article.author } : undefined,
            datePublished: article.published_at || undefined,
            image: article.cover_image_url || undefined,
            publisher: { "@type": "Organization", name: settings.school_name || siteName },
            mainEntityOfPage: url,
            isAccessibleForFree: true
        } : null
    };
};

const BackLink = () => (
    <p className="tcc-mag-back"><Link to="/tai-chi-company/articles" className="tcc-text-link">&larr; Back to Articles</Link></p>
);

const ArticleReader = () => {
    const { id } = useParams();
    const { settings, user, userLoaded } = useTcc();
    const size = useTextSize();
    const [article, setArticle] = useState(null);
    const [error, setError] = useState(null);
    usePageMeta(articleMeta(article, settings));

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

    return (
        <div className="tcc-page tcc-article-page">
            <BackLink />
            {article.locked ? (
                <article className="tcc-mag">
                    <ArticleHeader article={{ ...article, summary: "" }} />
                    <ArticleCoverPhoto article={article} className="tcc-mag-cover" />
                    {article.summary && <p className="tcc-lead tcc-section">{article.summary}</p>}
                    <div className="tcc-upgrade" role="note">
                        <p className="tcc-player-title">Create a free account to read this</p>
                        <p>All articles are free with an account. No payment needed: just your name, email and a password.</p>
                        <div className="tcc-button-row">
                            <Link to="/tai-chi-company/join?plan=free" className="custom-btn1 tcc-btn">Create free account</Link>
                            <Link to="/tai-chi-company/login" className="tcc-btn tcc-btn-outline">Log in</Link>
                        </div>
                    </div>
                </article>
            ) : (
                <ArticleView article={article} size={size} schoolName={settings.school_name || settings.app_name} />
            )}
            <BackLink />
        </div>
    );
};

export default ArticleReader;
