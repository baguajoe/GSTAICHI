import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

export const Articles = () => {
    const { id } = useParams(); // Get the article ID from the URL (if available)
    const [article, setArticle] = useState(null); // State to store the article
    const [error, setError] = useState(null); // State to handle errors

    // Fetch article from the backend
    useEffect(() => {
        if (id) {
            const fetchArticle = async () => {
                try {
                    const response = await fetch(`/api/articles/${id}`);
                    if (!response.ok) {
                        throw new Error("Error fetching article");
                    }
                    const data = await response.json();
                    setArticle(data);
                } catch (err) {
                    setError(err.message);
                }
            };
            fetchArticle();
        }
    }, [id]);

    if (error) {
        return (
            <div className="container">
                <h1>Error</h1>
                <p>{error}</p>
            </div>
        );
    }

    if (id && !article) {
        return (
            <div className="container">
                <h1>Loading Article...</h1>
            </div>
        );
    }

    return (
        <div className="container mt-5">
            <h1 className="mb-4">Articles</h1>

            {/* Dropdown Menu */}
            <div className="dropdown mb-4">
                <button
                    className="btn btn-secondary dropdown-toggle"
                    type="button"
                    id="articlesDropdown"
                    data-bs-toggle="dropdown"
                    aria-expanded="false"
                >
                    Articles Menu
                </button>
                <ul className="dropdown-menu" aria-labelledby="articlesDropdown">
                    <li>
                        <Link className="dropdown-item" to="/articles">
                            Articles List
                        </Link>
                    </li>
                </ul>
            </div>

            {/* Display Article if an ID is provided */}
            {id && article ? (
                <div>
                    <h1 className="mb-4">{article.title}</h1>
                    <p className="text-muted">
                        By {article.author} | Published on {article.publication_date}
                    </p>
                    <div>
                        <h3>Part 1</h3>
                        <p>{article.content_part1}</p>
                    </div>
                    <div>
                        <h3>Part 2</h3>
                        <p>{article.content_part2}</p>
                    </div>
                </div>
            ) : (
                <div>
                    <p>Select an option from the dropdown to view articles or browse the list.</p>
                </div>
            )}
        </div>
    );
};
