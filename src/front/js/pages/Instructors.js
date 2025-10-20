import React from "react";
import vincentImage from "../../img/VincentHoldBall.jpg";
import ginSoonImage from "../../img/GinSoon2.jpg";
import tonyZhuImage from "../../img/IMG_0986.jpg"; // You'll need to add this image to your img folder

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
            image: ginSoonImage,
            link: "/interviews/gin-soon-chu",
        },
        {
            name: "Master Vincent Chu, M.Ed.",
            description: `
                Vincent Chu, the second son of Gin Soon Chu, is a sixth-generation lineage practitioner of the Yang Style Tai Chi Chuan. 
                He began assisting his father at the Gin Soon Tai Chi Chuan Club in Boston at age 16. He has been teaching at the Brookline 
                Adult and Community Education Program since 1984. Vincent Chu has conducted many workshops and seminars in Canada and Europe 
                and is a frequent contributor to martial arts publications.
            `,
            image: vincentImage,
            link: "/interviews/vincent-chu",
        },
        {
            name: "Master Tony Zhu",
            description: `
                Tony Zhu is the sixth generation Yang Style Tai Chi Chuan lineage practitioner. He was introduced to the theory and practice 
                of Yang Tai Chi Chuan in 1986 by his uncle, Grandmaster Gin Soon Chu. Ever since then, he has been an active Yang Style Tai Chi 
                practitioner. Since 1996, Tony Zhu has been an assistant instructor at the headquarters of the Gin Soon Tai Chi Chuan Federation. 
                In 2000, Tony Zhu travelled with Grandmaster Gin Soon Chu and his son to give seminars on Tai Chi Chuan in Europe. With more than 
                30 years of diligent practice and learning under the supervision of Grandmaster Gin Soon Chu and his son, Vincent Chu, Tony Zhu 
                has mastered the Yang style Tai Chi Chuan.
            `,
            image: tonyZhuImage,
        }
    ];

    return (
        <div className="container my-5">
            <h1 className="text-center mb-4">Instructors</h1>
            <div className="row justify-content-center">
                {instructors.map((instructor, index) => (
                    <div key={index} className="col-md-6 col-lg-4 mb-4">
                        <div className="card shadow-sm h-100">
                            <img
                                src={instructor.image}
                                className="card-img-top"
                                style={{ height: "400px", objectFit: "contain", backgroundColor: "#f8f9fa" }}
                                alt={`Image of ${instructor.name}`}
                            />
                            <div className="card-body d-flex flex-column">
                                <h4 className="card-title">{instructor.name}</h4>
                                <p className="card-text" style={{ textAlign: "justify", flex: 1 }}>
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