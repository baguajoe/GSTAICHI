import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useTcc } from "./TccContext";
import { apiFetch, formatPrice } from "./api";
import { FormMessage } from "./FormField";
import SubscribeButton from "./SubscribeButton";

const longDate = (iso) => iso
    ? new Date(iso).toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" })
    : null;
const per = (interval) => (interval === "year" ? "per year" : "per month");

// The plan part of the Account page: current plan, next payment, change plan, cancel, or subscribe.
const MyPlan = () => {
    const { user, setUser, refreshUser } = useTcc();
    const location = useLocation();
    const navigate = useNavigate();
    const [sub, setSub] = useState(null);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [busy, setBusy] = useState(false);
    const [confirmCancel, setConfirmCancel] = useState(false);
    const [chosenPlan, setChosenPlan] = useState(null);

    useEffect(() => {
        const changed = new URLSearchParams(location.search).get("plan_changed");
        const load = changed
            ? apiFetch("/api/tcc/subscription/sync", { method: "POST" }).then((data) => {
                setSuccess("Thank you. Your plan change has been saved.");
                navigate("/tai-chi-company/account", { replace: true });
                refreshUser();
                return data;
            })
            : apiFetch("/api/tcc/subscription");
        load.then(setSub).catch(e => setError(e.message));
    }, []);

    if (!sub) return <section className="tcc-section"><h2>Your plan</h2>{error ? <FormMessage error={error} /> : <p>Loading…</p>}</section>;

    const staff = user.role === "admin" || user.role === "teacher";
    const plan = sub.plan;
    const paid = sub.has_access && sub.tier_rank > 0;

    const changePlan = async (option) => {
        setError(null);
        setBusy(true);
        try {
            const result = await apiFetch("/api/tcc/subscription/change", { method: "POST", body: { plan_id: option.id } });
            if (result.approve_url) {
                window.location.href = result.approve_url; // PayPal asks the member to approve the new price
                return;
            }
            setSub(result.subscription);
            setSuccess(result.msg);
            refreshUser();
        } catch (e) {
            setError(e.message);
        }
        setBusy(false);
    };

    const cancelPlan = async () => {
        setError(null);
        setBusy(true);
        try {
            const result = await apiFetch("/api/tcc/subscription/cancel", { method: "POST", body: {} });
            setSub(result.subscription);
            setSuccess(result.msg);
            setConfirmCancel(false);
            refreshUser();
        } catch (e) {
            setError(e.message);
        }
        setBusy(false);
    };

    const otherOptions = sub.options.filter(o => !plan || o.id !== plan.id);
    const subscribeOptions = (
        <div className="tcc-plan-options">
            {sub.options.map(o => (
                <button key={o.id} type="button" aria-pressed={chosenPlan && chosenPlan.id === o.id}
                    className={`tcc-btn tcc-btn-outline tcc-plan-option${chosenPlan && chosenPlan.id === o.id ? " active" : ""}`}
                    onClick={() => setChosenPlan(o)}>
                    {o.tier_name}: {formatPrice(o.price)} {per(o.interval)}
                </button>
            ))}
            {chosenPlan && (
                <div className="tcc-section">
                    <p>You chose <strong>{chosenPlan.tier_name}</strong> at {formatPrice(chosenPlan.price)} {per(chosenPlan.interval)}.</p>
                    <SubscribeButton plan={chosenPlan} user={user} onSubscribed={(result) => {
                        setUser(result.user);
                        setSub(result.subscription);
                        setSuccess(result.msg);
                        setChosenPlan(null);
                    }} />
                </div>
            )}
        </div>
    );

    return (
        <section className="tcc-section tcc-myplan">
            <h2>Your plan</h2>
            <FormMessage error={error} success={success} />

            {staff ? (
                <p>You have full access as {user.role === "admin" ? "an administrator" : "a teacher"}.</p>
            ) : paid && plan ? (
                <>
                    <p className="tcc-plan-line">
                        <strong>{plan.tier_name}</strong>, {formatPrice(plan.price)} {per(plan.interval)}
                        {sub.is_founding_member && <span className="tcc-badge tcc-badge-founding">Founding member</span>}
                    </p>
                    {sub.is_founding_member && <p>As a founding member you keep your price for life.</p>}
                    {sub.status === "active" && sub.next_billing_at && <p>Next payment: <strong>{longDate(sub.next_billing_at)}</strong></p>}
                    {sub.status === "cancelled" && (
                        <p className="tcc-notice">Your plan is cancelled. You can keep watching until <strong>{longDate(sub.paid_through)}</strong>.</p>
                    )}
                    {sub.status === "past_due" && (
                        <p className="tcc-notice">There was a problem with your last payment. PayPal will try again.
                            Please check the card in your PayPal account. You can keep watching for now.</p>
                    )}
                    {!sub.managed_by_paypal && <p>Your plan was set up by the school. Please call us to make changes.</p>}
                </>
            ) : sub.granted ? null : (
                <p>You have a <strong>free account</strong>. You can watch the free sample video.</p>
            )}

            {!staff && sub.granted && (
                <p className="tcc-notice">
                    The school has given you access to the <strong>{sub.granted.tier_name}</strong> level
                    {sub.granted.until ? <> until <strong>{longDate(sub.granted.until)}</strong></> : null}.
                </p>
            )}

            {!staff && sub.managed_by_paypal && sub.status === "active" && (
                <>
                    <h3>Change your plan</h3>
                    <p>Moving up gives you more videos right away. PayPal will ask you to approve the new price.</p>
                    <div className="tcc-plan-options">
                        {otherOptions.map(o => (
                            <button key={o.id} type="button" className="tcc-btn tcc-btn-outline tcc-plan-option"
                                disabled={busy || !o.paypal_plan_id} onClick={() => changePlan(o)}>
                                Switch to {o.tier_name}: {formatPrice(o.price)} {per(o.interval)}
                            </button>
                        ))}
                    </div>

                    <h3>Cancel your plan</h3>
                    {!confirmCancel ? (
                        <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => setConfirmCancel(true)}>Cancel my plan</button>
                    ) : (
                        <div className="tcc-notice">
                            <p>Are you sure? You will not be charged again. You can keep watching until
                                {" "}<strong>{longDate(sub.next_billing_at || sub.paid_through) || "the end of the period you paid for"}</strong>.</p>
                            <div className="tcc-button-row">
                                <button type="button" className="custom-btn1 tcc-btn" disabled={busy} onClick={cancelPlan}>Yes, cancel my plan</button>
                                <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => setConfirmCancel(false)}>No, keep my plan</button>
                            </div>
                        </div>
                    )}
                </>
            )}

            {!staff && (!paid || sub.status === "cancelled" || sub.status === "expired") && sub.options.length > 0 && (
                <>
                    <h3>{paid ? "Start a new plan" : "Choose a plan"}</h3>
                    {subscribeOptions}
                </>
            )}
        </section>
    );
};

export default MyPlan;
