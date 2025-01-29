import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

const FormattedContent = ({ content }) => {
  if (!content) return null;
  
  return (
    <div className="content-wrapper">
      {content.split('\n').map((paragraph, index) => (
        paragraph.trim() && (
          <p key={index} className="mb-3">
            {paragraph}
          </p>
        )
      ))}
    </div>
  );
};

export const Articles = () => {
    const { id } = useParams();
    const [article, setArticle] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (id) {
            const fetchArticle = async () => {
                try {
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
                    <div className="mb-5">
                        <h3 className="mb-3">Part 1</h3>
                        <FormattedContent content={article.content_part1} />
                    </div>
                    <div>
                        <h3 className="mb-3">Part 2</h3>
                        <FormattedContent content={article.content_part2} />
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

// export const Articles = () => {
//     const { id } = useParams();
//     const [article, setArticle] = useState(null);
//     const [error, setError] = useState(null);

//     useEffect(() => {
//         if (id) {
//             const fetchArticle = async () => {
//                 try {
//                     // Fix the string interpolation
//                     const response = await fetch(`${process.env.BACKEND_URL}/api/articles/${id}`);
//                     if (!response.ok) {
//                         throw new Error("Error fetching article");
//                     }
//                     const data = await response.json();
//                     setArticle(data);
//                 } catch (err) {
//                     setError(err.message);
//                 }
//             };
//             fetchArticle();
//         }
//     }, [id]);

//     if (error) {
//         return (
//             <div className="container">
//                 <h1>Error</h1>
//                 <p>{error}</p>
//             </div>
//         );
//     }

//     if (id && !article) {
//         return (
//             <div className="container">
//                 <h1>Loading Article...</h1>
//             </div>
//         );
//     }

//     return (
//         <div className="container mt-5">
//             <h1 className="mb-4">Articles</h1>
            
//             {/* Dropdown Menu */}
//             <div className="dropdown mb-4">
//                 <button
//                     className="btn btn-secondary dropdown-toggle"
//                     type="button"
//                     id="articlesDropdown"
//                     data-bs-toggle="dropdown"
//                     aria-expanded="false"
//                 >
//                     Articles Menu
//                 </button>
//                 <ul className="dropdown-menu" aria-labelledby="articlesDropdown">
//                     <li>
//                         <Link className="dropdown-item" to="/articles">
//                             Articles List
//                         </Link>
//                     </li>
//                 </ul>
//             </div>

//             {/* Display Article if an ID is provided */}
//             {id && article ? (
//                 <div>
//                     <h1 className="mb-4">{article.title}</h1>
//                     <p className="text-muted">
//                         By {article.author} | Published on {article.publication_date}
//                     </p>
//                     <div>
//                         <h3>Part 1</h3>
//                         <p>{article.content_part1}</p>
//                     </div>
//                     <div>
//                         <h3>Part 2</h3>
//                         <p>{article.content_part2}</p>
//                     </div>
//                 </div>
//             ) : (
//                 <div>
//                     <p>Select an option from the dropdown to view articles or browse the list.</p>
//                 </div>
//             )}
//         </div>
//     );
// };