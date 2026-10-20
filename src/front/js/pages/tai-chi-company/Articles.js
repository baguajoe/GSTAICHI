import React from "react";
import { Link } from "react-router-dom";

const Articles = () => (
    <div className="tcc-page tcc-narrow tcc-center">
        <h1>Articles</h1>
        <p className="tcc-lead">Member articles coming soon.</p>
        <Link to="/tai-chi-company/library" className="custom-btn1 tcc-btn">Go to the Library</Link>
    </div>
);

export default Articles;
