import React from "react";
import { Link } from "react-router-dom";

export const Navbar = () => {
	return (
		<nav className="navbar navbar-light bg-light">
			<div className="container-fluid">
				<div className="row">
					<Link to="/">
						<span className="navbar-brand mb-0 h1">React Boilerplate</span>
					</Link>
				</div>

				<div className="row mt-3">
					<div className="col-12">
						<Link to="/about-us">
							<button className="btn btn-primary w-100">About Us</button>
						</Link>
					</div>
				</div>
				<div className="row mt-2">
					<div className="col-12">
						<Link to="/classes">
							<button className="btn btn-primary w-100">Classes</button>
						</Link>
					</div>
				</div>
				<div className="row mt-2">
					<div className="col-12">
						<Link to="/curriculum">
							<button className="btn btn-primary w-100">Curriculum</button>
						</Link>
					</div>
				</div>
				<div className="row mt-2">
					<div className="col-12">
						<Link to="/events">
							<button className="btn btn-primary w-100">Events</button>
						</Link>
					</div>
				</div>
				<div className="row mt-2">
					<div className="col-12">
						<Link to="/contact-us">
							<button className="btn btn-primary w-100">Contact Us</button>
						</Link>
					</div>
				</div>
			</div>
		</nav>
	);
};
