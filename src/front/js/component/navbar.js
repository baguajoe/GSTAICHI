// navbar.js
import React from "react";
import { Link } from "react-router-dom";
import logo from "../../img/GinSoonLogo.png";
import banner from "../../img/fedbanner3.gif";
import "../../styles/navbar.css";

export const Navbar = () => {
    return (
        <nav className="navbar navbar-expand-lg navbar-light bg-white">
            <div className="container-fluid">
                <div className="navbar-content">
                    {/* Left Logo */}
                    <div className="logo-container">
                        <a className="navbar-brand" href="/">
                            <img src={logo} alt="Gin Soon Tai Chi Chuan Federation Logo" className="navbar-logo" />
                        </a>
                    </div>

                    {/* Center Banner */}
                    <div className="banner-container">
                        <img src={banner} alt="Gin Soon Tai Chi Chuan Federation Banner" className="banner-image" />
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
                            <ul className="navbar-nav">
                                <li className="nav-item">
                                    <Link className="nav-link active" to="/about-us">
                                        About Us
                                    </Link>
                                </li>
                                <li className="nav-item">
                                    <Link className="nav-link" to="/classes">
                                        Classes
                                    </Link>
                                </li>
                                <li className="nav-item">
                                    <Link className="nav-link" to="/curriculum">
                                        Curriculum
                                    </Link>
                                </li>
                                <li className="nav-item">
                                    <Link className="nav-link" to="/events">
                                        Events
                                    </Link>
                                </li>
                                <li className="nav-item">
                                    <Link className="nav-link" to="/contact-us">
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