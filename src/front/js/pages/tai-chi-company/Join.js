import React, { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch } from "../../component/tai-chi-company/api";
import TierCards, { IntervalToggle, FoundingBanner } from "../../component/tai-chi-company/TierCards";
import FormField, { FormMessage } from "../../component/tai-chi-company/FormField";

const Join = () => {
    const { user, login } = useTcc();
    const [billing, setBilling] = useState("month");
    const [chosen, setChosen] = useState(null);
    const [form, setForm] = useState({ name: "", email: "", password: "" });
    const [error, setError] = useState(null);
    const [busy, setBusy] = useState(false);
    const [justJoined, setJustJoined] = useState(false);
    const formRef = useRef(null);

    const choose = (tier, plan) => {
        setChosen({ tier, plan });
        if (formRef.current) formRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

    const submit = async (e) => {
        e.preventDefault();
        setError(null);
        setBusy(true);
        try {
            await apiFetch("/api/signup", { method: "POST", body: form, auth: false });
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

    const choice = chosen && (
        <p className="tcc-choice">
            You chose <strong>{chosen.tier.name}</strong>, paid {chosen.plan.interval === "year" ? "yearly" : "monthly"}.
        </p>
    );

    return (
        <div className="tcc-page">
            <h1>Join</h1>
            <FoundingBanner />

            <section className="tcc-section">
                <h2>Choose your level</h2>
                <IntervalToggle interval={billing} onChange={setBilling} />
                <TierCards interval={billing} onChoose={choose} chosenPlanId={chosen && chosen.plan.id} />
            </section>

            <section className="tcc-section tcc-form-section" ref={formRef}>
                {user ? (
                    <div className="tcc-notice">
                        {justJoined && <p className="tcc-success" role="status">Welcome{user.name ? `, ${user.name}` : ""}! Your free account is ready.</p>}
                        {choice}
                        <p><strong>Payment coming soon.</strong> For now you have a free account, and you can watch the free sample video.</p>
                        <Link to="/tai-chi-company/library" className="custom-btn1 tcc-btn">Go to the Library</Link>
                    </div>
                ) : (
                    <form onSubmit={submit} className="tcc-form" noValidate>
                        <h2>Create your free account</h2>
                        {choice}
                        <p>Payment coming soon. Today we will create a free account for you.</p>
                        <FormField id="join-name" label="Your name" name="name" autoComplete="name"
                            value={form.name} onChange={update} required />
                        <FormField id="join-email" label="Email" name="email" type="email" autoComplete="email"
                            value={form.email} onChange={update} required />
                        <FormField id="join-password" label="Password" name="password" type="password"
                            autoComplete="new-password" hint="At least 8 characters."
                            value={form.password} onChange={update} required minLength={8} />
                        <FormMessage error={error} />
                        <button type="submit" className="custom-btn1 tcc-btn tcc-btn-block" disabled={busy}>
                            {busy ? "Creating your account…" : "Create my free account"}
                        </button>
                        <p className="tcc-form-alt">
                            Already have an account? <Link to="/tai-chi-company/login">Log in</Link>
                        </p>
                    </form>
                )}
            </section>
        </div>
    );
};

export default Join;
