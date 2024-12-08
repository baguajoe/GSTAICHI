import React, { useState, useEffect, useContext } from "react";
import { Link } from "react-router-dom";

import { Context } from "../store/appContext";

export const Classes = () => {
	const { store, actions } = useContext(Context);

	return (
		<div className="container">
			<h1>Classes</h1>
		</div>
	);
};
