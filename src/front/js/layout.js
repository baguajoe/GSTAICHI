import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import ScrollToTop from "./component/scrollToTop";
import { BackendURL } from "./component/backendURL";

import { Home } from "./pages/home";
import { Demo } from "./pages/demo";
import { AboutUs } from "./pages/AboutUs";
import { Classes } from "./pages/Classes";
import { ContactUs } from "./pages/ContactUs";
import { Events } from "./pages/Events";
import { Single } from "./pages/single";
import { Sidebar } from "./component/sidebar";
import { Navbar } from "./component/navbar";
import { Footer } from "./component/footer";
import { Curriculum } from "./pages/Curriculum";
import injectContext from "./store/appContext";

// Create your first component
const Layout = () => {
    // The basename is used when your project is published in a subdirectory and not in the root of the domain
    const basename = process.env.BASENAME || "";

    // Check if BACKEND_URL is configured
    if (!process.env.BACKEND_URL || process.env.BACKEND_URL === "") return <BackendURL />;

    return (
        <div>
            <BrowserRouter basename={basename}>
                <ScrollToTop>
                    <Navbar />
                    <div className="d-flex">
                        {/* Sidebar */}
                        <Sidebar />

                        {/* Main Content */}
                        <div className="flex-grow-1 p-3">
                            <Routes>
                                <Route element={<Home />} path="/" />
                                <Route element={<Demo />} path="/demo" />
                                <Route element={<AboutUs />} path="/about-us" />
                                <Route element={<Classes />} path="/classes" />
                                <Route element={<ContactUs />} path="/contact-us" />
                                <Route element={<Curriculum />} path="/curriculum" />
                                <Route element={<Events />} path="/events" />
                                <Route element={<Single />} path="/single/:theid" />
                                <Route element={<h1>Not found!</h1>} />
                            </Routes>
                        </div>
                    </div>
                    <Footer />
                </ScrollToTop>
            </BrowserRouter>
        </div>
    );
};

export default injectContext(Layout);
