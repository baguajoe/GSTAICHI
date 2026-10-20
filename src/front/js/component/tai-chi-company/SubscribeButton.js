import React, { useState } from "react";
import { Link } from "react-router-dom";
import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js";
import { apiFetch } from "./api";
import { FormMessage } from "./FormField";

const PAYPAL_CLIENT_ID = process.env.PAYPAL_CLIENT_ID;
const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// After PayPal approval the server checks the subscription with PayPal itself before giving access.
// PayPal can take a few seconds to activate it, so ask a few times.
const confirmWithServer = async (subscriptionId) => {
    for (let attempt = 0; attempt < 6; attempt++) {
        const result = await apiFetch("/api/tcc/subscription/confirm", { method: "POST", body: { subscription_id: subscriptionId } });
        if (!result.pending) return result;
        await wait(3000);
    }
    throw new Error("PayPal is still finishing your payment. Please refresh this page in a minute; your plan will appear here.");
};

// PayPal subscribe button for one plan. onSubscribed(result) runs once the server has confirmed it.
const SubscribeButton = ({ plan, user, onSubscribed }) => {
    const [error, setError] = useState(null);
    const [busy, setBusy] = useState(false);

    if (!PAYPAL_CLIENT_ID || !plan.paypal_plan_id) {
        return <p className="tcc-notice">Online payment is being set up. Please check back soon, or call us to join.</p>;
    }
    if (busy) return <p className="tcc-success" role="status">Thank you! Confirming your payment with PayPal…</p>;

    return (
        <div className="tcc-paypal">
            <PayPalScriptProvider options={{ clientId: PAYPAL_CLIENT_ID, vault: true, intent: "subscription", currency: "USD" }}>
                <PayPalButtons
                    style={{ layout: "vertical", label: "subscribe", height: 50 }}
                    forceReRender={[plan.paypal_plan_id]}
                    createSubscription={(_data, actions) => actions.subscription.create({
                        plan_id: plan.paypal_plan_id,
                        custom_id: String(user.id)
                    })}
                    onApprove={async (data) => {
                        setError(null);
                        setBusy(true);
                        try {
                            onSubscribed(await confirmWithServer(data.subscriptionID));
                        } catch (e) {
                            setError(e.message);
                            setBusy(false);
                        }
                    }}
                    onError={() => setError("PayPal could not start the payment. Please try again, or call us for help.")}
                />
            </PayPalScriptProvider>
            <p className="tcc-field-hint">By subscribing you agree to the <Link to="/tai-chi-company/terms">Terms of Use</Link>.</p>
            <FormMessage error={error} />
        </div>
    );
};

export default SubscribeButton;
