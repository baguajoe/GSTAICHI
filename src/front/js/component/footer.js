import React from 'react';
import { Link } from "react-router-dom";
import gsTaiChi from "../../img/gstaichi_sm.gif";

const Footer = () => {
	const footerStyle = {
		backgroundColor: '#590d0d',
		color: 'white'
	};

	return (
		<footer style={footerStyle} className="py-5">
			<div className="container">
				<div className="row">
					{/* Contact Information */}
					<div className="col-md-4 mb-4 mb-md-0">
						<h3 className="h5 mb-4">Contact Us</h3>
						<div className="mb-2">
							<i className="fas fa-map-marker-alt me-2"></i>
							<span>123 Martial Arts Way, Suite 100</span>
						</div>
						<div className="mb-2">
							<i className="fas fa-phone me-2"></i>
							<span>(555) 123-4567</span>
						</div>
						<div className="mb-2">
							<i className="fas fa-envelope me-2"></i>
							<span>info@ginsoon.org</span>
						</div>
					</div>

					{/* Center Logo and Hours */}
					<div className="col-md-4 mb-4 mb-md-0 d-flex justify-content-center align-items-center">
						<div className="mb-4">
							<img
								src={gsTaiChi}
								alt="Tai Chi Practitioner"
								className="img-fluid"
								style={{ maxWidth: '175px', borderRadius: '8px' }}
							/>
						</div>

					</div>

					{/* Quick Links */}
					<div className="col-md-4">
						<h3 className="h5 mb-4 text-end">Quick Links</h3>
						<ul className="list-unstyled">
							<li className="mb-2 text-end">
								<Link to="/about-us" className="text-white text-decoration-none hover-opacity">
									<i className="fas fa-chevron-right me-2"></i>About Us
								</Link>
							</li>
							<li className="mb-2 text-end">
								<Link to="/classes" className="text-white text-decoration-none hover-opacity">
									<i className="fas fa-chevron-right me-2"></i>Class Schedule
								</Link>
							</li>
							<li className="mb-2 text-end">
								<Link to="/videos" className="text-white text-decoration-none hover-opacity">
									<i className="fas fa-chevron-right me-2"></i>Videos
								</Link>
							</li>
						</ul>
					</div>
				</div>

				{/* Copyright */}
				<div className="row mt-3 pt-3 border-top border-light">
					<div className="col-12 text-center">
						{/* <p className="mb-0">&copy; {new Date().getFullYear()} Gin Soon Tai Chi Chuan Federation. All rights reserved.</p> */}
						<p className="mb-0">&copy; 1969 Gin Soon Tai Chi Chuan Federation. All rights reserved.</p>
					</div>
				</div>
			</div>
		</footer>
	);
};

export default Footer;

