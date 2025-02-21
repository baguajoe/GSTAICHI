import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const SECTIONS = [
    'Application',
    'Forms',
    'Health',
    'Masters',
    'Philosophy',
    'Power',
    'Push Hands',
    'Qigong',
    'Technique',
    'Weapons',
    'Other'
];

export const ArticlesList = () => {
    const [articles, setArticles] = useState([]);
    const [error, setError] = useState(null);
    const [activeSection, setActiveSection] = useState(null);

    useEffect(() => {
        const fetchArticles = async () => {
            try {
                const response = await fetch(`${process.env.BACKEND_URL}/api/articles`);
                if (!response.ok) {
                    throw new Error("Failed to fetch articles");
                }
                const data = await response.json();
                setArticles(data);
            } catch (err) {
                setError(err.message);
            }
        };
        fetchArticles();
    }, []);

    const filteredArticles = activeSection
        ? articles.filter(article => {
            if (activeSection === 'Other') {
                // Show articles with no section or sections not in SECTIONS list
                return !article.section || !SECTIONS.includes(article.section) || article.section === 'Other';
            }
            return article.section === activeSection;
        })
        : articles;

    if (error) {
        return (
            <div className="container">
                <h1>Error</h1>
                <p>{error}</p>
            </div>
        );
    }

    if (articles.length === 0) {
        return (
            <div className="container">
                <h1>Loading Articles...</h1>
            </div>
        );
    }

    return (
        <div className="container-fluid mt-5 articles-list">
            <div className="row">
                {/* Sections Sidebar */}
                <div className="col-md-3">
                    <div className="card shadow-sm">
                        <div className="card-body">
                            <h5 className="card-title mb-3">Categories</h5>
                            <div className="nav flex-column nav-pills">
                                <button
                                    className={`nav-link text-start mb-2 ${!activeSection ? 'active' : ''}`}
                                    onClick={() => setActiveSection(null)}
                                >
                                    All Articles
                                </button>
                                {SECTIONS.map(section => (
                                    <button
                                        key={section}
                                        className={`nav-link text-start mb-2 ${activeSection === section ? 'active' : ''}`}
                                        onClick={() => setActiveSection(section)}
                                    >
                                        {section}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Articles List */}
                <div className="col-md-9">
                    <div className="card shadow-sm">
                        <div className="card-body">
                            <h2 className="mb-4">
                                {activeSection ? `${activeSection} Articles` : 'All Articles'}
                            </h2>
                            <div className="row row-cols-1 row-cols-md-2 g-4">
                                {filteredArticles.map((article) => (
                                    <div key={article.id} className="col">
                                        <Link
                                            to={`/articles/${article.id}`}
                                            className="text-decoration-none"
                                        >
                                            <div className="card h-100 hover-effect border-0 shadow-sm">
                                                <div className="card-body">
                                                    <h5 className="card-title mb-2">
                                                        {article.title}
                                                    </h5>
                                                    <p className="card-text text-muted mb-2">
                                                        By {article.author}
                                                    </p>
                                                    <p className="card-text text-muted small">
                                                        Published on {article.publication_date}
                                                    </p>
                                                    {article.section && (
                                                        <span className="badge bg-light text-dark">
                                                            {article.section}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </Link>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="copyright-notice">
                            All articles presented on this website are provided for informational purposes. Use of any articles or images without express written consent of the Gin Soon Tai Chi Chuan Federation is prohibited.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};