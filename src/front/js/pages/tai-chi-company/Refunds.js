import React from "react";
import { Link } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { LegalPage, ContactEmail } from "../../component/tai-chi-company/legal";

// The number of days comes from Site Settings (Refund days) in /admin.
const Refunds = () => {
    const { settings } = useTcc();
    const days = settings.refund_days ?? 7;
    const sections = [
        {
            heading: `Full refund within ${days} days`,
            body: <p>If you're not happy, email <ContactEmail /> within {days} days of your first payment for a full refund.</p>
        },
        {
            heading: "After that",
            body: <>
                <p>After that, payments are not refunded.</p>
                <p>You can cancel any time on your <Link to="/tai-chi-company/account">Account page</Link> and keep
                    access until the end of the period you paid for.</p>
            </>
        }
    ];
    return <LegalPage title="Refund Policy" sections={sections} />;
};

export default Refunds;
