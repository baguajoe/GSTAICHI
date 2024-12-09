import React, { useContext } from "react";
import { Context } from "../store/appContext";

export const Classes = () => {
	const { store, actions } = useContext(Context);

	// Class schedule data
	const schedule = [
		{
			day: "Monday",
			dayClasses: "11AM to 1PM",
			eveningClasses: "4PM - 8PM",
		},
		{
			day: "Tuesday",
			dayClasses: "N/A",
			eveningClasses: "4PM - 8PM",
		},
		{
			day: "Wednesday",
			dayClasses: "N/A",
			eveningClasses: "4PM - 8PM",
		},
		{
			day: "Thursday",
			dayClasses: "11AM to 1PM",
			eveningClasses: "4PM - 8PM",
		},
		{
			day: "Friday",
			dayClasses: "N/A",
			eveningClasses: "4PM - 8PM",
		},
		{
			day: "Saturday",
			dayClasses: "1PM to 4PM",
			eveningClasses: "N/A",
		},
	];

	return (
		<div className="container">
			<h1 className="text-center my-4">Class Schedule</h1>
			<table className="table table-striped table-bordered">
				<thead className="thead-dark">
					<tr>
						<th>Day</th>
						<th>Day Classes</th>
						<th>Evening Classes</th>
					</tr>
				</thead>
				<tbody>
					{schedule.map((entry, index) => (
						<tr key={index}>
							<td>{entry.day}</td>
							<td>{entry.dayClasses}</td>
							<td>{entry.eveningClasses}</td>
						</tr>
					))}
				</tbody>
			</table>
		</div>
	);
};
