import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTcc } from "./TccContext";
import { apiFetch, formatPrice } from "./api";
import SubscribeButton from "./SubscribeButton";

const per = (interval) => (interval === "year" ? "per year" : "per month");

// Shown in place of a paid video the viewer's plan does not include. A free member can pick a paid plan
// and pay with PayPal right here; a member who already pays changes plan on the Account page.
// title/reason/freeLine change the wording for other paid features (Ask Vincent).
const UpgradeToWatch = ({ tierRank, onUpgraded, title, reason, freeLine }) => {
    const { user, setUser, tierName } = useTcc();
    const [options, setOptions] = useState(null);
    const [chosen, setChosen] = useState(null);
    const [done, setDone] = useState(null);
    const needed = tierName(tierRank);
    const paying = user && user.is_paying_member;

    useEffect(() => {
        if (!user || paying) return;
        apiFetch("/api/tcc/plan-options")
            .then(list => setOptions(list.filter(o => (o.tier_rank || 0) >= (tierRank || 0))))
            .catch(() => setOptions([]));
    }, [user && user.id, paying, tierRank]);

    const heading = <p className="tcc-player-title">{title || "Upgrade to watch"}</p>;
    const part = <p>{reason || <>This video is part of the {needed ? `${needed} plan` : "member library"}.</>}</p>;

    if (done) {
        return <div className="tcc-upgrade" role="status"><p className="tcc-success">{done}</p></div>;
    }

    if (!user) {
        return (
            <div className="tcc-upgrade" role="note">
                {heading}
                {part}
                <p>Choose a plan to watch it, or log in if you already have one.</p>
                <div className="tcc-button-row">
                    <Link to="/tai-chi-company/join" className="custom-btn1 tcc-btn">See the plans</Link>
                    <Link to="/tai-chi-company/login" className="tcc-btn tcc-btn-outline">Log in</Link>
                </div>
            </div>
        );
    }

    if (paying) {
        return (
            <div className="tcc-upgrade" role="note">
                {heading}
                {part}
                <p>You can move up to this level on your Account page.</p>
                <Link to="/tai-chi-company/account" className="custom-btn1 tcc-btn">Change my plan</Link>
            </div>
        );
    }

    return (
        <div className="tcc-upgrade" role="note">
            {heading}
            {part}
            <p>{freeLine || "You are on the Free plan. Choose a plan below to watch it."} You can cancel any time.</p>
            {options === null ? <p>Loading the plans…</p> : options.length === 0 ? (
                <Link to="/tai-chi-company/account" className="custom-btn1 tcc-btn">See the plans</Link>
            ) : (
                <div className="tcc-plan-options">
                    {options.map(o => (
                        <button key={o.id} type="button" aria-pressed={!!chosen && chosen.id === o.id}
                            className={`tcc-btn tcc-btn-outline tcc-plan-option${chosen && chosen.id === o.id ? " active" : ""}`}
                            onClick={() => setChosen(o)}>
                            {o.tier_name}: {formatPrice(o.price)} {per(o.interval)}
                        </button>
                    ))}
                </div>
            )}
            {chosen && (
                <div className="tcc-section">
                    <p>You chose <strong>{chosen.tier_name}</strong> at {formatPrice(chosen.price)} {per(chosen.interval)}.</p>
                    <SubscribeButton plan={chosen} user={user} onSubscribed={(result) => {
                        setUser(result.user);
                        setDone(result.msg);
                        if (onUpgraded) onUpgraded();
                    }} />
                </div>
            )}
        </div>
    );
};

export default UpgradeToWatch;
