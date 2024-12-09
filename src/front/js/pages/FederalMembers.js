import React, { useContext } from "react";
import { Context } from "../store/appContext";

export const FederalMembers = () => {
	const { store, actions } = useContext(Context);

	// List of federal members
	const members = [
		{ name: "Gin Soon Tai Chi Chuan Club", location: "Headquarters" },
		{ name: "H. Won Tai Chi Institute", location: "New York City" },
		{ name: "Schule Stephan Hagen Tai Chi Chuan", location: "Germany" },
		{ name: "North Shore Tai-Chi Club", location: "Salem, MA" },
		{ name: "Internal Arts Institute", location: "Stuart, FL" },
		{ name: "Rhode Island School of Tai Chi", location: "Rhode Island" },
		{ name: "Nicanor Snow Seacoast Tai-Chi Club", location: "Seacoast" },
		{ name: "Tai Chi Chuan Club Zlin", location: "Zlin, Czech Republic" },
		{ name: "Tai Chi Rennes", location: "Rennes, France" },
		{ name: "Ecole de Tai Chi Chuan", location: "France" },
		{ name: "Tony Zhu", location: "Reading, MA" },
		{ name: "Wu Healing", location: "West Hartford, CT" },
		{ name: "Meditation in Motion", location: "Italy" },
		{ name: "Arthur Soohoo", location: "Roslindale, MA" },
		{ name: "Choi Tai Chi and Qigong", location: "Bayonne, NJ" },
		{ name: "West Wind Tai Chi", location: "Fairbanks, AK" },
	];

	return (
		<div className="container my-4">
			<h1 className="text-center mb-4">Federal Members</h1>
			<div className="row">
				{members.map((member, index) => (
					<div key={index} className="col-md-6 mb-3">
						<div className="card shadow-sm">
							<div className="card-body">
								<h5 className="card-title">{member.name}</h5>
								<p className="card-text">
									<strong>Location:</strong> {member.location}
								</p>
							</div>
						</div>
					</div>
				))}
			</div>
		</div>
	);
};
