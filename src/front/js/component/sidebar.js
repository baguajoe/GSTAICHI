import React from "react";
import { Link } from "react-router-dom";

export const Sidebar = () => {
    return (
        <div className="d-flex flex-column bg-light" style={{ height: "100vh", width: "250px" }}>
            <h3 className="text-center py-3">Sidebar</h3>
            <nav className="nav flex-column px-3">
                {/* History */}
                <Link className="nav-link" to="/history">
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

                {/* Videos */}
                <Link className="nav-link mt-2" to="/videos">
                    Videos
                </Link>

                {/* Books */}
                <Link className="nav-link mt-2" to="/books">
                    Books
                </Link>

                {/* Articles */}
                <Link className="nav-link mt-2" to="/articles">
                    Articles
                </Link>
            </nav>
        </div>
    );
};

export default Sidebar;
