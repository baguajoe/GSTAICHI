import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import "../../styles/articles.css";
import { articlesData } from '../utils/articlesData.js';

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

const FormattedContent = ({ content }) => {
  if (!content) return null;
  return (
    // <div className="content-wrapper">
    //   {content.split('\n').map((paragraph, index) => (
    //     paragraph.trim() && (
    //       <p key={index} className="mb-3">{paragraph}</p>
    //     )
    //   ))}
    // </div>
    <div
      className="content-wrapper"
      dangerouslySetInnerHTML={{ __html: content }}
    />
  );
};

export const Articles = () => {
  const { id } = useParams();
  const [articles] = useState(articlesData);
  const [activeArticle, setActiveArticle] = useState(null);
  const [activeSection, setActiveSection] = useState(null);

  // Set active article when ID changes
  useEffect(() => {
    if (id) {
      const foundArticle = articles.find(article => article.id === parseInt(id));
      if (foundArticle) {
        setActiveArticle(foundArticle);
      }
    }
  }, [id, articles]);

  const filteredArticles = activeSection
    ? articles.filter(article => article.section === activeSection)
    : articles;

  const handleSectionClick = (section) => {
    setActiveSection(section);
    setActiveArticle(null); // Reset active article when changing sections
  };

  return (
    <div className="container-fluid mt-4 articles-div">
      <div className="row">
        {/* Sections Sidebar */}
        <div className="col-md-3">
          <div className="card shadow-sm">
            <div className="card-body">
              <h5 className="card-title mb-3">Categories</h5>
              <div className="list-group">
                <button
                  className={`list-group-item list-group-item-action ${!activeSection ? 'active' : ''}`}
                  onClick={() => handleSectionClick(null)}
                >
                  All Articles
                </button>
                {SECTIONS.map(section => (
                  <button
                    key={section}
                    className={`list-group-item list-group-item-action ${activeSection === section ? 'active' : ''}`}
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
                  <button
                    className="custom-btn-charcoal mb-3"
                    onClick={() => setActiveArticle(null)}
                  >
                    ← Back to Articles
                  </button>
                  <h2 className="mt-3 mb-2" style={{ fontWeight: '600' }}>{activeArticle.title}</h2>
                  <p className="text-muted mb-4">
                    By {activeArticle.author}
                    {activeArticle.section && ` | Category: ${activeArticle.section}`}
                  </p>

                  <div className="mb-4 mx-2 article-content">
                    <FormattedContent content={activeArticle.content} />
                  </div>

                  <div className="copyright-notice">
                    <p>
                      Article By Vincent Chu<br></br>
                      <b>Copyright © 1969-2025 V. Chu. All rights reserved.</b>
                    </p>
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
                              By {article.author}
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
                    <hr className="copyright-divider" />
                    <p>
                      All the articles presented in this web site are provided for informational purposes.
                      Use of any of the articles or images without express written consent of the Gin Soon Tai Chi Chuan Federation is prohibited.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div >
  );
};

export default Articles;