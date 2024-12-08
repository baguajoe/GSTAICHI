import React, { useState, useEffect, useContext } from "react";
import { Link } from "react-router-dom";

import { Context } from "../store/appContext";

export const AboutUs = () => {
	const { store, actions } = useContext(Context);

	return (
		<div className="container">
			<h1>About Us</h1>
		</div>
	);
};
