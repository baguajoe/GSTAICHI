import React, { useContext } from "react";
import { Context } from "../store/appContext";
import "../../styles/workshops.css";

export const Workshops = () => {
	const { store, actions } = useContext(Context);

	// Workshop data
	const workshops = [
		{
			location: "Spytihnev",
			dates: "November 22 - November 23",
			description: "Jin Ba Duan",
		},
		{
			location: "Spytihnev",
			dates: "November 24 - November 25",
			description: "Corrections of The Returning Tai Chi Chuan Form",
		},
		{
			location: "Spytihnev to Prague",
			dates: "November 26",
			description: "Transfer from Spytihnev to Prague",
			isTransfer: true,
		},
		{
			location: "Prague",
			dates: "November 27 - November 28",
			description: "Correction of Medium Frame Form",
		},
		{
			location: "Prague",
			dates: "November 29",
			description: "The Animals Frolics",
		},
		{
			location: "Prague to Liberec",
			dates: "November 29",
			description: "Transfer to Liberec",
			isTransfer: true,
		},
		{
			location: "Liberec",
			dates: "November 30 – December 3",
			description: "Teaching 43 techniques Large Circle Form",
		},
		{
			location: "Prague",
			dates: "December 4",
			description: "Departure from Prague",
			isDeparture: true,
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
					<strong>Czech Republic:</strong> These workshops are run in Czech Republic from approximately November 22nd to December
					4th each year. However, the exact dates may differ per year. For more information, contact Karel Nuhlicek at{" "}
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
							className={`card shadow h-100 workshop-card ${workshop.isTransfer ? 'border-info' : ''} ${workshop.isDeparture ? 'border-warning' : ''}`}
						>
							<div className="card-body">
								<h4 className="card-title">
									{workshop.isTransfer && <i className="fas fa-bus me-2 text-info"></i>}
									{workshop.isDeparture && <i className="fas fa-plane-departure me-2 text-warning"></i>}
									{!workshop.isTransfer && !workshop.isDeparture && <i className="fas fa-chalkboard-teacher me-2 text-success"></i>}
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