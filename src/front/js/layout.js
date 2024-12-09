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
import { History } from "./pages/History"; // Import History component
import injectContext from "./store/appContext";
import { FederalMembers } from "./pages/FederalMembers";
import { Instructors } from "./pages/Instructors";
import { Articles } from "./pages/Articles"; // Ensure this matches your import path
import { Lineage } from "./pages/Lineage";
import { ArticlesList } from "./pages/ArticlesList"; // Add this import

// Create your first component
const Layout = () => {
    const basename = process.env.BASENAME || "";

    if (!process.env.BACKEND_URL || process.env.BACKEND_URL === "") return <BackendURL />;

    return (
        <div>
            <BrowserRouter basename={basename}>
                <ScrollToTop>
                    <Navbar />
                    <div className="d-flex">
                        <Sidebar />
                        <div className="flex-grow-1 p-3">
                            <Routes>
                                <Route element={<Home />} path="/" />
                                <Route element={<Demo />} path="/demo" />
                                <Route element={<AboutUs />} path="/about-us" />
                                <Route element={<Classes />} path="/classes" />
                                <Route element={<ContactUs />} path="/contact-us" />
                                <Route element={<Curriculum />} path="/curriculum" />
                                <Route element={<Events />} path="/events" />
                                <Route element={<History />} path="/history" />
                                <Route element={<FederalMembers />} path="/federal-members" />
                                <Route element={<Lineage />} path="/lineage" />
                                <Route element={<Instructors />} path="/instructors" />
                                <Route element={<Articles />} path="/articles" /> {/* Dropdown and default content */}
                                <Route element={<Articles />} path="/articles/:id" /> {/* Single article view */}
                                <Route element={<ArticlesList />} path="/articles/list" /> {/* List of articles */}
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
