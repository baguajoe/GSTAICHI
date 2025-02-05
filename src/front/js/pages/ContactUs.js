import React, { useState, useContext } from "react";
import { Context } from "../store/appContext";


export const ContactUs = () => {
	const { store, actions } = useContext(Context);

	// Form state
	const [formData, setFormData] = useState({
		name: "",
		email: "",
		message: "",
	});

	const [submitted, setSubmitted] = useState(false);

	// Handle form field changes
	const handleChange = (e) => {
		setFormData({ ...formData, [e.target.name]: e.target.value });
	};

	// Handle form submission
	const handleSubmit = async (e) => {
		e.preventDefault();

		const result = await actions.submitContactForm(formData);

		if (result.success) {
			setSubmitted(true);
			setFormData({ name: "", email: "", message: "" });
		} else {
			// Handle error - you might want to add error state to display this
			alert("Failed to send message: " + result.message);
		}
	};

	return (
		<div className="container my-4">
			<h1 className="text-center mb-4">Contact Us</h1>

			{/* Contact Details */}
			<div className="mb-4">
				<p>
					<strong>Address:</strong> 33 Harrison Avenue, 5th Floor, Boston, MA
					02111
				</p>
				<p>
					<strong>Tel:</strong> <a href="tel:+16175424442">(617) 542-4442</a>
				</p>
				<p>
					<strong>Email:</strong>{" "}
					<a href="mailto:chu.v@usa.com">chu.v@usa.com</a>
				</p>
			</div>

			{/* Contact Form */}
			<div className="card shadow">
				<div className="card-body">
					<h2 className="card-title mb-4">Send Us a Message</h2>
					{submitted && (
						<div className="alert alert-success" role="alert">
							Thank you for your message! We will get back to you soon.
						</div>
					)}
					<form onSubmit={handleSubmit}>
						<div className="mb-3">
							<label htmlFor="name" className="form-label">
								Name
							</label>
							<input
								type="text"
								className="form-control"
								id="name"
								name="name"
								value={formData.name}
								onChange={handleChange}
								required
							/>
						</div>
						<div className="mb-3">
							<label htmlFor="email" className="form-label">
								Email
							</label>
							<input
								type="email"
								className="form-control"
								id="email"
								name="email"
								value={formData.email}
								onChange={handleChange}
								required
							/>
						</div>
						<div className="mb-3">
							<label htmlFor="message" className="form-label">
								Message
							</label>
							<textarea
								className="form-control"
								id="message"
								name="message"
								rows="5"
								value={formData.message}
								onChange={handleChange}
								required
							></textarea>
						</div>
						<button type="submit" className="btn btn-primary">
							Send Message
						</button>
					</form>
				</div>
			</div>
		</div>
	);
};
