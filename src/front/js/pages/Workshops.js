import React, { useContext } from "react";
import { Context } from "../store/appContext";

export const Workshops = () => {
	const { store, actions } = useContext(Context);

	// Workshop data
	const workshops = [
		{
			location: "Spytihnev",
			dates: "November 24 - November 25",
			description: "Teaching of 15 techniques Small Frame Form",
		},
		{
			location: "Spytihnev",
			dates: "November 26 - November 27",
			description:
				"Finishing the Returning Tai Chi Chuan Form. (continuing from last year)",
		},
		{
			location: "Prague",
			dates: "November 28 - November 29",
			description: "Teaching of 26 Techniques Broadsword (1.5 days)",
		},
		{
			location: "Prague",
			dates: "November 29 - November 30",
			description:
				"Finishing the Medium Frame Form (1.5 days). (continuing from last year)",
		},
		{
			location: "Liberec",
			dates: "December 1",
			description:
				"Teaching Tai Chi Chuan Fundamentals Training (recommended for beginners and advanced)",
		},
		{
			location: "Liberec",
			dates: "December 2 - December 3",
			description: "Teaching of Tai Chi Chuan for Beginners",
		},
	];

	return (
		<div className="container my-4">
			<h1 className="text-center mb-4">Upcoming Workshops</h1>

			{/* General Information */}
			<div className="mb-4">
				<p>
					We are receptive to teaching workshops. So far, we have taught in
					Germany, England, France, the Czech Republic, and Canada, where the Gin
					Soon Tai Chi Chuan Federation has branches. For information regarding
					workshops, contact us.
				</p>
				<p>
					<strong>Czech Republic:</strong> These workshops are run in Czech Republic from approximately November 24th to December
					4th each year. However, the exact dates may differ per year. For more information, contact Karel Nuhlicek at{" "}
					<a href="mailto:karel.nuhlicek@impromat.cz">
						karel.nuhlicek@impromat.cz
					</a>.
				</p>
			</div>

			{/* Workshops Section */}
			<div className="row">
				{workshops.map((workshop, index) => (
					<div key={index} className="col-md-6 mb-4">
						<div className="card shadow">
							<div className="card-body">
								<h4 className="card-title">{workshop.location}</h4>
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
