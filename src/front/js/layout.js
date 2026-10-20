import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ScrollToTop from "./component/scrollToTop";
import { BackendURL } from "./component/backendURL";

// Import your pages and components
import { Home } from "./pages/home";
import { Demo } from "./pages/demo";
import { AboutUs } from "./pages/AboutUs";
import { Classes } from "./pages/Classes";
import { ContactUs } from "./pages/ContactUs";
import { Workshops } from "./pages/Workshops";
import { Curriculum } from "./pages/Curriculum";
import { History } from "./pages/History";
import { FederationMembers } from "./pages/FederationMembers";
import { Instructors } from "./pages/Instructors";
import { Articles } from "./pages/Articles";
import { Lineage } from "./pages/Lineage";
import { ArticlesList } from "./pages/ArticlesList";
import Books from "./pages/Books";
import { Single } from "./pages/single";
import { Sidebar } from "./component/sidebar";
import { Navbar } from "./component/navbar";
import Footer from "./component/footer";
import injectContext from "./store/appContext";
import { Gallery } from "./pages/Gallery";
import TccLayout from "./component/tai-chi-company/TccLayout";
import TccLanding from "./pages/tai-chi-company/Landing";
import TccJoin from "./pages/tai-chi-company/Join";
import TccLogin from "./pages/tai-chi-company/Login";
import TccResetPassword from "./pages/tai-chi-company/ResetPassword";
import TccLibrary from "./pages/tai-chi-company/Library";
import TccWatch from "./pages/tai-chi-company/Watch";
import TccArticles from "./pages/tai-chi-company/Articles";
import TccAccount from "./pages/tai-chi-company/Account";
import TccTerms from "./pages/tai-chi-company/Terms";
import TccVincentsCorner from "./pages/tai-chi-company/VincentsCorner";
import TccAddToPhone from "./pages/tai-chi-company/AddToPhone";
import TccArticleReader from "./pages/tai-chi-company/ArticleReader";
import TccStudio from "./pages/tai-chi-company/Studio";

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
                                <Route element={<Workshops />} path="/workshops" />
                                <Route element={<History />} path="/history" />
                                <Route element={<Instructors />} path="/instructors" />
                                <Route element={<FederationMembers />} path="/federation-members" />
                                <Route element={<Lineage />} path="/lineage" />
                                <Route element={<Articles />} path="/articles" />
                                <Route element={<Articles />} path="/articles/:id" />
                                <Route element={<ArticlesList />} path="/articles-list" />
                                <Route element={<Gallery />} path="/gallery" />
                                <Route element={<Navigate to="/tai-chi-company" replace />} path="/videos" />
                                <Route element={<Books />} path="/books" />

                                {/* Tai Chi Company member app */}
                                <Route element={<TccLayout />} path="/tai-chi-company">
                                    <Route index element={<TccLanding />} />
                                    <Route element={<TccJoin />} path="join" />
                                    <Route element={<TccLogin />} path="login" />
                                    <Route element={<TccResetPassword />} path="reset-password" />
                                    <Route element={<TccLibrary />} path="library" />
                                    <Route element={<TccWatch />} path="watch/:slug" />
                                    <Route element={<TccArticles />} path="articles" />
                                    <Route element={<TccArticleReader />} path="articles/:id" />
                                    <Route element={<TccStudio />} path="studio" />
                                    <Route element={<TccAccount />} path="account" />
                                    <Route element={<TccTerms />} path="terms" />
                                    <Route element={<TccVincentsCorner />} path="vincents-corner" />
                                    <Route element={<TccAddToPhone />} path="add-to-phone" />
                                </Route>

                                <Route element={<Single />} path="/single/:theid" />
                                <Route element={<h1>Not found!</h1>} path="*" />
                            </Routes>
                        </div>
                    </div>
                    {/* Footer */}
                    <Footer />
                </ScrollToTop>
            </BrowserRouter>
        </div>
    );
};

export default injectContext(Layout);
