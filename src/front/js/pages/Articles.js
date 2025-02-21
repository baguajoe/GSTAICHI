import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import FormattedContent from '../component/FormattedContent';
import "../../styles/articles.css"

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

export const Articles = () => {
  const { id } = useParams();
  const [articles, setArticles] = useState([]);
  const [activeArticle, setActiveArticle] = useState(null);
  const [activeSection, setActiveSection] = useState(null);
  const [error, setError] = useState(null);

  // Fetch all articles
  useEffect(() => {
    const fetchArticles = async () => {
      try {
        const response = await fetch(`${process.env.BACKEND_URL}/api/articles`);
        if (!response.ok) throw new Error('Error fetching articles');
        const data = await response.json();
        setArticles(data);
      } catch (err) {
        setError(err.message);
      }
    };
    fetchArticles();
  }, []);

  // Fetch single article when ID changes
  useEffect(() => {
    if (id) {
      const fetchArticle = async () => {
        try {
          const response = await fetch(`${process.env.BACKEND_URL}/api/articles/${id}`);
          if (!response.ok) throw new Error('Error fetching article');
          const data = await response.json();
          setActiveArticle(data);
        } catch (err) {
          setError(err.message);
        }
      };
      fetchArticle();
    }
  }, [id]);

  const filteredArticles = activeSection
    ? articles.filter(article => article.section === activeSection)
    : articles;

  if (error) {
    return (
      <div className="container">
        <h1>Error</h1>
        <p>{error}</p>
      </div>
    );
  }

  const handleSectionClick = (section) => {
    setActiveSection(section);
    setActiveArticle(null); // Reset active article when changing sections
  };

  return (
    <div className="container-fluid mt-4 articles-div">
      <div className="row">
        {/* Sections Sidebar */}
        <div className="col-md-3 section-sidebar">
          <div className="card shadow-sm">
            <div className="card-body">
              <h5 className="card-title mb-3">Categories</h5>
              <div className="list-group">
                <button
                  className={`list-group-item list-group-item-action ${!activeSection ? 'active' : ''}`}
                  // onClick={() => setActiveSection(null)}
                  onClick={() => handleSectionClick(null)}
                >
                  All Articles
                </button>
                {SECTIONS.map(section => (
                  <button
                    key={section}
                    className={`list-group-item list-group-item-action ${activeSection === section ? 'active' : ''}`}
                    // onClick={() => setActiveSection(section)}
                    onClick={() => handleSectionClick(section)}
                  >
                    {section}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="col-md-9">
          <div className="card shadow-sm">
            <div className="card-body">
              {activeArticle ? (
                // Single Article View
                <div>
                <div className='d-flex justify-content-between align-items-center mb-3'>
                  <button
                    className="custom-btn-charcoal mb-3"
                    onClick={() => setActiveArticle(null)}
                  >
                    ← Back to Articles
                  </button>
                  <button
                    className="custom-btn-bronze"
                    onClick={() => window.print()}
                  >
                    🖨️ Print Article
                  </button>
                  </div>
                  <h2 className="mb-3">{activeArticle.title}</h2>
                  <p className="text-muted">
                    By {activeArticle.author} | Published on {activeArticle.publication_date}
                    {activeArticle.section && ` | Category: ${activeArticle.section}`}
                  </p>

                  {/* Add translator's note if it exists */}
                  {activeArticle.translator_note && (
                    <div className="translator-note">
                      <strong>Translator's Note:</strong> {activeArticle.translator_note}
                    </div>
                  )}

                  <div className="mb-4">
                    <h4 className="mb-3">Part 1</h4>
                    <FormattedContent
                      content={activeArticle.content_part1}
                      images={activeArticle.images}
                    />
                  </div>

                  {activeArticle.content_part2 && (
                    <div>
                      <h4 className="mb-3">Part 2</h4>
                      <FormattedContent
                        content={activeArticle.content_part2}
                        images={activeArticle.images}
                      />
                    </div>
                  )}

                  {/* Add copyright notice */}
                  <div className="copyright-notice">
                    {activeArticle.copyright_info ||
                      "Copyright © 1969-2025 V. Chu. All rights reserved."}
                  </div>
                </div>
              ) : (
                // Articles List View
                <div>
                  <h2 className="mb-4">
                    {activeSection ? `${activeSection} Articles` : 'All Articles'}
                  </h2>
                  <div className="row row-cols-1 row-cols-md-2 g-4">
                    {filteredArticles.map(article => (
                      <div key={article.id} className="col">
                        <div className="card h-100 hover-shadow">
                          <div className="card-body">
                            <h5 className="card-title">{article.title}</h5>
                            <p className="card-text text-muted">
                              By {article.author} | {article.publication_date}
                            </p>
                            <button
                              className="custom-btn-bronze"
                              onClick={() => setActiveArticle(article)}
                            >
                              Read Article
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="copyright-notice">
                    All articles presented on this website are provided for informational purposes. Use of any articles or images without express written consent of the Gin Soon Tai Chi Chuan Federation is prohibited.
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Articles;