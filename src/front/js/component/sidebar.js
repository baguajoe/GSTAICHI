import React from "react";
import { Link } from "react-router-dom";

export const Sidebar = () => {
    return (
        <div className="d-flex flex-column bg-light" style={{ height: "100vh", width: "250px" }}>
            <h3 className="text-center py-3">Sidebar</h3>
            <nav className="nav flex-column px-3">
                <Link className="nav-link" to="/history">
                    History
                </Link>

                <div className="dropdown">
                    <button
                        className="btn btn-light dropdown-toggle w-100 text-start"
                        type="button"
                        id="lineageDropdown"
                        data-bs-toggle="dropdown"
                        aria-expanded="false"
                    >
                        Lineage
                    </button>
                    <ul className="dropdown-menu" aria-labelledby="lineageDropdown">
                        <li>
                            <Link className="dropdown-item" to="/lineage/early">
                                Early Lineage
                            </Link>
                        </li>
                        <li>
                            <Link className="dropdown-item" to="/lineage/modern">
                                Modern Lineage
                            </Link>
                        </li>
                    </ul>
                </div>

                <div className="dropdown mt-2">
                    <button
                        className="btn btn-light dropdown-toggle w-100 text-start"
                        type="button"
                        id="instructorsDropdown"
                        data-bs-toggle="dropdown"
                        aria-expanded="false"
                    >
                        Instructors
                    </button>
                    <ul className="dropdown-menu" aria-labelledby="instructorsDropdown">
                        <li>
                            <Link className="dropdown-item" to="/instructors/senior">
                                Senior Instructors
                            </Link>
                        </li>
                        <li>
                            <Link className="dropdown-item" to="/instructors/junior">
                                Junior Instructors
                            </Link>
                        </li>
                    </ul>
                </div>

                <Link className="nav-link mt-2" to="/federal-members">
                    Federal Members
                </Link>
                <Link className="nav-link mt-2" to="/videos">
                    Videos
                </Link>
                <Link className="nav-link mt-2" to="/books">
                    Books
                </Link>
                <Link className="nav-link mt-2" to="/articles">
                    Articles
                </Link>
            </nav>
        </div>
    );
};

export default Sidebar;
