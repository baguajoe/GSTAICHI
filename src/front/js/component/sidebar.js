import React from "react";
import { Link } from "react-router-dom";
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
            <h3 className="text-center py-3">Sidebar</h3>
            <nav className="nav flex-column">
                {/* Home */}
                <Link className="nav-link" to="/">
                    Home
                </Link>

                {/* About Us */}
                {/* <Link className="nav-link mt-2" to="/about-us">
                    About Us
                </Link> */}

                {/* Classes */}
                {/* <Link className="nav-link mt-2" to="/classes">
                    Classes
                </Link> */}

                {/* Curriculum */}
                {/* <Link className="nav-link mt-2" to="/curriculum">
                    Curriculum
                </Link> */}

                {/* Events */}
                {/* <Link className="nav-link mt-2" to="/events">
                    Events
                </Link> */}

                {/* History */}
                <Link className="nav-link mt-2" to="/history">
                    History
                </Link>

                {/* Lineage */}
                <Link className="nav-link mt-2" to="/lineage">
                    Lineage
                </Link>

                {/* Instructors */}
                <Link className="nav-link mt-2" to="/instructors">
                    Instructors
                </Link>

                {/* Federal Members */}
                <Link className="nav-link mt-2" to="/federal-members">
                    Federal Members
                </Link>

                {/* Articles */}
                <Link className="nav-link mt-2" to="/articles-list">
                    Articles
                </Link>

                {/* Video Management */}
                <Link className="nav-link mt-2" to="/videos">
                    Video Management
                </Link>

                {/* Video Streaming */}
                <Link className="nav-link mt-2" to="/video-streaming/1/123">
                    Video Streaming (Example)
                </Link>

                {/* Books */}
                <Link className="nav-link mt-2" to="/books">
                    Books
                </Link>
            </nav>
        </div>
    );
};

export default Sidebar;
