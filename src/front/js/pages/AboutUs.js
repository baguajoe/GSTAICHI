import React, { useState, useEffect, useCallback } from "react";
import { school } from "../utils/schoolInfo";
import "../../styles/aboutUs.css";

export const AboutUs = () => {
    const [activeSection, setActiveSection] = useState("introduction");
    const sections = ["introduction", "difference", "history", "contact"];

    const navigateSection = useCallback((direction) => {
        setActiveSection(prevSection => {
            const currentIndex = sections.indexOf(prevSection);
            if (direction === 'next') {
                return sections[(currentIndex + 1) % sections.length];
            } else {
                return sections[(currentIndex - 1 + sections.length) % sections.length];
            }
        });
    }, [sections]);

    useEffect(() => {
        const handleKeyPress = (event) => {
            if (event.key === "ArrowLeft") {
                navigateSection('prev');
            } else if (event.key === "ArrowRight") {
                navigateSection('next');
            }
        };

        document.addEventListener("keydown", handleKeyPress);
        return () => document.removeEventListener("keydown", handleKeyPress);
    }, [navigateSection]);

    const handleSectionChange = useCallback((section) => {
        setActiveSection(section);
    }, []);

    const cardStyle = {
        backgroundColor: "#f8f9fa",
        borderRadius: "15px",
        boxShadow: "0 4px 8px rgba(0,0,0,0.1)",
        overflow: "hidden",
        transition: "transform 0.3s ease",
        cursor: "pointer",
        margin: "0 auto"
    };

    const imageStyle = {
        objectFit: "contain",
        width: "100%",
        height: "100%",
        width: "100%",
        backgroundColor: "#f8f9fa"
    };

    const arrowStyle = {
        position: "absolute",
        top: "calc(50% + 70px)", // Offset to account for header and nav
        transform: "translateY(-50%)",
        fontSize: "2rem",
        color: "#590d0d",
        cursor: "pointer",
        zIndex: 100,
        transition: "color 0.3s ease",
        backgroundColor: "rgba(255, 255, 255, 0.8)",
        borderRadius: "50%",
        padding: "10px",
    };

    return (
        <div className="about-us-div container mt-4">
            <div className="row justify-content-center">
                <div className="col-12 col-lg-10 position-relative">
                    <h1 className="text-center mb-4">About Us</h1>

                    {/* Navigation Bar */}
                    <nav className="nav nav-pills nav-justified mb-4">
                        <button
                            className={`nav-link ${activeSection === "introduction" ? "active" : ""}`}
                            onClick={() => handleSectionChange("introduction")}
                        >
                            Introduction
                        </button>
                        <button
                            className={`nav-link ${activeSection === "difference" ? "active" : ""}`}
                            onClick={() => handleSectionChange("difference")}
                        >
                            Why We're Different
                        </button>
                        <button
                            className={`nav-link ${activeSection === "history" ? "active" : ""}`}
                            onClick={() => handleSectionChange("history")}
                        >
                            History
                        </button>
                        <button
                            className={`nav-link ${activeSection === "contact" ? "active" : ""}`}
                            onClick={() => handleSectionChange("contact")}
                        >
                            Contact Information
                        </button>
                    </nav>

                    {/* Left Arrow */}
                    <i
                        className="fa-solid fa-circle-chevron-left arrow-style"
                        style={{ ...arrowStyle, left: "0px" }}
                        onClick={() => navigateSection('prev')}
                        // onMouseOver={(e) => e.target.style.color = "#0b5ed7"}
                        // onMouseOut={(e) => e.target.style.color = "#0d6efd"}
                        onMouseOver={(e) => e.target.style.color = "#400909"}
                        onMouseOut={(e) => e.target.style.color = "#590d0d"}
                    ></i>

                    {/* Right Arrow */}
                    <i
                        className="fa-solid fa-circle-chevron-right"
                        style={{ ...arrowStyle, right: "0px" }}
                        onClick={() => navigateSection('next')}
                        onMouseOver={(e) => e.target.style.color = "#400909"}
                        onMouseOut={(e) => e.target.style.color = "#590d0d"}
                    ></i>

                    {/* Content Sections */}
                    <div className="content px-5">
                        {activeSection === "introduction" && (
                            <div className="card" style={cardStyle}>
                                <div className="row g-0">
                                    <div className="col-md-4">
                                        <img
                                            src={school.images.founded}
                                            alt="Placeholder"
                                            className="img-fluid"
                                            style={imageStyle}
                                        />
                                    </div>
                                    <div className="col-md-8">
                                        <div className="card-body d-flex align-items-center h-100">
                                            <p className="card-text text-center px-4 mb-0">
                                                {school.founded}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeSection === "difference" && (
                            <div className="card" style={cardStyle}>
                                <div className="row g-0">
                                    <div className="col-md-4">
                                        <img
                                            src={school.images.difference}
                                            alt="Placeholder"
                                            className="img-fluid"
                                            style={imageStyle}
                                        />
                                    </div>
                                    <div className="col-md-8">
                                        <div className="card-body d-flex align-items-center h-100">
                                            <p className="card-text text-center px-4 mb-0">
                                                {school.difference}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeSection === "history" && (
                            <div className="card" style={cardStyle}>
                                <div className="row g-0">
                                    <div className="col-md-4">
                                        <img
                                            src={school.images.federation}
                                            alt="Placeholder"
                                            className="img-fluid"
                                            style={imageStyle}
                                        />
                                    </div>
                                    <div className="col-md-8">
                                        <div className="card-body d-flex align-items-center h-100">
                                            <p className="card-text text-center px-4 mb-0">
                                                {school.federation}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeSection === "contact" && (
                            <div className="card" style={cardStyle}>
                                <div className="row g-0">
                                    <div className="col-md-4">
                                        <img
                                            src={school.images.contact}
                                            alt="Placeholder"
                                            className="img-fluid"
                                            style={imageStyle}
                                        />
                                    </div>
                                    <div className="col-md-8">
                                        <div className="card-body d-flex align-items-center justify-content-center h-100">
                                            <p className="card-text text-center px-4 mb-0">
                                                The headquarters are located at<br />
                                                {school.address.join(", ")}.<br />
                                                Contact Vincent Chu at {school.phone}<br />
                                                or via email at {school.email}.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div >
    );
};