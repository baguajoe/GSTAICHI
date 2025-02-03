import React, { useContext } from "react";
import { Context } from "../store/appContext";

export const Curriculum = () => {
	const { store, actions } = useContext(Context);

	// Curriculum data
	const curriculum = [
		{
			title: "Solo Forms",
			description:
				"The curriculum includes the 85 Movements Solo Form (divided into small, medium, and large frames), the 108 Movements Solo Form, the Long Form (Tai Chi Chung Chuan), the Fast Form, the 13 Animals Form or 13 Postures, and the 2-Person Sparring Set. Additionally, short forms choreographed by Master Vincent Chu are taught.",
		},
		{
			title: "Push Hand Exercises",
			description:
				"Includes Walking; Stationary Step Single and Double Joint Hand; Active Step Single and Double Joint Hand; Open & Close; Great Pulling; Four Corners & Four Directions; Lan Cho Hua (pick up the broken flowers); and Dynamic Push Hands.",
		},
		{
			title: "Weapons Forms",
			description:
				"Forms include the Staff Form, 13 Spear Techniques Form, Small Flower Spear Form, Knife Form, Sword Form, and the Special Weapon Form (halbert).",
		},
		{
			title: "Power Development Exercises (Qigong)",
			description:
				"Exercises include Wu Chi Posture, Tai Chi Chuan Qigong, and others aimed at enhancing internal energy and qi manipulation.",
		},
	];

	return (
		<div className="container my-4">
			<h1 className="text-center mb-4">Curriculum</h1>
			<p>
				The Gin Soon Tai Chi Chuan Federation's headquarters offers some of
				these forms and is among the few schools in the country teaching
				authentic Yang-style Tai Chi Chuan forms. The training is extensive
				and intensive, taught by knowledgeable instructors. Many observers
				have noted the completeness of the curriculum and the depth of
				instructions.
			</p>

			{/* Curriculum Sections */}
			<div className="row">
				{curriculum.map((section, index) => (
					<div key={index} className="col-md-6 mb-4">
						<div className="card h-100 shadow">
							<div className="card-body">
								<h3 className="card-title">{section.title}</h3>
								<p className="card-text">{section.description}</p>
							</div>
						</div>
					</div>
				))}
			</div>

		</div>
	);
};
