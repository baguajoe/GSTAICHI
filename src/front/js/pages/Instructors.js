import React from "react";

export const Instructors = () => {
    const instructors = [
        {
            name: "Master Gin Soon Chu",
            description: `
                Master Gin Soon Chu began his study of Tai Chi Chuan under Master Lai Hok Soon in Hong Kong in 1956. 
                Upon the passing of Master Lai in 1964, he inherited the school. Later, Master Chu became a student 
                of the famous Grand Master Yeung Sau Chung, the world leader of the Yang school. In 1977, he was accepted 
                as a disciple and was made responsible for propagating the Yang family tradition throughout North America. 
                Master Chu personally supervises his classes with the assistance of senior students.
            `,
            image: "https://via.placeholder.com/300x200?text=Master+Gin+Soon+Chu",
            link: "/interviews/gin-soon-chu", // Placeholder for a future link to his interview.
        },
        {
            name: "Vincent Chu, M.Ed.",
            description: `
                Vincent Chu, the second son of Gin Soon Chu, is a sixth-generation lineage practitioner of the Yang Style Tai Chi Chuan. 
                He began assisting his father at the Gin Soon Tai Chi Chuan Club in Boston at age 16. He has been teaching at the Brookline 
                Adult and Community Education Program since 1984. Vincent Chu has conducted many workshops and seminars in Canada and Europe 
                and is a frequent contributor to martial arts publications.
            `,
            image: "https://via.placeholder.com/300x200?text=Vincent+Chu",
            link: "/interviews/vincent-chu", // Placeholder for a future link to his interview.
        },
        {
            name: "Master Gordon Chu",
            description: `
                Placeholder text for Master Gordon Chu. Details about his contributions to the Yang Style Tai Chi Chuan 
                and his teachings will be added soon.
            `,
            image: "https://via.placeholder.com/300x200?text=Master+Gordon+Chu",
            link: "#", // Placeholder link, to be updated later.
        },
    ];

    return (
        <div className="container my-5">
            <h1 className="text-center mb-4">Instructors</h1>
            <div className="row">
                {instructors.map((instructor, index) => (
                    <div key={index} className="col-md-6 mb-4">
                        <div className="card shadow-sm h-100">
                            <img
                                src={instructor.image}
                                className="card-img-top"
                                alt={`Image of ${instructor.name}`}
                            />
                            <div className="card-body">
                                <h4 className="card-title">{instructor.name}</h4>
                                <p className="card-text" style={{ textAlign: "justify" }}>
                                    {instructor.description}
                                </p>
                                {instructor.link && (
                                    <a href={instructor.link} className="btn btn-primary">
                                        Read More
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
