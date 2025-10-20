import React from "react";
import { Link } from "react-router-dom";
// import yinyangImg from "../../img/yinyang.gif"; // Import the yin yang image

export const FederationMembers = () => {
	// List of federation members with their links
	const members = [
		{ name: "Gin Soon Tai Chi Chuan Club", location: "Headquarters", link: "/aboutUs", isExternal: false },
		{ name: "H. Won Tai Chi Institute", location: "New York City", link: "http://www.nytaichi.com/", isExternal: true },
		{ name: "Schule Stephan Hagen Tai Chi Chuan", location: "Germany", link: "http://www.yang-taichi.com/", isExternal: true },
		{ name: "North Shore Tai-Chi Club", location: "Salem, MA", link: "http://johntoytaichi.freeservers.com/", isExternal: true },
		{ name: "Internal Arts Institute", location: "Stuart, FL", link: "https://www.internalartsinstitute.com", isExternal: true },
		{ name: "Rhode Island School of Tai Chi", location: "Rhode Island", link: "http://www.ritaichi.com", isExternal: true },
		{ name: "Nicanor Snow Seacoast Tai-Chi Club", location: "Seacoast", link: "http://www.seacoasttaichi.com", isExternal: true },
		{ name: "Tai Chi Chuan Club Zlin", location: "Zlin, Czech Republic", link: "http://www.taijizlin.cz/", isExternal: true },
		{ name: "Tai Chi Rennes", location: "Rennes, France", link: "http://www.multimania.com/taichirennes", isExternal: true },
		{ name: "Ecole de Tai Chi Chuan", location: "France", link: "http://taichi-etc.fr", isExternal: true },
		{ name: "Tony Zhu", location: "Reading, MA", link: "http://www.takehometaichi.com", isExternal: true },
		{ name: "Wu Healing", location: "West Hartford, CT", link: "http://www.wuhealing.com", isExternal: true },
		{ name: "MEDiTATiON iN MOTiON", location: "Italy", link: "http://www.meditationinmotion.eu/index.html", isExternal: true },
		{ name: "Arthur Soohoo", location: "Roslindale, MA", link: "http://roslindaleyoga.com/", isExternal: true },
		{ name: "Choi Tai Chi and Qigong", location: "Bayonne, NJ", link: "https://choitaichiandqigong.org", isExternal: true },
		{ name: "West Wind Tai Chi", location: "Fairbanks, AK", link: "https://www.westwindtaichi.org", isExternal: true },
	];

	return (
		<div className="container my-5">
			<h1 className="text-center mb-5">Federation Members</h1>
			<div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
				{members.map((member, index) => (
					<div key={index} className="col">
						<div className="card shadow-sm h-100">
							<div className="card-body">
								<h5 className="card-title">
									{/* <img 
										src={yinyangImg} 
										alt="yin yang" 
										className="me-2" 
										style={{ verticalAlign: 'middle', width: '20px' }}
									/> */}
									{member.isExternal ? (
										<a 
											href={member.link} 
											target="_blank" 
											rel="noopener noreferrer"
											className="text-decoration-none text-primary"
										>
											{member.name}
										</a>
									) : (
										<Link 
											to={member.link}
											className="text-decoration-none text-primary"
										>
											{member.name}
										</Link>
									)}
								</h5>
								<p className="card-text text-muted mb-0">
									{member.location}
								</p>
							</div>
						</div>
					</div>
				))}
			</div>
		</div>
	);
};

export default FederationMembers;