import React from "react";
import vincentImage from "../../img/VincentHoldBall.jpg";
import ginSoonImage from "../../img/GinSoon2.jpg";
import gordonImage from "../../img/gordonfairlady2.png";
import tonyZhuImage from "../../img/IMG_0986.jpg";

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
        },
        {
            name: "Master Gordon Chu",
            description: `
                Gordon Chu is a sixth-generation lineage practitioner of Classical Yang Family Tai Chi Chuan. He is the third of three sons 
                of Grandmaster Gin Soon Chu. Gordon currently teaches at Gin Soon Tai Chi Club and is a co-successor of Gin Soon Tai Chi 
                Chuan Federation USA.
            `,
            image: gordonImage,
        },
        {
            name: "Master Tony Zhu",
            description: `
                Tony Zhu is a sixth-generation Yang Style Tai Chi Chuan lineage practitioner. He was introduced to the theory and practice 
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