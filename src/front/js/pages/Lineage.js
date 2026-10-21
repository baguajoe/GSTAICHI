import React from "react";
import { lineage } from "../utils/schoolInfo";

export const Lineage = () => {
    return (
        <div className="container my-5">
            <h1 className="text-center mb-4">Yang Style Tai Chi Lineage</h1>
            <div className="row">
                {lineage.map((person, index) => (
                    // <div key={index} className="col-md-6 mb-4">
                    <div key={index} className="col-lg-4 mb-4 col-md-6">
                        <div className="card shadow-sm h-100">
                            <img
                                src={person.image}
                                className="card-img-top"
                                // style={{ maxWidth: "200px" }}
                                alt={person.name}
                            />
                            <div className="card-body">
                                <h4 className="card-title">{person.name}</h4>
                                <p className="card-subtitle text-muted">{person.lifespan}</p>
                                <p className="card-text mt-3" style={{ textAlign: "justify" }}>
                                    {person.description}
                                </p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div >
    );
};

export default Lineage;
