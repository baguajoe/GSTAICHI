import React, { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch } from "../../component/tai-chi-company/api";
import TierCards, { IntervalToggle, FoundingBanner } from "../../component/tai-chi-company/TierCards";
import FormField, { FormMessage } from "../../component/tai-chi-company/FormField";
import SubscribeButton from "../../component/tai-chi-company/SubscribeButton";
import { LegalLinks } from "../../component/tai-chi-company/legal";

const Join = () => {
    const { user, login, setUser, tiers } = useTcc();
    const [searchParams] = useSearchParams();
    const [billing, setBilling] = useState("month");
    const [chosen, setChosen] = useState(null);
    const [form, setForm] = useState({ name: "", email: "", password: "" });
    const [agreed, setAgreed] = useState(false);
    const [error, setError] = useState(null);
    const [busy, setBusy] = useState(false);
    const [justJoined, setJustJoined] = useState(false);
    const [subscribed, setSubscribed] = useState(null);
    const formRef = useRef(null);

    const scrollToForm = () => {
        if (formRef.current) formRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    const choose = (tier, plan) => {
        setChosen({ tier, plan });
        scrollToForm();
    };
    // The Free plan: just an account, no PayPal
    const chooseFree = () => {
        setChosen({ free: true });
        scrollToForm();
    };
    const freeChosen = !!(chosen && chosen.free);

    // A plan chosen on the home page arrives as ?plan=<id>; select it (and its Monthly/Annual) once the tiers load
    const planParam = searchParams.get("plan");
    useEffect(() => {
        if (!planParam || chosen) return;
        if (planParam === "free") {
            chooseFree();
            return;
        }
        for (const tier of tiers) {
            const plan = (tier.plans || []).find(p => String(p.id) === planParam);
            if (plan) {
                setBilling(plan.interval);
                choose(tier, plan);
                return;
            }
        }
    }, [planParam, tiers]);

    const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

    const submit = async (e) => {
        e.preventDefault();
        setError(null);
        if (!agreed) {
            setError("Please tick the box to agree to the health disclaimer and the Terms of Use.");
            return;
        }
        setBusy(true);
        try {
            await apiFetch("/api/signup", { method: "POST", body: { ...form, agree_terms: true }, auth: false });
            await login(form.email, form.password);
            setJustJoined(true);
        } catch (err) {
            setError(err.message === "User already exists"
                ? "There is already an account with this email. Please log in instead."
                : err.message);
        } finally {
            setBusy(false);
        }
    };

    const choice = chosen && (freeChosen ? (
        <p className="tcc-choice">You chose the <strong>Free</strong> plan. No payment needed.</p>
    ) : (
        <p className="tcc-choice">
            You chose <strong>{chosen.tier.name}</strong>, paid {chosen.plan.interval === "year" ? "yearly" : "monthly"}.
        </p>
    ));

    return (
        <div className="tcc-page">
            <h1>Join</h1>
            <FoundingBanner />

            <section className="tcc-section">
                <h2>Choose your level</h2>
                <IntervalToggle interval={billing} onChange={setBilling} />
                <TierCards interval={billing} onChoose={choose} chosenPlanId={chosen && chosen.plan && chosen.plan.id}
                    onChooseFree={chooseFree} freeChosen={freeChosen} />
                <LegalLinks className="tcc-center" />
            </section>

            <section className="tcc-section tcc-form-section" ref={formRef}>
                {user ? (
                    <div className="tcc-notice">
                        {justJoined && <p className="tcc-success" role="status">Welcome{user.name ? `, ${user.name}` : ""}! Your account is ready.</p>}
                        {subscribed ? (
                            <>
                                <p className="tcc-success" role="status">{subscribed}</p>
                                <Link to="/tai-chi-company/library" className="custom-btn1 tcc-btn">Go to the Library</Link>
                            </>
                        ) : user.is_paying_member ? (
                            <>
                                <p>You already have a plan. You can change it on your Account page.</p>
                                <Link to="/tai-chi-company/account" className="custom-btn1 tcc-btn">Go to my Account</Link>
                            </>
                        ) : freeChosen ? (
                            <>
                                <p>{justJoined ? "You are on the Free plan." : "You already have a free account."} You can read all the
                                    articles and watch the free sample videos.</p>
                                <div className="tcc-button-row">
                                    <Link to="/tai-chi-company/articles" className="custom-btn1 tcc-btn">Read the Articles</Link>
                                    <Link to="/tai-chi-company/library" className="tcc-btn tcc-btn-outline">Go to the Library</Link>
                                </div>
                                <p>To watch all the videos, choose a paid plan above at any time.</p>
                            </>
                        ) : chosen ? (
                            <>
                                {choice}
                                <h3>Pay with PayPal</h3>
                                <p>You can pay with your PayPal account or a credit or debit card. You can cancel any time.</p>
                                <SubscribeButton plan={chosen.plan} user={user} onSubscribed={(result) => {
                                    setUser(result.user);
                                    setSubscribed(result.msg);
                                }} />
                            </>
                        ) : (
                            <>
                                <p>You are on the <strong>Free</strong> plan: you can read all the <Link to="/tai-chi-company/articles">articles</Link> and
                                    watch the free sample videos in the <Link to="/tai-chi-company/library">Library</Link>.</p>
                                <p><strong>To watch all the videos, choose a paid plan above</strong> by pressing "Choose this plan".</p>
                            </>
                        )}
                    </div>
                ) : (
                    <form onSubmit={submit} className="tcc-form" noValidate>
                        <h2>Create your account</h2>
                        {freeChosen
                            ? <p>Just your name, email and a password. No payment needed.</p>
                            : <p>Next, choose your plan and pay securely with PayPal or a card. Or choose <strong>Free</strong> to start without paying.</p>}
                        {choice}
                        <FormField id="join-name" label="Your name" name="name" autoComplete="name"
                            value={form.name} onChange={update} required />
                        <FormField id="join-email" label="Email" name="email" type="email" autoComplete="email"
                            value={form.email} onChange={update} required />
                        <FormField id="join-password" label="Password" name="password" type="password"
                            autoComplete="new-password" hint="At least 8 characters."
                            value={form.password} onChange={update} required minLength={8} />
                        <label className="tcc-check tcc-agree">
                            <input type="checkbox" checked={agreed} onChange={e => setAgreed(e.target.checked)} required aria-required="true" />
                            <span>
                                I have read the <Link to="/tai-chi-company/health" target="_blank" rel="noopener">health disclaimer</Link> and
                                agree to the <Link to="/tai-chi-company/terms" target="_blank" rel="noopener">Terms of Use</Link>
                            </span>
                        </label>
                        <FormMessage error={error} />
                        <button type="submit" className="custom-btn1 tcc-btn tcc-btn-block" disabled={busy}>
                            {busy ? "Creating your account…" : freeChosen ? "Create my free account" : "Create my account"}
                        </button>
                        <p className="tcc-form-alt">
                            Already have an account? <Link to="/tai-chi-company/login">Log in</Link>
                        </p>
                        <LegalLinks className="tcc-center" />
                    </form>
                )}
            </section>
        </div>
    );
};

export default Join;
