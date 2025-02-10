import React from "react";
import { Link, useLocation } from "react-router-dom";
// import ginSoonImg from "../../img/gstaichi_sm.gif";
import ginSoonImg from "../../img/GSL.png";

import "../../styles/sidebar.css";


export const Sidebar = () => {
    const location = useLocation();

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
            <img src={ginSoonImg} alt="Gin Soon" className="sidebar-logo" />
            <nav className="nav flex-column">
                <Link 
                    className= {`nav-link ${location.pathname === "/" ? "active" : ""}`} 
                    to="/"
                >
                    Home
                </Link>

                <Link 
                    className= {`nav-link mt-2 ${location.pathname === "/history" ? "active" : ""}`} 
                    to="/history"
                >
                    History
                </Link>

                <Link 
                    className= {`nav-link mt-2 ${location.pathname === "/lineage" ? "active" : ""}`} 
                    to="/lineage"
                >
                    Lineage
                </Link>

                <Link 
                    className= {`nav-link mt-2 ${location.pathname === "/instructors" ? "active" : ""}`} 
                    to="/instructors"
                >
                    Instructors
                </Link>

                <Link 
                    className= {`nav-link mt-2 ${location.pathname === "/federal-members" ? "active" : ""}`} 
                    to="/federal-members"
                >
                    Federal Members
                </Link>

              
                <Link 
                    className= {`nav-link mt-2 ${location.pathname === "/articles-list" ? "active" : ""}`} 
                    to="/articles-list"
                >  
                    Articles
                </Link>
                
                <Link 
                    className= {`nav-link mt-2 ${location.pathname === "/gallery" ? "active" : ""}`} 
                    to="/gallery"
                >  
                    Gallery
                </Link>

                <Link 
                    className= {`nav-link mt-2 ${location.pathname === "/videos" ? "active" : ""}`} 
                    to="/videos"
                >  
                    Video 
                </Link>

                <Link 
                    className= {`nav-link mt-2 ${location.pathname === "/books" ? "active" : ""}`} 
                    to="/books"
                >  
                    Books
                </Link>
            </nav>
        </div>
    );
};

export default Sidebar;
