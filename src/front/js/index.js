// Import React and ReactDOM into the bundle
import React from "react";
import ReactDOM from "react-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

// Include your index.css file into the bundle
import "../styles/index.css";

// Import your Layout component
import Layout from "./layout";

// Render your React application
ReactDOM.render(<Layout />, document.querySelector("#app"));
