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
import { Link } from "react-router-dom";

export const ArticlesList = () => {
    const [articles, setArticles] = useState([]);
    const [error, setError] = useState(null);

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
        <div className="container mt-5">
            <h1>Articles</h1>
            <ul className="list-group">
                {articles.map((article) => (
                    <li key={article.id} className="list-group-item">
                        <Link to={`/articles/${article.id}`} className="text-decoration-none">
                            <h5 className="mb-1">{article.title}</h5>
                            <p className="mb-1 text-muted">By {article.author} | {article.publication_date}</p>
                        </Link>
                    </li>
                ))}
            </ul>
        </div>
    );
};