import React from "react";
import { Link } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { LegalPage, ContactEmail } from "../../component/tai-chi-company/legal";

const Terms = () => {
    const { settings } = useTcc();
    const school = settings.school_name || "Gin Soon Tai Chi Chuan Federation";
    const address = settings.address || "33 Harrison Avenue, 5th Floor, Boston, MA 02111";
    const days = settings.refund_days ?? 7;

    const sections = [
        {
            heading: "Who we are",
            body: <>
                <p>{settings.app_name} is run by {school}, {address}.</p>
                <p>Questions about these terms? Email <ContactEmail />.</p>
            </>
        },
        {
            heading: "Subscriptions",
            body: <>
                <p>Paid plans are monthly or yearly. You pay through PayPal, and your plan renews automatically until you cancel.</p>
                <p>You can cancel any time, on your <Link to="/tai-chi-company/account">Account page</Link> or in your PayPal account.
                    After you cancel, you keep access until the end of the period you paid for.</p>
                <p>See the <Link to="/tai-chi-company/refunds">Refund Policy</Link>: a full refund if you ask within {days} days of your first payment.</p>
            </>
        },
        {
            heading: "The Free plan",
            body: <p>The Free plan lets you watch the free sample videos and read all the articles. No payment is needed.</p>
        },
        {
            heading: "For your personal use only",
            body: <>
                <p>The videos and articles are for your own practice.</p>
                <p>Please do not download, record, copy or post them anywhere else, and do not share your account with anyone.</p>
                <p>{settings.video_watermark
                    ? "Videos are watermarked with your email and member number."
                    : "Videos are protected, and we can see which account is watching them."}{" "}
                    We may close accounts that break this rule, without a refund.</p>
                <p>All videos, articles and pictures are protected by copyright and belong to {school}.</p>
            </>
        },
        {
            heading: "Your health",
            body: <p>Please read the <Link to="/tai-chi-company/health">health disclaimer</Link> before you practice.
                The lessons are for education and are not medical advice. You practice at your own risk.</p>
        },
        {
            heading: "Changes",
            body: <>
                <p>Prices and lessons may change over time.</p>
                <p>If the price of your plan goes up, we will email you before the change.
                    Founding members keep their price for life.</p>
            </>
        },
        {
            heading: "The law",
            body: <p>These terms are governed by the laws of the Commonwealth of Massachusetts.</p>
        }
    ];

    return <LegalPage title="Terms of Use" intro="The rules for using the app, in plain language." sections={sections} />;
};

export default Terms;
