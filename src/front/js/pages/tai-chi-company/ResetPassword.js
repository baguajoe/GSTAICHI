import React, { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { apiFetch } from "../../component/tai-chi-company/api";
import FormField, { FormMessage } from "../../component/tai-chi-company/FormField";

// Step 1: ask for the reset email.
const RequestReset = () => {
    const [email, setEmail] = useState("");
    const [error, setError] = useState(null);
    const [sent, setSent] = useState(null);
    const [busy, setBusy] = useState(false);

    const submit = async (e) => {
        e.preventDefault();
        setError(null);
        setBusy(true);
        try {
            const data = await apiFetch("/api/forgot-password", { method: "POST", body: { email }, auth: false });
            setSent(`${data.msg} Please check your email, including the spam folder. The link works for one hour.`);
        } catch (err) {
            setError(err.message);
        } finally {
            setBusy(false);
        }
    };

    return (
        <form onSubmit={submit} className="tcc-form" noValidate>
            <h1>Reset your password</h1>
            <p>Enter the email you use for your account. We will send you a link to choose a new password.</p>
            <FormField id="reset-email" label="Email" type="email" autoComplete="email"
                value={email} onChange={e => setEmail(e.target.value)} required />
            <FormMessage error={error} success={sent} />
            <button type="submit" className="custom-btn1 tcc-btn tcc-btn-block" disabled={busy}>
                {busy ? "Sending…" : "Send me a reset link"}
            </button>
            <p className="tcc-form-alt"><Link to="/tai-chi-company/login">Back to log in</Link></p>
        </form>
    );
};

// Step 2: the page the email link opens.
const ChooseNewPassword = ({ token }) => {
    const [password, setPassword] = useState("");
    const [confirm, setConfirm] = useState("");
    const [error, setError] = useState(null);
    const [done, setDone] = useState(null);
    const [busy, setBusy] = useState(false);

    const submit = async (e) => {
        e.preventDefault();
        setError(null);
        if (password !== confirm) {
            setError("The two passwords are not the same. Please type them again.");
            return;
        }
        setBusy(true);
        try {
            const data = await apiFetch("/api/reset-password", { method: "POST", body: { token, password }, auth: false });
            setDone(data.msg);
        } catch (err) {
            setError(err.message);
        } finally {
            setBusy(false);
        }
    };

    if (done) {
        return (
            <div className="tcc-form">
                <h1>Password changed</h1>
                <p className="tcc-success" role="status">{done}</p>
                <Link to="/tai-chi-company/login" className="custom-btn1 tcc-btn tcc-btn-block">Log in</Link>
            </div>
        );
    }

    return (
        <form onSubmit={submit} className="tcc-form" noValidate>
            <h1>Choose a new password</h1>
            <FormField id="new-password" label="New password" type="password" autoComplete="new-password"
                hint="At least 8 characters." value={password} onChange={e => setPassword(e.target.value)} required minLength={8} />
            <FormField id="confirm-password" label="Type the new password again" type="password" autoComplete="new-password"
                value={confirm} onChange={e => setConfirm(e.target.value)} required />
            <FormMessage error={error} />
            <button type="submit" className="custom-btn1 tcc-btn tcc-btn-block" disabled={busy}>
                {busy ? "Saving…" : "Save my new password"}
            </button>
            <p className="tcc-form-alt"><Link to="/tai-chi-company/reset-password">Ask for a new reset link</Link></p>
        </form>
    );
};

const ResetPassword = () => {
    const [params] = useSearchParams();
    const token = params.get("token");
    return (
        <div className="tcc-page tcc-narrow">
            {token ? <ChooseNewPassword token={token} /> : <RequestReset />}
        </div>
    );
};

export default ResetPassword;
