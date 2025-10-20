import React from "react";
import { Link, useLocation } from "react-router-dom";
// import ginSoonImg from "../../img/gstaichi_sm.gif";
import ginSoonImg from "../../img/GSL.png";

import "../../styles/sidebar.css";


export const Sidebar = () => {
    const location = useLocation();

    return (
        <div
            className="d-flex flex-column bg-light sidebar-div"
            id="sidebar-div"
            style={{
                minHeight: "100%",
                width: "250px",
                borderRight: "1px solid #ddd",
                padding: "15px",
            }}
        >
            <Link to="/">
                <img src={ginSoonImg} alt="Gin Soon" className="sidebar-logo my-4" />
            </Link>
            <nav className="nav flex-column">
                <Link
                    className={`nav-link ${location.pathname === "/" ? "active" : ""}`}
                    to="/"
                >
                    Home
                </Link>

                <Link
                    className={`nav-link mt-2 ${location.pathname === "/history" ? "active" : ""}`}
                    to="/history"
                >
                    History
                </Link>

                <Link
                    className={`nav-link mt-2 ${location.pathname === "/lineage" ? "active" : ""}`}
                    to="/lineage"
                >
                    Lineage
                </Link>

                <Link
                    className={`nav-link mt-2 ${location.pathname === "/instructors" ? "active" : ""}`}
                    to="/instructors"
                >
                    Instructors
                </Link>

                <Link
                    className={`nav-link mt-2 ${location.pathname === "/federation-members" ? "active" : ""}`}
                    to="/federation-members"
                >
                    Federation Members
                </Link>


                <Link
                    className={`nav-link mt-2 ${location.pathname === "/articles-list" || location.pathname.startsWith("/articles") ? "active" : ""}`}
                    to="/articles-list"
                >
                    Articles
                </Link>

                <Link
                    className={`nav-link mt-2 ${location.pathname === "/gallery" ? "active" : ""}`}
                    to="/gallery"
                >
                    Gallery
                </Link>

                <Link
                    className={`nav-link mt-2 ${location.pathname === "/videos" ? "active" : ""}`}
                    to="/videos"
                >
                    Video
                </Link>

                <Link
                    className={`nav-link mt-2 ${location.pathname === "/books" ? "active" : ""}`}
                    to="/books"
                >
                    Books & DVDs
                </Link>
            </nav>
        </div>
    );
};

export default Sidebar;
