import React from "react";
import { Carousel } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import img1 from "../../img/1.jpg"
import img2 from "../../img/2.jpg"
import img3 from "../../img/3.jpg"


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
						<Carousel.Caption className="bg-transparent bg-opacity-75 p-4 rounded">
							<h2 className="mb-3">{section.title}</h2>
							<p className="text-start">{section.content}</p>
						</Carousel.Caption>
					</Carousel.Item>
				))}
			</Carousel>
		</div>
	);
};

export default History;
// import React from "react";
// import { Carousel } from "react-bootstrap";

// export const History = () => {
// 	const sections = [
// 		{
// 			title: "Part 1: Origins and Early Life",
// 			content: `
// 				Yang FuKui (1799-1872), better known as Yeung Lou Sim, was born in Yongnian County in Northern China's Hebei Province. 
// 				Because of poverty, he had to leave his home village at the age of ten for Chenjiagou in Wenxian County in Central China's Henan Province to make a living. 
// 				He served as an attendant in the Chen family there and learned the "Lao Jia" (traditional form) style of the Tai Chi Chuan as well as "Push Hand" and combat with weapons from the famous Chinese boxing Master Chen Changxing (1771-1863). 
// 				After three trips and many years of industrious study and practice, he returned to Yongnian. Before his departure for his home village, Chen Changxing told him that since he had become skillful martial artist, he would not have to worry about food and clothing for the rest of his life.

// 				When Yeung Lo Sim returned to Yongnian County, he put up at the Tai He Tang drugstore, which was run by the Chen family of Chenjiagou. 
// 				The house was belonging to the Wu brothers' (Wu Chengqing, Wu Heqing and Wu Ruqing) were all enthusiasts of the folk martial art. 
// 				They admired Yeung Lou Sim's superb skill and learned martial art from him.

// 				The local people in Yongnian County held Yeung Lou Sim in high esteem and praised his Tai Chi Chuan as "cotton boxing", "soft boxing" or "solvent boxing" for its wonderful effects in overcoming the strong and beating the adversary without injuring him and for its flexible attacking and defending tactics.
// 			`,
// 			image: "https://via.placeholder.com/800x400?text=Origins+and+Early+Life",
// 		},
// 		{
// 			title: "Part 2: Generational Legacy",
// 			content: `
// 				At that time, Wu Ruqing was a councilor in the Sichuan Office of the Judicial Department of the Imperial Court. 
// 				He recommended Yeung Lou Sim to teach Tai Chi Chuan in the ancient capital city of Beijing where many nobles of the Qing Dynasty learned martial art from him. 
// 				The House of Prince Duan, one of the royal families in the capital, and employed a large number of boxing masters and wrestlers, and some of them were anxious to have a trial of strength with Yeung Lou Sim, but he invariably declined their challenge politely. 
// 				One day, a famous boxing master of high prestige insisted on competing with Yeung to see who was the stronger. 
// 				The boxer suggested that they sit on two chairs and pit their right fists against each other. Yeung Lou Sim had no choice but to agree. 
// 				Shortly after the contest began, that boxing master started to sweat all over and his chair creaked as if it was going to fall apart. But Yeung Lou Sim looked as composed and serene as ever. 
// 				Then he got up and in a gentle tone to onlookers: "The master's skill is indeed superb. Only his chair is not as firmly made as mine." 
// 				The man was so moved by his modesty that he never failed to praise Yeung's exemplary conduct and unmatched martial art skill. 
// 				Later on, whenever anyone wanted to try his power with Yeung Lou Sim, Yeung would throw the challenger to the ground without injury him. 
// 				In this way, Yeung Lou Sim gained great fame and high prestige and was nicknamed "Yeung the invincible." 
// 				He was later appointed a martial art officer in the Qing Court with the rank higher than the 7th grade official. When he paid a visited to Chenjiagou to see his old friends, he received a warm welcome.
// 			`,
// 			image: "https://via.placeholder.com/800x400?text=Generational+Legacy",
// 		},
// 		{
// 			title: "Part 3: Global Spread and Refinement",
// 			content: `
// 				Yeung Ching Po's eldest son, Yeung Sau Chung (1907-1985), has been teaching Tai Chi Chuan in Hong Kong since 1949 until his death in 1985. 
// 				Yeung Chung Kee, his second son, retired chairman of The Handan Wushu Association, living at home in Yongnian County, Hebei Province. 
// 				Yeung Chung Tood (Yang Zhendou), the third son, is living and teaching Tai Chi Chuan in Tai Yuan City, Shanzi Province. 
// 				He is also the chairman of Shanzi Yang Style Tai Chi Chuan Research Association. 
// 				In November 1961, he went to Shanghai City to give a Tai Chi Chuan exhibition which caused a great sensation. 
// 				Many Tai Chi Chuan enthusiasts made a special trip to Shanghai to watch him perform. Yeung Sau Chung had three daughters from his second wife. 
// 				They are Yeung Tai Yee, Yeung Ma Lee and Yeung Yee Li, who are living in Hong Kong and carry on their family art of Tai Chi Chuan. 
// 				His first disciple, Ip Tai Tak, retired and living in Hong Kong. His second disciple, Gin Soon Chu, has been teaching Tai Chi Chuan in Boston, Massachusetts since 1969. 
// 				His third disciple, K.H. Chu, is teaching Tai Chi Chuan in England and Europe.
// 			`,
// 			image: "https://via.placeholder.com/800x400?text=Global+Spread+and+Refinement",
// 		},
// 	];

// 	return (
// 		<div className="container my-4">
// 			<h1 className="text-center mb-4">History of Yang Style Tai Chi</h1>

// 			<div id="historyCarousel" className="carousel slide" data-bs-ride="carousel">
// 				<div className="carousel-indicators">
// 					{sections.map((_, index) => (
// 						<button
// 							key={index}
// 							type="button"
// 							data-bs-target="#historyCarousel"
// 							data-bs-slide-to={index}
// 							className={index === 0 ? "active" : ""}
// 							aria-current={index === 0 ? "true" : "false"}
// 							aria-label={`Slide ${index + 1}`}
// 						></button>
// 					))}
// 				</div>

// 				<div className="carousel-inner">
// 					{sections.map((section, index) => (
// 						<div key={index} className={`carousel-item ${index === 0 ? 'active' : ''}`}>
// 							<img
// 								src={section.image}
// 								className="d-block w-100"
// 								alt={section.title}
// 							/>
// 							<div className="carousel-caption d-none d-md-block bg-dark bg-opacity-75 p-4 rounded">
// 								<h2 className="mb-3">{section.title}</h2>
// 								<p className="text-start">{section.content}</p>
// 							</div>
// 						</div>
// 					))}
// 				</div>

// 				<button className="carousel-control-prev" type="button" data-bs-target="#historyCarousel" data-bs-slide="prev">
// 					<span className="carousel-control-prev-icon" aria-hidden="true"></span>
// 					<span className="visually-hidden">Previous</span>
// 				</button>
// 				<button className="carousel-control-next" type="button" data-bs-target="#historyCarousel" data-bs-slide="next">
// 					<span className="carousel-control-next-icon" aria-hidden="true"></span>
// 					<span className="visually-hidden">Next</span>
// 				</button>
// 			</div>

// 			{/* Carousel to display sections */}
// 			<Carousel>
// 				{sections.map((section, index) => (
// 					<Carousel.Item key={index}>
// 						<img
// 							className="d-block w-100"
// 							src={section.image}
// 							alt={section.title}
// 						/>
// 						<div className="carousel-caption d-none d-md-block">
// 							<h2>{section.title}</h2>
// 							<p style={{ textAlign: "justify" }}>{section.content}</p>
// 						</div>
// 					</Carousel.Item>
// 				))}
// 			</Carousel>
// 		</div>
// 	);
// };
