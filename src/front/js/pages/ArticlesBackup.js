import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import "../../styles/articles.css";
import { articlesData } from '../utils/articlesData.js'; // Import the articles data

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
    <div className="content-wrapper">
      {content.split('\n').map((paragraph, index) => (
        paragraph.trim() && (
          <p key={index} className="mb-3">{paragraph}</p>
        )
      ))}
    </div>
  );
};

export const Articles = () => {
  const { id } = useParams();
  const [articles] = useState(articlesData); // Use the imported data directly
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
                  <h2 className="mb-3">{activeArticle.title}</h2>
                  <p className="text-muted">
                    By {activeArticle.author} | Published on {activeArticle.publication_date}
                    {activeArticle.section && ` | Category: ${activeArticle.section}`}
                  </p>
                  <div className="mb-4">
                    <h4 className="mb-3">Part 1</h4>
                    <FormattedContent content={activeArticle.content_part1} />
                  </div>
                  {activeArticle.content_part2 && (
                    <div>
                      <h4 className="mb-3">Part 2</h4>
                      <FormattedContent content={activeArticle.content_part2} />
                    </div>
                  )}
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