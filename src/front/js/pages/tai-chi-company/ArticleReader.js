import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch } from "../../component/tai-chi-company/api";
import { useTextSize } from "../../component/tai-chi-company/TextSize";
import ArticleView, { ArticleHeader, ArticleCoverPhoto } from "../../component/tai-chi-company/ArticleView";

const BackLink = () => (
    <p className="tcc-mag-back"><Link to="/tai-chi-company/articles" className="tcc-text-link">&larr; Back to Articles</Link></p>
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

    return (
        <div className="tcc-page tcc-article-page">
            <BackLink />
            {article.locked ? (
                <article className="tcc-mag">
                    <ArticleHeader article={{ ...article, summary: "" }} />
                    <ArticleCoverPhoto article={article} className="tcc-mag-cover" />
                    {article.summary && <p className="tcc-lead tcc-section">{article.summary}</p>}
                    <div className="tcc-upgrade" role="note">
                        <p className="tcc-player-title">Subscribe to read</p>
                        <p>Every plan includes all member articles.</p>
                        <div className="tcc-button-row">
                            <Link to={user ? "/tai-chi-company/account" : "/tai-chi-company/join"} className="custom-btn1 tcc-btn">See the plans</Link>
                            {!user && <Link to="/tai-chi-company/login" className="tcc-btn tcc-btn-outline">Log in</Link>}
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
