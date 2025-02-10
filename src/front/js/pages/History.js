import React from "react";
import { Carousel } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import img1 from "../../img/wudang1.jpg"
import img2 from "../../img/wudang2.jpg"
import img3 from "../../img/wudang3.jpg"


export const History = () => {
	const sections = [
		{
			title: "Part 1: Origins and Early Life",
			content: `Yang FuKui (1799-1872), better known as Yeung Lou Sim, was born in Yongnian County in Northern China's Hebei Province. 
				Because of poverty, he had to leave his home village at the age of ten for Chenjiagou in Wenxian County in Central China's Henan Province to make a living. 
				He served as an attendant in the Chen family there and learned the "Lao Jia" (traditional form) style of the Tai Chi Chuan as well as "Push Hand" and combat with weapons from the famous Chinese boxing Master Chen Changxing (1771-1863). 
				After three trips and many years of industrious study and practice, he returned to Yongnian. Before his departure for his home village, Chen Changxing told him that since he had become skillful martial artist, he would not have to worry about food and clothing for the rest of his life.`,
			// image: "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/13/f8/5c/05/picture-lake.jpg?w=1200&h=-1&s=1"
			image: img1
		},
		{
			title: "Part 2: Generational Legacy",
			content: `At that time, Wu Ruqing was a councilor in the Sichuan Office of the Judicial Department of the Imperial Court. 
				He recommended Yeung Lou Sim to teach Tai Chi Chuan in the ancient capital city of Beijing where many nobles of the Qing Dynasty learned martial art from him. 
				The House of Prince Duan, one of the royal families in the capital, and employed a large number of boxing masters and wrestlers, and some of them were anxious to have a trial of strength with Yeung Lou Sim, but he invariably declined their challenge politely.`,
			// image: "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/13/f8/5c/05/picture-lake.jpg?w=1200&h=-1&s=1"
			image: img2
		},
		{
			title: "Part 3: Global Spread and Refinement",
			content: `Yeung Ching Po's eldest son, Yeung Sau Chung (1907-1985), has been teaching Tai Chi Chuan in Hong Kong since 1949 until his death in 1985. 
				Yeung Chung Kee, his second son, retired chairman of The Handan Wushu Association, living at home in Yongnian County, Hebei Province. 
				Yeung Chung Tood (Yang Zhendou), the third son, is living and teaching Tai Chi Chuan in Tai Yuan City, Shanzi Province.`,
			// image: "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/13/f8/5c/05/picture-lake.jpg?w=1200&h=-1&s=1"
			image: img3
		}
	];
	return (
		<div className="container py-5">
			<h1 className="text-center mb-4">History of Yang Style Tai Chi</h1>
			<Carousel>
				{sections.map((section, index) => (
					<Carousel.Item key={index}>
						<img
							className="d-block w-100"
							src={section.image}
							alt={section.title}
							style={{ maxHeight: "600px", objectFit: "cover" }}
						/>
						<Carousel.Caption className="bg-transparent p-4">
							<h2 className="mb-3">{section.title}</h2>
							<p className="text-start bg-dark bg-opacity-50 p-3 rounded">{section.content}</p>
						</Carousel.Caption>
					</Carousel.Item>
				))}
			</Carousel>
		</div>
	);
};

export default History;