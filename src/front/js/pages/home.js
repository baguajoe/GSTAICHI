import React, { useContext } from "react";
import { Link } from "react-router-dom";
import { Context } from "../store/appContext";
import imageUrl from "../../img/ginssonvincentdalu.png"; // Ensure correct filename
import "../../styles/home.css";

export const Home = () => {
    const { store, actions } = useContext(Context);

    return (
        <div className="text-center home-container">
            <h1 className="text-white">Gin Soon Tai Chi Chuan Federation</h1>
            <div className="tcc-home-banner">
                <h2 className="tcc-home-banner-title">New: The Tai Chi Company</h2>
                <p className="tcc-home-banner-text">
                    Learn Tai Chi at home with Master Vincent Chu: video lessons for every level
                </p>
                <Link to="/tai-chi-company" className="tcc-home-banner-btn">Join now</Link>
            </div>
            <p>
                <img src={imageUrl} alt="Uploaded Martial Arts Image" className="custom-image" />
            </p>
            <div className="hours-container">
                <h2 className="text-white">Hours</h2>
                <p className="text-white">Monday - Friday: 4PM - 8PM</p>
                <p className="text-white">Monday and Thursday: 11AM - 1PM</p>
                <p className="text-white">Saturday: 1PM - 4PM</p>
            </div>
        </div>
    );
};
