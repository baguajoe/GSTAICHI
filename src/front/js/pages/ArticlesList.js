// import React, { useEffect, useState } from "react";
// import { Link } from "react-router-dom";

// export const ArticlesList = () => {
//     const [articles, setArticles] = useState([]); // State for articles
//     const [error, setError] = useState(null); // State for error handling

//     // Fetch articles from the backend
//     useEffect(() => {
//         const fetchArticles = async () => {
//             try {
//                 const response = await fetch(process.env.BACKEND_URL + "/api/articles");
//                 if (!response.ok) {
//                     throw new Error("Failed to fetch articles");
//                 }
//                 const data = await response.json();
//                 setArticles(data);
//                 console.log("articles", data )
//             } catch (err) {
//                 setError(err.message);
//             }
//         };
//         fetchArticles();
//     }, []);

//     if (error) {
//         return (
//             <div className="container">
//                 <h1>Error</h1>
//                 <p>{error}</p>
//             </div>
//         );
//     }

//     if (articles.length === 0) {
//         return (
//             <div className="container">
//                 <h1>Loading Articles...</h1>
//             </div>
//         );
//     }

//     return (
//         <div className="container mt-5">
//             <h1>Articles</h1>
//             <ul className="list-group">
//                 {articles.map((article) => (
//                     <li key={article.id} className="list-group-item">
//                         <Link to={`/articles/${article.id}`}>{article.title}</Link>
//                     </li>
//                 ))}
//             </ul>
//         </div>
//     );
// };


import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

export const ArticlesList = () => {
    const { id } = useParams();
    const [article, setArticle] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (id) {
            const fetchArticle = async () => {
                try {
                    // Fix the string interpolation
                    const response = await fetch(`${process.env.BACKEND_URL}/api/articles/${id}`);
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









