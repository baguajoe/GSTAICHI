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

const images = [
    { src: ginSoonChuck, alt: "Gin Soon, Chuck Norris" },
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
    return (
        <div className="container py-5">
            <h1 className="text-center mb-4">Gallery</h1>
            <Carousel>
                {images.map((image, index) => (
                    <Carousel.Item key={index}>
                        <img
                            className="d-block w-100"
                            src={image.src}
                            alt={image.alt}
                            style={{ maxHeight: "600px", objectFit: "cover" }}
                        />
                        <Carousel.Caption>
                            <h5>{image.alt}</h5>
                        </Carousel.Caption>
                    </Carousel.Item>
                ))}
            </Carousel>
        </div>
    );
};

export default Gallery;