import React from "react";
import { Link } from "react-router-dom";
import ginSoonImg from "../../img/gstaichi_sm.gif";
import "../../styles/sidebar.css";


export const Sidebar = () => {
    return (
        <div
            className="d-flex flex-column bg-light sidebar-div"
            style={{
                height: "100vh",
                width: "250px",
                borderRight: "1px solid #ddd",
                padding: "15px",
            }}
        >
            <img src={ginSoonImg} alt="Gin Soon"
                className="rounded"
            />
            <nav className="nav flex-column">
                <Link className="nav-link" to="/">
                    Home
                </Link>

                <Link className="nav-link mt-2" to="/history">
                    History
                </Link>

                <Link className="nav-link mt-2" to="/lineage">
                    Lineage
                </Link>

                <Link className="nav-link mt-2" to="/instructors">
                    Instructors
                </Link>

                <Link className="nav-link mt-2" to="/federal-members">
                    Federal Members
                </Link>

                <Link className="nav-link mt-2" to="/articles-list">
                    Articles
                </Link>
                <Link className="nav-link mt-2" to="/gallery">
                    Gallery
                </Link>

                <Link className="nav-link mt-2" to="/videos">
                    Video Management
                </Link>

                <Link className="nav-link mt-2" to="/video-streaming/1/123">
                    Video Streaming (Example)
                </Link>

                <Link className="nav-link mt-2" to="/books">
                    Books
                </Link>
            </nav>
        </div>
    );
};

export default Sidebar;
