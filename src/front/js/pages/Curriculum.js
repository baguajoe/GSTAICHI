import React, { useState, useEffect, useContext } from "react";
import { Link } from "react-router-dom";

import { Context } from "../store/appContext";

export const Curriculum = () => {
	const { store, actions } = useContext(Context);

	return (
		<div className="container">
			<h1>Curriculum</h1>
		</div>
	);
};
