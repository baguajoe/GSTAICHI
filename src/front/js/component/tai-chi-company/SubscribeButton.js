import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js";
import { FormMessage } from "./FormField";
import { HELP_EMAIL, useTcc } from "./TccContext";

// While subscriptions are tested in sandbox mode they use the sandbox app; the shop keeps the live PAYPAL_CLIENT_ID
const PAYPAL_CLIENT_ID = (process.env.PAYPAL_MODE || "sandbox").toLowerCase() !== "live" && process.env.PAYPAL_SANDBOX_CLIENT_ID
    ? process.env.PAYPAL_SANDBOX_CLIENT_ID
    : process.env.PAYPAL_CLIENT_ID;

// True while a PayPal payment is being confirmed (or needs attention): show <ActivationNotice /> instead of the plans
export const useActivationShowing = () => {
    const { activation } = useTcc();
    return !!activation && activation.state !== "done";
};

// Runs onDone(result) once the server has confirmed the plan (result has msg, user and subscription)
export const useActivationDone = (onDone) => {
    const { activation, clearActivation } = useTcc();
    useEffect(() => {
        if (activation && activation.state === "done") {
            onDone(activation.result);
            clearActivation();
        }
    }, [activation]);
};

// Shown instead of the plan picker from PayPal's approval until the server has confirmed the plan.
// Returns null when there is nothing to show (no payment waiting, or already confirmed).
export const ActivationNotice = () => {
    const { activation, clearActivation } = useTcc();
    if (!activation || activation.state === "done") return null;
    if (activation.state === "failed") {
        return (
            <div className="tcc-notice" role="alert">
                <FormMessage error={activation.message} />
                <p>If PayPal took a payment, email <a href={`mailto:${HELP_EMAIL}`}>{HELP_EMAIL}</a> and we will sort it out.</p>
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={clearActivation}>Back to the plans</button>
            </div>
        );
    }
    return (
        <div className="tcc-notice" role="status" aria-live="polite">
            <p className="tcc-success"><strong>Payment received — activating your account</strong></p>
            {activation.state === "slow" ? (
                <p>PayPal is taking longer than usual. Your payment is safe and your plan will appear on its own: refresh
                    this page in a few minutes, or sign in again later. If it is not there within an hour, email{" "}
                    <a href={`mailto:${HELP_EMAIL}`}>{HELP_EMAIL}</a>. Please do not pay again.</p>
            ) : (
                <p>This usually takes a few seconds, but can take a few minutes. You can keep this page open. Please do not pay again.</p>
            )}
        </div>
    );
};

// PayPal subscribe button for one plan. Only for signed-in members: the subscription is tied to their account.
// When PayPal approves, the shared activation (TccContext) confirms it with the server, retrying as needed.
const SubscribeButton = ({ plan }) => {
    const { user, startActivation } = useTcc();
    const [error, setError] = useState(null);

    if (!user) {
        return (
            <p className="tcc-notice">
                Please <Link to="/tai-chi-company/login">log in</Link> or <Link to="/tai-chi-company/join">create an account</Link> to subscribe.
            </p>
        );
    }
    if (!PAYPAL_CLIENT_ID || !plan.paypal_plan_id) {
        return <p className="tcc-notice">Online payment is being set up. Please check back soon, or email <a href={`mailto:${HELP_EMAIL}`}>{HELP_EMAIL}</a> to join.</p>;
    }

    return (
        <div className="tcc-paypal">
            <PayPalScriptProvider options={{ clientId: PAYPAL_CLIENT_ID, vault: true, intent: "subscription", currency: "USD" }}>
                <PayPalButtons
                    style={{ layout: "vertical", label: "subscribe", height: 50 }}
                    forceReRender={[plan.paypal_plan_id, user.id]}
                    createSubscription={(_data, actions) => actions.subscription.create({
                        plan_id: plan.paypal_plan_id,
                        custom_id: String(user.id)
                    })}
                    onApprove={async (data) => {
                        setError(null);
                        startActivation(data.subscriptionID, user.id);
                    }}
                    onError={() => setError(`PayPal could not start the payment. Please try again, or email ${HELP_EMAIL} for help.`)}
                />
            </PayPalScriptProvider>
            <p className="tcc-field-hint">By subscribing you agree to the <Link to="/tai-chi-company/terms">Terms of Use</Link>.</p>
            <FormMessage error={error} />
        </div>
    );
};

export default SubscribeButton;
