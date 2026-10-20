import React from "react";
import { useTcc } from "./TccContext";
import { formatPrice } from "./api";

const INTERVALS = [
    { key: "month", label: "Monthly", per: "per month" },
    { key: "year", label: "Annual", per: "per year" }
];

export const IntervalToggle = ({ interval, onChange }) => (
    <div className="tcc-toggle" role="group" aria-label="Choose how often to pay">
        {INTERVALS.map(i => (
            <button
                key={i.key}
                type="button"
                className={`tcc-toggle-btn${interval === i.key ? " active" : ""}`}
                aria-pressed={interval === i.key}
                onClick={() => onChange(i.key)}
            >
                {i.label}
            </button>
        ))}
    </div>
);

const planFor = (tier, interval) => (tier.plans || []).find(p => p.interval === interval);

// Founding member offer is on while a founding plan is offered and the end date (if any) has not passed.
export const foundingOfferOpen = (tiers, settings) => {
    const end = settings.founding_member_end_date ? new Date(settings.founding_member_end_date) : null;
    if (end && end < new Date()) return false;
    return tiers.some(t => (t.plans || []).some(p => p.is_founding));
};

export const FoundingBanner = () => {
    const { tiers, settings } = useTcc();
    if (!foundingOfferOpen(tiers, settings)) return null;
    const end = settings.founding_member_end_date ? new Date(settings.founding_member_end_date) : null;
    return (
        <div className="tcc-founding-banner">
            <strong>Founding member offer:</strong> Join now and keep this price for life.
            {end && <> Offer ends {end.toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" })}.</>}
        </div>
    );
};

// What each tier includes: its description plus the video sections it unlocks.
const sectionsFor = (tier, settings) =>
    (settings.video_sections || []).filter(s => s.tier_rank <= tier.rank).map(s => s.label);

const TierCards = ({ interval, onChoose, chosenPlanId }) => {
    const { tiers, settings } = useTcc();
    const per = INTERVALS.find(i => i.key === interval).per;

    return (
        <div className="tcc-tier-grid">
            {tiers.map(tier => {
                const plan = planFor(tier, interval);
                const monthly = planFor(tier, "month");
                const saving = interval === "year" && plan && monthly
                    ? Number(monthly.price) * 12 - Number(plan.price)
                    : 0;
                const chosen = plan && plan.id === chosenPlanId;
                return (
                    <section key={tier.id} className={`tcc-tier-card${chosen ? " chosen" : ""}`}>
                        <h3 className="tcc-tier-name">{tier.name}</h3>
                        {plan ? (
                            <p className="tcc-tier-price">
                                <span className="tcc-price">{formatPrice(plan.price)}</span> {per}
                            </p>
                        ) : (
                            <p className="tcc-tier-price">Not offered {per}</p>
                        )}
                        {saving > 0 && <p className="tcc-tier-saving">Save {formatPrice(saving)} compared to paying monthly</p>}
                        {tier.description && <p>{tier.description}</p>}
                        <ul className="tcc-tier-includes">
                            {sectionsFor(tier, settings).map(label => <li key={label}>{label} videos</li>)}
                            <li>Member articles</li>
                        </ul>
                        {onChoose && plan && (
                            <button type="button" className="custom-btn1 tcc-btn tcc-btn-block" onClick={() => onChoose(tier, plan)}>
                                {chosen ? "Chosen" : "Choose this plan"}
                            </button>
                        )}
                    </section>
                );
            })}
        </div>
    );
};

export default TierCards;
