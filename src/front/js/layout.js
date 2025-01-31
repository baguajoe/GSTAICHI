import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import ScrollToTop from "./component/scrollToTop";
import { BackendURL } from "./component/backendURL";

// Import your pages and components
import { Home } from "./pages/home";
import { Demo } from "./pages/demo";
import { AboutUs } from "./pages/AboutUs";
import { Classes } from "./pages/Classes";
import { ContactUs } from "./pages/ContactUs";
import { Events } from "./pages/Events";
import { Curriculum } from "./pages/Curriculum";
import { History } from "./pages/History";
import { FederalMembers } from "./pages/FederalMembers";
import { Instructors } from "./pages/Instructors";
import { Articles } from "./pages/Articles";
import { Lineage } from "./pages/Lineage";
import { ArticlesList } from "./pages/ArticlesList";
import VideoManagementPage from "./pages/VideoManagementPage";
import Video from "./pages/Video";
import VideoStreaming from "./pages/VideoStreaming";
import { Books } from "./pages/Books";
import { Single } from "./pages/single";
import { Sidebar } from "./component/sidebar";
import { Navbar } from "./component/navbar";
// import { Footer } from "./component/footer";
import injectContext from "./store/appContext";
import { Gallery } from "./pages/Gallery";

// Create your Layout component
const Layout = () => {
    const basename = process.env.BASENAME || "";

    if (!process.env.BACKEND_URL || process.env.BACKEND_URL === "") return <BackendURL />;

    return (
        <div>
            <BrowserRouter basename={basename}>
                <ScrollToTop>
                    <Navbar />
                    <div className="d-flex">
                        {/* Sidebar for navigation */}
                        <Sidebar />

                        {/* Main content area */}
                        <div className="flex-grow-1 p-3">
                            <Routes>
                                {/* Routes for different pages */}
                                <Route element={<Home />} path="/" />
                                <Route element={<Demo />} path="/demo" />
                                <Route element={<AboutUs />} path="/about-us" />
                                <Route element={<Classes />} path="/classes" />
                                <Route element={<ContactUs />} path="/contact-us" />
                                <Route element={<Curriculum />} path="/curriculum" />
                                <Route element={<Events />} path="/events" />
                                <Route element={<History />} path="/history" />
                                <Route element={<Instructors />} path="/instructors" />
                                <Route element={<FederalMembers />} path="/federal-members" />
                                <Route element={<Lineage />} path="/lineage" />
                                <Route element={<Articles />} path="/articles" />
                                <Route element={<Articles />} path="/articles/:id" />
                                <Route element={<ArticlesList />} path="/articles-list" />
                                <Route element={<Gallery />} path="/gallery" />
                                <Route element={<VideoManagementPage />} path="/videos" />
                                <Route element={<Video />} path="/video" />
                                <Route element={<VideoStreaming />} path="/video-streaming/:videoId/:userId" />
                                <Route element={<Books />} path="/books" />

                                <Route element={<Single />} path="/single/:theid" />
                                <Route element={<h1>Not found!</h1>} path="*" />
                            </Routes>
                        </div>
                    </div>
                    {/* Footer */}
                    {/* <Footer /> */}
                </ScrollToTop>
            </BrowserRouter>
        </div>
    );
};

export default injectContext(Layout);
