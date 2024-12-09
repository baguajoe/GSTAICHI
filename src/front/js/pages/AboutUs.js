import React, { useState, useContext } from "react";
import { Context } from "../store/appContext";

export const AboutUs = () => {
    const { store, actions } = useContext(Context); // Context integration
    const [activeSection, setActiveSection] = useState("introduction");

    const handleSectionChange = (section) => {
        setActiveSection(section);
    };

    return (
        <div className="container mt-4">
            <h1>About Us</h1>

            {/* Navigation Bar */}
            <nav className="nav nav-pills nav-justified mb-4">
                <button
                    className={`nav-link ${activeSection === "introduction" ? "active" : ""}`}
                    onClick={() => handleSectionChange("introduction")}
                >
                    Introduction
                </button>
                <button
                    className={`nav-link ${activeSection === "difference" ? "active" : ""}`}
                    onClick={() => handleSectionChange("difference")}
                >
                    Why We're Different
                </button>
                <button
                    className={`nav-link ${activeSection === "history" ? "active" : ""}`}
                    onClick={() => handleSectionChange("history")}
                >
                    History
                </button>
                <button
                    className={`nav-link ${activeSection === "contact" ? "active" : ""}`}
                    onClick={() => handleSectionChange("contact")}
                >
                    Contact Information
                </button>
            </nav>

            {/* Content Sections */}
            <div className="content">
                {activeSection === "introduction" && (
                    <div className="d-flex">
                        {/* Image Placeholder */}
                        <img
                            src="https://via.placeholder.com/150"
                            alt="Placeholder"
                            className="img-fluid me-3"
                            style={{ width: "150px", height: "150px" }}
                        />
                        {/* Text Content */}
                        <p>
                            The Gin Soon Tai Chi Club was founded in 1969 with permission from Grandmaster
                            Yeung Sau Chung to propagate the Yang Style Tai Chi Chuan in North America. It is the
                            oldest school teaching Tai Chi Chuan in the Greater Boston Area today.
                        </p>
                    </div>
                )}
                {activeSection === "difference" && (
                    <div className="d-flex">
                        {/* Image Placeholder */}
                        <img
                            src="https://via.placeholder.com/150"
                            alt="Placeholder"
                            className="img-fluid me-3"
                            style={{ width: "150px", height: "150px" }}
                        />
                        {/* Text Content */}
                        <p>
                        Although there are many schools of Tai Chi Chuan available in the United States, the Gin Soon Tai Chi Club is different from others because its founder Master Gin Soon Chu, is a disciple who studied with and was authorized to teach by Grandmaster Yang Sau-Chung, firstborn and heir of the legendary Yang Cheng-Fu. Master Chu received a deep and well-rounded training, first from Master Lai Hok Soon and then Grandmaster Yang Sau-Chung, a training that covered all aspects of Classical Yang Family Tai Chi Chuan.
                        </p>
                    </div>
                )}
                {activeSection === "history" && (
                    <div className="d-flex">
                        {/* Image Placeholder */}
                        <img
                            src="https://via.placeholder.com/150"
                            alt="Placeholder"
                            className="img-fluid me-3"
                            style={{ width: "150px", height: "150px" }}
                        />
                        {/* Text Content */}
                        <p>
                        Over the years, many students have graduated from the school and became instructors themselves. In 1995, the Gin Soon Tai Chi Chuan Federation was established to better serve our members who come from different countries.

All instructions at the headquarters, private and group, are taught by Master Gin Soon Chu and his son Vincent Chu, who studied from his father when he was very young.
                        </p>
                    </div>
                )}
                {activeSection === "contact" && (
                    <div className="d-flex">
                        {/* Image Placeholder */}
                        <img
                            src="https://via.placeholder.com/150"
                            alt="Placeholder"
                            className="img-fluid me-3"
                            style={{ width: "150px", height: "150px" }}
                        />
                        {/* Text Content */}
                        <p>
                            The headquarters are located at 33 Harrison Avenue, 5th floor, Boston, MA 02111. The school
                            operates Monday to Friday (4:00 PM - 8:00 PM), Monday and Thursday mornings (11:00 AM - 1:00 PM),
                            and Saturday afternoons (1:00 PM - 4:00 PM). For more information, contact Vincent Chu at
                            (617) 542-4442 or via email at chu.v@usa.com.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};
