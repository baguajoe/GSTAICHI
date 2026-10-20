import React, { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch } from "../../component/tai-chi-company/api";
import FormField, { FormMessage } from "../../component/tai-chi-company/FormField";

const ChangePassword = () => {
    const empty = { current_password: "", new_password: "", confirm: "" };
    const [form, setForm] = useState(empty);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [busy, setBusy] = useState(false);

    const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

    const submit = async (e) => {
        e.preventDefault();
        setError(null);
        setSuccess(null);
        if (form.new_password !== form.confirm) {
            setError("The two new passwords are not the same. Please type them again.");
            return;
        }
        setBusy(true);
        try {
            const data = await apiFetch("/api/tcc/change-password", {
                method: "POST",
                body: { current_password: form.current_password, new_password: form.new_password }
            });
            setSuccess(data.msg);
            setForm(empty);
        } catch (err) {
            setError(err.message);
        } finally {
            setBusy(false);
        }
    };

    return (
        <form onSubmit={submit} className="tcc-form tcc-section" noValidate>
            <h2>Change your password</h2>
            <FormField id="current-password" label="Current password" name="current_password" type="password"
                autoComplete="current-password" value={form.current_password} onChange={update} required />
            <FormField id="account-new-password" label="New password" name="new_password" type="password"
                autoComplete="new-password" hint="At least 8 characters." value={form.new_password} onChange={update} required minLength={8} />
            <FormField id="account-confirm-password" label="Type the new password again" name="confirm" type="password"
                autoComplete="new-password" value={form.confirm} onChange={update} required />
            <FormMessage error={error} success={success} />
            <button type="submit" className="custom-btn1 tcc-btn" disabled={busy}>
                {busy ? "Saving…" : "Change password"}
            </button>
        </form>
    );
};

const Account = () => {
    const { user, userLoaded, logout, tierName } = useTcc();
    const navigate = useNavigate();

    if (!userLoaded) return <p className="tcc-page tcc-center">Loading…</p>;
    if (!user) return <Navigate to="/tai-chi-company/login" replace state={{ from: "/tai-chi-company/account" }} />;

    const staff = user.role === "admin" || user.role === "teacher";
    const plan = staff
        ? `Full access (${user.role === "admin" ? "administrator" : "teacher"})`
        : (user.effective_tier_rank > 0 && tierName(user.effective_tier_rank)) || "Free account";

    const signOut = () => {
        logout();
        navigate("/tai-chi-company");
    };

    return (
        <div className="tcc-page tcc-narrow">
            <h1>Your Account</h1>
            <dl className="tcc-account-details">
                <dt>Name</dt>
                <dd>{user.name || "Not given"}</dd>
                <dt>Email</dt>
                <dd>{user.email}</dd>
                <dt>Your plan</dt>
                <dd>
                    {plan}
                    {user.is_founding_member && <span className="tcc-badge tcc-badge-founding">Founding member</span>}
                </dd>
            </dl>
            <p className="tcc-notice">Plan changes and billing coming soon.</p>

            <ChangePassword />

            <section className="tcc-section">
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={signOut}>Log out</button>
            </section>
            <p className="tcc-form-alt"><Link to="/tai-chi-company/add-to-phone">Add this app to your phone's home screen</Link></p>
            <p className="tcc-form-alt"><Link to="/tai-chi-company/terms">Terms of Use</Link></p>
        </div>
    );
};

export default Account;
