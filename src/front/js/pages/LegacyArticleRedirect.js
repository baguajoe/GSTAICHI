import React, { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { apiFetch } from "../component/tai-chi-company/api";

// Old links to the public Articles page (/articles/<number>) open the same article in Tai Chi Company.
// Articles that were not moved, and anything else, go to the Tai Chi Company articles list.
const LegacyArticleRedirect = () => {
    const { id } = useParams();
    const navigate = useNavigate();

    useEffect(() => {
        if (!/^\d+$/.test(id || "")) {
            navigate("/tai-chi-company/articles", { replace: true });
            return;
        }
        apiFetch(`/api/tcc/articles/legacy/${id}`, { auth: false })
            .then(found => navigate(`/tai-chi-company/articles/${found.id}`, { replace: true }))
            .catch(() => navigate("/tai-chi-company/articles", { replace: true }));
    }, [id]);

    return <p className="container my-5 text-center">Opening the article…</p>;
};

export default LegacyArticleRedirect;
