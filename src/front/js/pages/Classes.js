import React, { useContext } from "react";
import { Context } from "../store/appContext";
import "../../styles/classes.css"

export const Classes = () => {
	const { store, actions } = useContext(Context);

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

	const handlePrint = () => {
		window.print();
	}

	return (
		<div className="container main-content">
			{/* Print button - screen only */}
			<div className="screen-only">
				<div className="text-end mb-3">
					<button onClick={handlePrint} className="custom-btn1">
						<i className="fas fa-print"></i> Print Schedule
					</button>
				</div>
			</div>

			{/* Content visible in both screen and print */}
			<div className="schedule-content">
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

				{/* Contact info - only shows in print */}
				<div className="print-only-contact">
					<p>	Gin Soon Tai Chi Chuan Federation<br />
						33 Harrison Avenue, 5th floor, Boston, MA 02111<br />
						Contact Vincent Chu at (617) 542-4442</p>
				</div>
			</div>
		</div>
	);
};