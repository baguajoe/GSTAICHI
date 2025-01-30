import React from "react";
import comparativeStudyImage from "../../img/comparativeStudy.png";
import TaiChiChuanCirclesImage from "../../img/TaiChiChuanCircles.jpg";


export const Books = () => {
    const books = [
        {
            title: "Tai Chi Chuan: A Comparative Study",
            description: `
                In Tai Chi Chuan: A Comparative Study, author and renowned practitioner Vincent Chu lays out in clear language and detailed photographs 
                the theory and practice of Tai Chi Chuan. Chu's introduction and teaching clarify important concepts and points of emphasis that have 
                until now remained elusive in the available literature on the subject. From basic demonstrations of proper posture to an eye-opening 
                discussion of 'intent', this book offers something for practitioners of all levels. Chu presents three complete short forms for those 
                interested in learning a Tai Chi Chuan routine suitable to their health and objectives. To facilitate the learning process, video of 
                all three forms can be viewed free online at the Gin Soon Tai Chi Chuan Federation's website (http://www.gstaichi.org).
            `,
            cost: "$27.95",
            image: comparativeStudyImage,
            link: "https://www.gstaichi.org"
        },
        {
            title: "TaiChiChuanCircles",
            description: `
                The Circle is a simple symbol. It is a product of ancient Chinese knowledge and a symbol of ancient Chinese traditional culture. 
                The circle represents the universe and everything that manifests within it. All natural phenomena and humanity's development 
                operate in an infinite process or circle. Therefore, circles represent an idea, an operation, beauty, and protection. 
                
                Physical activity such as Tai Chi Chuan is composed of health, martial arts, and performing arts values. It is done in balanced, 
                steady circular motion and involves the entire body. Whether it is the principle, practice, or confrontational engagement, 
                Tai Chi Chuan adheres to the circle principle.
            `,
            image: TaiChiChuanCirclesImage,
            link: "https://www.gstaichi.org"
        }
    ];

    return (
        <div className="container my-5">
            <h1 className="text-center mb-4">Books</h1>
            <div className="row">
                {books.map((book, index) => (
                    <div key={index} className="col-md-6 mb-4">
                        <div className="card shadow-sm h-100">
                            <img src={book.image} className="card-img-top" alt={book.title} />
                            <div className="card-body">
                                <h4 className="card-title">{book.title}</h4>
                                <p className="card-text" style={{ textAlign: "justify" }}>
                                    {book.description}
                                </p>
                                <p className="card-text font-weight-bold">Cost: {book.cost || "Contact for Pricing"}</p>
                                {book.link && (
                                    <a href={book.link} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                                        More Information
                                    </a>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Books;
