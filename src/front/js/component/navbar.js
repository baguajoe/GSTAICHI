import React from "react";
import { Link } from "react-router-dom";
import logo from "/workspaces/GSTAICHI/public/fedbanner3.gif"

export const Navbar = () => {
    return (
        <nav className="navbar navbar-expand-lg bg-body-tertiary">
            <div className="container-fluid">
                {/* Logo Section */}
                <a className="navbar-brand" href="/">
                    <img
                        src= {logo} // Adjust path based on where you place the image
                        alt="Gin Soon Tai Chi Chuan Federation Logo"
                        style={{ height: "50px", marginRight: "10px" }} // Adjust height as needed
                    />
                </a>

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
                <div className="collapse navbar-collapse justify-content-end" id="navbarNav">
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
        </nav>
    );
};
