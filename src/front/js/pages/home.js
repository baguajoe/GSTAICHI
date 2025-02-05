import React, { useContext } from "react";
import { Context } from "../store/appContext";
import imageUrl from "../../img/ginssonvincentdalu.png"; // Ensure correct filename
import "../../styles/home.css";

export const Home = () => {
    const { store, actions } = useContext(Context);

    return (
        <div className="text-center home-container">
            <h1 className="text-white">Gin Soon Tai Chi Chuan Federation</h1>
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
