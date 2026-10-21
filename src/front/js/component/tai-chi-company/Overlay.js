import React from "react";
import ReactDOM from "react-dom";

// Dialogs and the full-size photo viewer are drawn at the top level of the page, so they always cover the
// site's menu bar and are never clipped by the page around them. They keep the member app's look and colour.
const Overlay = ({ children }) => {
    const app = document.querySelector(".tcc-app");
    const color = app ? getComputedStyle(app).getPropertyValue("--primary-color").trim() : "";
    return ReactDOM.createPortal(
        <div className="tcc-app tcc-overlay-root" style={color ? { "--primary-color": color } : undefined}>{children}</div>,
        document.body
    );
};

export default Overlay;
