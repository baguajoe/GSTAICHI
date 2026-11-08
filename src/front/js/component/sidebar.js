import React from "react";
import { Link, useLocation } from "react-router-dom";
// import ginSoonImg from "../../img/gstaichi_sm.gif";
import ginSoonImg from "../../img/GSL.png";

import "../../styles/sidebar.css";

// Also shown inside the navbar's hamburger menu on phones, where the sidebar is hidden
export const SITE_MENU = [
    { to: "/", label: "Home" },
    { to: "/history", label: "History" },
    { to: "/lineage", label: "Lineage" },
    { to: "/instructors", label: "Instructors" },
    { to: "/federation-members", label: "Federation Members" },
    { to: "/gallery", label: "Gallery" },
    { to: "/tai-chi-company", label: "The Tai Chi Company", includesSubpages: true },
    { to: "/books", label: "Books & DVDs" },
];

export const isMenuItemActive = (item, pathname) =>
    item.includesSubpages ? pathname.startsWith(item.to) : pathname === item.to;

export const Sidebar = () => {
    const location = useLocation();

    return (
        <div
            className="d-none d-md-flex flex-column bg-light sidebar-div"
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
                {SITE_MENU.map((item, i) => (
                    <Link
                        key={item.to}
                        className={`nav-link ${i > 0 ? "mt-2" : ""} ${isMenuItemActive(item, location.pathname) ? "active" : ""}`}
                        to={item.to}
                    >
                        {item.label}
                    </Link>
                ))}
            </nav>
        </div>
    );
};

export default Sidebar;
