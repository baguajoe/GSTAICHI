// navbar.js
import React from "react";
import { Link, useLocation } from "react-router-dom";
// import logo from "../../img/GinSoonLogo.png";
import logo from "../../img/gstaichi_sm.gif";

import banner from "../../img/fedbanner3.gif";
import "../../styles/navbar.css";
import { SITE_MENU, isMenuItemActive } from "./sidebar";

// Bootstrap leaves the hamburger menu open after a tap, because the page never reloads
const closeMenuAfterLinkTap = (e) => {
    if (!e.target.closest("a")) return;
    const menu = window.bootstrap && window.bootstrap.Collapse.getInstance(e.currentTarget.parentElement);
    if (menu) menu.hide();
};


export const Navbar = () => {
    const location = useLocation();

    return (
        <nav className="navbar navbar-expand-lg navbar-light bg-white">
            <div className="container-fluid">
                <div className="navbar-content">
                    {/* Left Logo */}
                    {/* <div className="logo-container">
                        <a className="navbar-brand" href="/">
                            <img src={logo} alt="Gin Soon Tai Chi Chuan Federation Logo" className="navbar-logo" />
                        </a>
                    </div> */}

                    {/* Center Banner */}
                    <div className="banner-container">
                        <Link to="/">
                            <img src={banner} alt="Gin Soon Tai Chi Chuan Federation Banner" className="banner-image" />
                        </Link>
                    </div>

                    {/* Navigation Section */}
                    <div className="nav-section">
                        {/* Navbar Toggle Button */}
                        <button
                            className="navbar-toggler"
                            type="button"
                            data-bs-toggle="collapse"
                            data-bs-target="#navbarNav"
                            aria-controls="navbarNav"
                            aria-expanded="false"
                            aria-label="Toggle navigation"
                        >
                            <span className="navbar-toggler-icon"></span>
                        </button>

                        {/* Navigation Links */}
                        <div className="collapse navbar-collapse" id="navbarNav">
                            <ul className="navbar-nav" onClick={closeMenuAfterLinkTap}>
                                {/* The sidebar's links: phones have no sidebar column */}
                                {SITE_MENU.map(item => (
                                    <li className="nav-item d-md-none" key={item.to}>
                                        <Link
                                            className={`nav-link ${isMenuItemActive(item, location.pathname) ? "active" : ""}`}
                                            to={item.to}
                                        >
                                            {item.label}
                                        </Link>
                                    </li>
                                ))}
                                <li className="nav-item">
                                    <Link
                                        className={`nav-link ${location.pathname === "/about-us" ? "active" : ""}`}
                                        to="/about-us"
                                    >
                                        About Us
                                    </Link>
                                </li>
                                <li className="nav-item">

                                    <Link
                                        className={`nav-link ${location.pathname === "/classes" ? "active" : ""}`}
                                        to="/classes"
                                    >
                                        Classes
                                    </Link>
                                </li>
                                <li className="nav-item">

                                    <Link
                                        className={`nav-link ${location.pathname === "/curriculum" ? "active" : ""}`}
                                        to="/curriculum"
                                    >
                                        Curriculum
                                    </Link>
                                </li>
                                <li className="nav-item">

                                    <Link
                                        className={`nav-link ${location.pathname === "/workshops" ? "active" : ""}`}
                                        to="/workshops"
                                    >
                                        Workshops
                                    </Link>
                                </li>
                                <li className="nav-item">

                                    <Link
                                        className={`nav-link ${location.pathname === "/contact-us" ? "active" : ""}`}
                                        to="/contact-us"
                                    >
                                        Contact Us
                                    </Link>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    );
};