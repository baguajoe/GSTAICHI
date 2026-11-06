import React from "react";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { LegalPage, ContactEmail } from "../../component/tai-chi-company/legal";

const Privacy = () => {
    const { settings } = useTcc();
    const teacher = settings.teacher_name || "Vincent";
    const sections = [
        {
            heading: "What we collect",
            body: <ul className="tcc-legal-list">
                <li>Your name and email address</li>
                <li>Your password, stored securely so that nobody can read it, not even us</li>
                <li>Your plan</li>
                <li>Which videos you watch, and how far you got</li>
                <li>Questions you send {teacher}</li>
            </ul>
        },
        {
            heading: "Payments",
            body: <p>Payments are handled by PayPal. We never see or store your card number.</p>
        },
        {
            heading: "Why we use it",
            body: <ul className="tcc-legal-list">
                <li>To run your account</li>
                <li>To protect the videos{settings.video_watermark ? " (your email and member number appear in the video watermark)" : ""}</li>
                <li>To send you emails about your account and, if you choose, emails about new videos</li>
            </ul>
        },
        {
            heading: "We never sell your information",
            body: <p>We never sell or share your information, except with the services needed to run the app:
                PayPal, our hosting and our email.</p>
        },
        {
            heading: "Deleting your account",
            body: <p>You can ask us to delete your account and your information by emailing <ContactEmail />.</p>
        },
        {
            heading: "Cookies",
            body: <p>We only use what is needed to keep you signed in.</p>
        }
    ];
    return <LegalPage title="Privacy Policy" intro="What we keep about you, and why, in plain language." sections={sections} />;
};

export default Privacy;
