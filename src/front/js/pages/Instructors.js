import React from "react";
import { instructors } from "../utils/schoolInfo";

export const Instructors = () => {
    return (
        <div className="container my-5">
            <h1 className="text-center mb-4">Instructors</h1>
            <div className="row justify-content-center">
                {instructors.map((instructor, index) => (
                    <div key={index} className="col-lg-3 col-md-6 mb-4">
                        <div className="card shadow-sm h-100">
                            <div style={{ height: "350px", backgroundColor: "#f8f9fa", display: "flex", alignItems: "center", justifyContent: "center" }}>
                                <img
                                    src={instructor.image}
                                    className="card-img-top"
                                    style={{ maxHeight: "350px", width: "auto", maxWidth: "100%", objectFit: "contain" }}
                                    alt={`Image of ${instructor.name}`}
                                />
                            </div>
                            <div className="card-body d-flex flex-column">
                                <h5 className="card-title">{instructor.name}</h5>
                                <p className="card-text" style={{ flex: 1 }}>
                                    {instructor.description}
                                </p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Instructors;