import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch } from "../../component/tai-chi-company/api";

export const formatDate = (iso) => iso
    ? new Date(iso).toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" })
    : "";

export const ArticleCover = ({ article }) => (
    article.cover_image_url
        ? <img src={article.cover_image_url} alt="" className="tcc-article-cover" loading="lazy"
            style={{ objectPosition: article.cover_position || "50% 50%" }} />
        : <div className="tcc-article-cover tcc-thumb-placeholder" aria-hidden="true"><span>{article.category || "Article"}</span></div>
);

const ArticleCard = ({ article }) => (
    <Link to={`/tai-chi-company/articles/${article.id}`} className="tcc-article-card">
        <ArticleCover article={article} />
        <div className="tcc-article-card-body">
            <div className="tcc-badges">
                {article.is_new && <span className="tcc-badge tcc-badge-free">New</span>}
                {article.is_free && <span className="tcc-badge tcc-badge-free">Free for everyone</span>}
                {article.category && <span className="tcc-badge tcc-badge-soon">{article.category}</span>}
                {article.locked && <span className="tcc-badge tcc-badge-locked"><i className="fas fa-lock" aria-hidden="true"></i> Subscribe to read</span>}
            </div>
            <h3 className="tcc-video-title">{article.title}</h3>
            <p className="tcc-article-meta">
                {article.author && <>By {article.author} · </>}{formatDate(article.published_at)} · {article.reading_minutes} min read
            </p>
            {article.summary && <p className="tcc-video-desc">{article.summary}</p>}
        </div>
    </Link>
);

const Articles = () => {
    const { settings, user, userLoaded } = useTcc();
    const [articles, setArticles] = useState(null);
    const [canRead, setCanRead] = useState(false);
    const [error, setError] = useState(null);
    const [category, setCategory] = useState("");
    const [search, setSearch] = useState("");
    const [searched, setSearched] = useState("");

    const load = (cat, q) => {
        setError(null);
        const params = new URLSearchParams();
        if (cat) params.set("category", cat);
        if (q) params.set("q", q);
        apiFetch(`/api/tcc/articles?${params}`)
            .then(data => {
                setArticles(data.articles);
                setCanRead(data.can_read);
            })
            .catch(e => setError(e.message));
    };

    useEffect(() => {
        if (userLoaded) load(category, searched);
    }, [userLoaded, user && user.id, category, searched]);

    const categories = [{ key: "", label: "All" }, ...(settings.article_categories || []).map(c => ({ key: c, label: c }))];

    return (
        <div className="tcc-page">
            <h1>Articles</h1>
            <p className="tcc-lead">Articles for members about forms, history, health, training and more.</p>
            {!canRead && articles && (
                <p className="tcc-notice">
                    Articles marked "Free for everyone" can be read by anyone. For the others, <Link to="/tai-chi-company/join">choose any plan</Link> to read them all.
                </p>
            )}

            <form className="tcc-search" role="search" onSubmit={(e) => { e.preventDefault(); setSearched(search.trim()); }}>
                <label htmlFor="article-search">Search the articles</label>
                <div className="tcc-search-row">
                    <input id="article-search" className="tcc-input" type="search" value={search}
                        onChange={e => setSearch(e.target.value)} placeholder="For example: push hands" />
                    <button type="submit" className="custom-btn1 tcc-btn">Search</button>
                </div>
            </form>

            <div className="tcc-tabs" role="group" aria-label="Show articles by category">
                {categories.map(c => (
                    <button key={c.key || "all"} type="button" aria-pressed={category === c.key}
                        className={`tcc-tab${category === c.key ? " active" : ""}`} onClick={() => setCategory(c.key)}>
                        {c.label}
                    </button>
                ))}
            </div>

            {searched && (
                <p>
                    Showing articles that mention <strong>"{searched}"</strong>.{" "}
                    <button type="button" className="tcc-link-button" onClick={() => { setSearch(""); setSearched(""); }}>Show all</button>
                </p>
            )}
            {error && <p className="tcc-error" role="alert">{error}</p>}
            {!articles && !error && <p>Loading…</p>}
            {articles && articles.length === 0 && (
                <p className="tcc-notice">{searched || category ? "No articles match. Try another word or category." : "Member articles are coming soon."}</p>
            )}
            {articles && articles.length > 0 && (
                <div className="tcc-video-grid">
                    {articles.map(a => <ArticleCard key={a.id} article={a} />)}
                </div>
            )}
        </div>
    );
};

export default Articles;
