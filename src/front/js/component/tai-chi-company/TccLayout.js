import React from "react";
import { NavLink, Outlet, Link } from "react-router-dom";
import { TccProvider, useTcc } from "./TccContext";
import { useHomeScreenApp } from "./homeScreenApp";
import "../../../styles/taiChiCompany.css";

const navItems = (settings, user) => [
    { to: "/tai-chi-company", label: "Home", end: true },
    { to: "/tai-chi-company/library", label: "Library" },
    { to: "/tai-chi-company/vincents-corner", label: settings.corner_name || "Corner" },
    { to: "/tai-chi-company/articles", label: "Articles" },
    { to: "/tai-chi-company/account", label: "Account" },
    ...(user && (user.role === "teacher" || user.role === "admin")
        ? [{ to: "/tai-chi-company/studio", label: "Studio" }]
        : [])
];

const navClass = ({ isActive }) => `tcc-nav-link${isActive ? " active" : ""}`;

const TccNav = () => {
    const { settings, user, userLoaded } = useTcc();
    return (
        <header className="tcc-header">
            <Link to="/tai-chi-company" className="tcc-brand">
                {settings.logo_url && <img src={settings.logo_url} alt="" className="tcc-brand-logo" />}
                <span>{settings.app_name}</span>
            </Link>
            <nav className="tcc-nav" aria-label={`${settings.app_name} menu`}>
                {navItems(settings, user).map(item => (
                    <NavLink key={item.to} to={item.to} end={item.end} className={navClass}>
                        {item.label}
                    </NavLink>
                ))}
                {userLoaded && !user && (
                    <>
                        <NavLink to="/tai-chi-company/login" className={navClass}>Log In</NavLink>
                        <NavLink to="/tai-chi-company/join" className={({ isActive }) => `tcc-nav-link tcc-nav-signup${isActive ? " active" : ""}`}>
                            Sign Up
                        </NavLink>
                    </>
                )}
            </nav>
        </header>
    );
};

const TccFooter = () => {
    const { settings } = useTcc();
    const phoneHref = (settings.contact_phone || "").replace(/[^\d+]/g, "");
    return (
        <footer className="tcc-footer">
            {settings.contact_phone && (
                <p className="tcc-help-line">
                    Need help? Call <a href={`tel:${phoneHref}`}>{settings.contact_phone}</a>
                </p>
            )}
            <p className="tcc-copyright">
                &copy; {new Date().getFullYear()} {settings.copyright_line || settings.school_name}
            </p>
            <p className="tcc-footer-links">
                <Link to="/tai-chi-company/add-to-phone">Add this app to your phone</Link>
                <span aria-hidden="true"> · </span>
                <Link to="/tai-chi-company/terms">Terms of Use</Link>
            </p>
        </footer>
    );
};

const TccShell = () => {
    const { settings, loadError, loadSite } = useTcc();
    useHomeScreenApp(settings);

    if (loadError) {
        return (
            <div className="tcc-app">
                <div className="tcc-page tcc-center">
                    <p className="tcc-error" role="alert">{loadError}</p>
                    <button type="button" className="custom-btn1 tcc-btn" onClick={loadSite}>Try again</button>
                </div>
            </div>
        );
    }
    if (!settings) {
        return <div className="tcc-app"><p className="tcc-page tcc-center">Loading…</p></div>;
    }

    return (
        <div className="tcc-app" style={{ "--primary-color": settings.primary_color }}>
            <TccNav />
            <main className="tcc-main">
                <Outlet />
            </main>
            <TccFooter />
        </div>
    );
};

const TccLayout = () => (
    <TccProvider>
        <TccShell />
    </TccProvider>
);

export default TccLayout;
