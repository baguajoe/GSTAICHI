import React from "react";
import { Link } from "react-router-dom";
import { HELP_EMAIL } from "./TccContext";

// Health disclaimer, legal page links and the shared layout of the Terms, Privacy, Refunds and Health pages.

export const HEALTH_DISCLAIMER = [
    "Tai Chi and Qigong are gentle exercise, but any physical activity carries some risk.",
    "Talk to your doctor before starting, especially if you have a health condition, are pregnant, or have had recent surgery or injury.",
    "Practice at your own pace, stop if you feel pain, dizziness or shortness of breath, and use a clear, safe space.",
    "The lessons are for education and are not medical advice. You practice at your own risk."
];

export const LEGAL_PAGES = [
    { to: "/tai-chi-company/terms", label: "Terms" },
    { to: "/tai-chi-company/privacy", label: "Privacy" },
    { to: "/tai-chi-company/refunds", label: "Refunds" },
    { to: "/tai-chi-company/health", label: "Health disclaimer" }
];

export const isLegalPage = (pathname) => LEGAL_PAGES.some(p => pathname.replace(/\/+$/, "") === p.to);

// "Terms · Privacy · Refunds · Health disclaimer"
export const LegalLinks = ({ className = "" }) => (
    <p className={`tcc-legal-links ${className}`}>
        {LEGAL_PAGES.map((p, i) => (
            <React.Fragment key={p.to}>
                {i > 0 && <span aria-hidden="true"> · </span>}
                <Link to={p.to}>{p.label}</Link>
            </React.Fragment>
        ))}
    </p>
);

export const HealthDisclaimerText = () => (
    <div className="tcc-health-text">
        {HEALTH_DISCLAIMER.map((line, i) => <p key={i}>{line}</p>)}
    </div>
);

// Under the video player
export const PracticeNote = () => (
    <p className="tcc-practice-note">
        Practice at your own pace. Talk to your doctor before starting.{" "}
        <Link to="/tai-chi-company/health">Read the health disclaimer</Link>
    </p>
);

export const ContactEmail = () => <a href={`mailto:${HELP_EMAIL}`}>{HELP_EMAIL}</a>;

// Large-text page with short sections. sections: [{ heading, body }]
export const LegalPage = ({ title, intro, sections }) => (
    <div className="tcc-page tcc-narrow tcc-legal">
        <h1>{title}</h1>
        {intro && <p className="tcc-lead">{intro}</p>}
        {sections.map(s => (
            <section key={s.heading} className="tcc-legal-section">
                <h2>{s.heading}</h2>
                {s.body}
            </section>
        ))}
        <LegalLinks className="tcc-legal-bottom" />
    </div>
);
