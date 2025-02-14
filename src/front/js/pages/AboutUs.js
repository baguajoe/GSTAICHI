import React, { useState, useEffect, useCallback } from "react";
import GSCYSC from "../../img/GSCYSC.jpg";
import GinSoonBall from "../../img/GinSoonBall.jpg";
import GinSoonSnakeCreep from "../../img/GinSoonSnakeCreep.jpg";
import GinSoonPerryPunch from "../../img/GinSoonPerryPunch.jpg";
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
        zIndex: 1000,
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
                                            src={GSCYSC}
                                            alt="Placeholder"
                                            className="img-fluid"
                                            style={imageStyle}
                                        />
                                    </div>
                                    <div className="col-md-8">
                                        <div className="card-body d-flex align-items-center h-100">
                                            <p className="card-text text-center px-4 mb-0">
                                                The Gin Soon Tai Chi Club was founded in 1969 with permission from Grandmaster
                                                Yeung Sau Chung to propagate the Yang Style Tai Chi Chuan in North America. It is the
                                                oldest school teaching Tai Chi Chuan in the Greater Boston Area today.
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
                                            src={GinSoonBall}
                                            alt="Placeholder"
                                            className="img-fluid"
                                            style={imageStyle}
                                        />
                                    </div>
                                    <div className="col-md-8">
                                        <div className="card-body d-flex align-items-center h-100">
                                            <p className="card-text text-center px-4 mb-0">
                                                Although there are many schools of Tai Chi Chuan available in the United States,
                                                the Gin Soon Tai Chi Club is different from others because its founder Master Gin Soon Chu,
                                                is a disciple who studied with and was authorized to teach by Grandmaster Yang Sau-Chung,
                                                firstborn and heir of the legendary Yang Cheng-Fu.
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
                                            src={GinSoonSnakeCreep}
                                            alt="Placeholder"
                                            className="img-fluid"
                                            style={imageStyle}
                                        />
                                    </div>
                                    <div className="col-md-8">
                                        <div className="card-body d-flex align-items-center h-100">
                                            <p className="card-text text-center px-4 mb-0">
                                                Over the years, many students have graduated from the school and became instructors themselves.
                                                In 1995, the Gin Soon Tai Chi Chuan Federation was established to better serve our members who
                                                come from different countries.
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
                                            src={GinSoonPerryPunch}
                                            alt="Placeholder"
                                            className="img-fluid"
                                            style={imageStyle}
                                        />
                                    </div>
                                    <div className="col-md-8">
                                        <div className="card-body d-flex align-items-center h-100">
                                            <p className="card-text text-center px-4 mb-0">
                                                The headquarters are located at 33 Harrison Avenue, 5th floor, Boston, MA 02111.
                                                Contact Vincent Chu at (617) 542-4442 or via email at chu.v@usa.com.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};