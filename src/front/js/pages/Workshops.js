import React, { useContext } from "react";
import { Context } from "../store/appContext";
import "../../styles/workshops.css";

export const Workshops = () => {
	const { store, actions } = useContext(Context);

	// Workshop data
	const workshops = [
		{
			location: "Prague",
			dates: "November 21 – November 22",
			description: "Gu Yang Tzu's Yi Jin Gong (2 days)",
		},
		{
			location: "Prague",
			dates: "November 23 – November 24",
			description: "Returning Tai Chi Chuan (2 days)",
		},
		{
			location: "Prague",
			dates: "November 25",
			description: "Day off — rest day, no classes scheduled",
			isRestDay: true,
		},
		{
			location: "Prague",
			dates: "November 26 – November 27",
			description: "Medium Long Form (2 days)",
		},
		{
			location: "Prague",
			dates: "November 28",
			description: "Five Animals Frolics (1 day)",
		},
		{
			location: "Prague",
			dates: "November 29",
			description: "Tai Chi Gong (1 day)",
		},
		{
			location: "Prague",
			dates: "November 30 – December 1",
			description: "43 Techniques Large Circle Form (2 days)",
		},
	];

	return (
		<div className="container my-4 workshops-container">
			<h1 className="text-center mb-4">Upcoming Workshops</h1>

			{/* General Information */}
			<div className="mb-4 workshops-info">
				<p>
					We are receptive to teaching workshops. So far, we have taught in
					Germany, England, France, the Czech Republic, and Canada, where the Gin
					Soon Tai Chi Chuan Federation has branches. For information regarding
					workshops, contact us.
				</p>
				<p>
					<strong>Czech Republic:</strong> These workshops are held in Prague from approximately November 21st to December
					1st each year. However, the exact dates may differ per year. For more information, contact Karel Nuhlicek at{" "}
					<a href="mailto:karel.nuhlicek@impromat.cz">
						karel.nuhlicek@impromat.cz
					</a>.
				</p>
			</div>

			{/* Workshops Section */}
			<div className="row workshop-row">
				{workshops.map((workshop, index) => (
					<div key={index} className="col-md-6 mb-4">
						<div
							className={`card shadow h-100 workshop-card ${workshop.isRestDay ? 'border-secondary' : ''}`}
						>
							<div className="card-body">
								<h4 className="card-title">
									{workshop.isRestDay
										? <i className="fas fa-mug-hot me-2 text-secondary"></i>
										: <i className="fas fa-chalkboard-teacher me-2 text-success"></i>}
									{workshop.location}
								</h4>
								<p className="card-text">
									<strong>Dates:</strong> {workshop.dates}
								</p>
								<p className="card-text">{workshop.description}</p>
							</div>
						</div>
					</div>
				))}
			</div>
		</div>
	);
};

export default Workshops;