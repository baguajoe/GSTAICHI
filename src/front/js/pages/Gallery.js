import React from "react";
import ginSoonChuck from "../../img/GinSoonChuck.jpg";
import prague from "../../img/Prague.jpg";
import prague2 from "../../img/Prague2.jpg";
import riverBoat from "../../img/RiverBoat.jpg";
import riverBoat2 from "../../img/RiverBoat2.jpg";
import small from "../../img/small.jpg";
import vincent from "../../img/Vincent.jpg";
import vincentDimitrisJoe from "../../img/VincentDimitrisJoe.jpg";
import vincentFuWen from "../../img/VincentFuWen.jpg";
import ginSoon2 from "../../img/GinSoon2.jpg";
import ysc from "../../img/YSC.jpg";
import img1 from "../../img/1.jpg";
import img2 from "../../img/2.jpg";
import img3 from "../../img/3.jpg";
import img4 from "../../img/4.jpg";
import img5 from "../../img/5.jpg";
import img6 from "../../img/6.jpg";
import img7 from "../../img/7.jpg";
import img8 from "../../img/8.jpg";
import img9 from "../../img/9.jpg";
import img10 from "../../img/10.jpg";
import img11 from "../../img/11.jpg";
import img12 from "../../img/12.jpg";
import { Carousel } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import "../../styles/gallery.css"

const images = [
    { src: ginSoonChuck, alt: "" },
    { src: prague, alt: "Workshop In Prague" },
    { src: prague2, alt: "Workshop In Prague" },
    { src: riverBoat, alt: "August Moon Festival" },
    { src: riverBoat2, alt: "August Moon Festival" },
    { src: small, alt: "Small Circle Circle Workshop" },
    { src: vincent, alt: "Peter Hunt, Master Yang Zhengdo, Yang June, Vincent Chu" },
    { src: vincentDimitrisJoe, alt: "Vincent, Dimitris, and Joe" },
    { src: vincentFuWen, alt: "Vincent Fu Zhong Wen" },
    { src: ginSoon2, alt: "Gin Soon Portrait" },
    { src: ysc, alt: "YSC Event" },
    { src: img1, alt: "New Years Celebration 2009" },
    { src: img2, alt: "New Years Celebration 2009" },
    { src: img3, alt: "New Years Celebration 2009" },
    { src: img4, alt: "New Years Celebration 2009" },
    { src: img5, alt: "New Years Celebration 2009" },
    { src: img6, alt: "New Years Celebration 2009" },
    { src: img7, alt: "New Years Celebration 2009" },
    { src: img8, alt: "New Years Celebration 2009" },
    { src: img9, alt: "New Years Celebration 2009" },
    { src: img10, alt: "New Years Celebration 2009" },
    { src: img11, alt: "New Years Celebration 2009" },
    { src: img12, alt: "New Years Celebration 2009" }
];



export const Gallery = () => {
    const arrowStyle = {
        position: "absolute",
        top: "calc(50% + 70px)", // Offset to account for header and nav
        transform: "translateY(-50%)",
        fontSize: "2rem",
        color: "#590d0d",
        cursor: "pointer",
        zIndex: 1000,
        transition: "color 0.3s ease",
        // backgroundColor: "rgba(255, 255, 255, 0.8)",
        borderRadius: "50%",
        padding: "10px",
    };

    return (
        <div className="container py-5">
            <h1 className="text-center display-4 mb-4">Gallery</h1>

            <div className="carousel-container" style={{ backgroundColor: '#f8f9fa' }}>
            <Carousel 
                    // ref={carouselRef}
                    prevIcon={
                        <i
                            className="fa-solid fa-circle-chevron-left"
                            style={{ ...arrowStyle, left: "0px" }}
                            onMouseOver={(e) => e.target.style.color = "#400909"}
                            onMouseOut={(e) => e.target.style.color = "#590d0d"}
                        />
                    }
                    nextIcon={
                        <i
                            className="fa-solid fa-circle-chevron-right"
                            style={{ ...arrowStyle, right: "0px" }}
                            onMouseOver={(e) => e.target.style.color = "#400909"}
                            onMouseOut={(e) => e.target.style.color = "#590d0d"}
                        />
                    }
                >
                    {images.map((image, index) => (
                        <Carousel.Item key={index}>
                            <div
                                style={{
                                    height: '70vh',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    backgroundColor: '#e9ecef'
                                }}
                            >
                                <img
                                    src={image.src}
                                    alt={image.alt}
                                    style={{
                                        height: 'auto',
                                        width: 'auto',
                                        minHeight: '100%',
                                        maxHeight: '100%',
                                        maxWidth: '100%',
                                        objectFit: 'contain'
                                    }}
                                />
                            </div>
                            <Carousel.Caption className="bg-dark bg-opacity-50 rounded p-2">
                                <h5 className="mb-0">{image.alt}</h5>
                            </Carousel.Caption>
                        </Carousel.Item>
                    ))}
                </Carousel>
            </div>
        </div>
    );
};

export default Gallery;