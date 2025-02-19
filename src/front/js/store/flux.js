const getState = ({ getStore, getActions, setStore }) => {
	return {
		store: {
			message: null,
		},

		actions: {
			submitContactForm: async (formData) => {
				try {
					const response = await fetch(process.env.BACKEND_URL + "/api/contact", {
						method: "POST",
						headers: {
							"Content-Type": "application/json",
						},
						body: JSON.stringify(formData)
					});
					
					if (!response.ok) {
						const data = await response.json();
						throw new Error(data.error || "Failed to submit form");
					}
					
					const data = await response.json();
					return { success: true, message: data.message };
				} catch (error) {
					console.error("Error submitting contact form:", error);
					return { success: false, message: error.message };
				}
			}
		}
	};
};

export default getState;
