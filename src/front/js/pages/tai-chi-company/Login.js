import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import FormField, { FormMessage } from "../../component/tai-chi-company/FormField";

const Login = () => {
    const { user, login, logout } = useTcc();
    const navigate = useNavigate();
    const location = useLocation();
    const [form, setForm] = useState({ email: "", password: "" });
    const [error, setError] = useState(null);
    const [busy, setBusy] = useState(false);

    // Pages that need a sign-in send the member here and back again afterwards
    const from = (location.state && location.state.from) || "/tai-chi-company/library";

    const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

    const submit = async (e) => {
        e.preventDefault();
        setError(null);
        setBusy(true);
        try {
            await login(form.email, form.password);
            navigate(from, { replace: true });
        } catch (err) {
            setError(err.status === 401 ? "That email and password do not match. Please try again." : err.message);
            setBusy(false);
        }
    };

    if (user) {
        return (
            <div className="tcc-page tcc-narrow">
                <h1>Log In</h1>
                <p>You are already logged in as <strong>{user.email}</strong>.</p>
                <div className="tcc-button-row">
                    <Link to="/tai-chi-company/library" className="custom-btn1 tcc-btn">Go to the Library</Link>
                    <button type="button" className="tcc-btn tcc-btn-outline" onClick={logout}>Log out</button>
                </div>
            </div>
        );
    }

    return (
        <div className="tcc-page tcc-narrow">
            <form onSubmit={submit} className="tcc-form" noValidate>
                <h1>Log In</h1>
                <FormField id="login-email" label="Email" name="email" type="email" autoComplete="email"
                    value={form.email} onChange={update} required />
                <FormField id="login-password" label="Password" name="password" type="password"
                    autoComplete="current-password" value={form.password} onChange={update} required />
                <FormMessage error={error} />
                <button type="submit" className="custom-btn1 tcc-btn tcc-btn-block" disabled={busy}>
                    {busy ? "Logging in…" : "Log in"}
                </button>
                <p className="tcc-form-alt"><Link to="/tai-chi-company/reset-password">Forgot your password?</Link></p>
                <p className="tcc-form-alt">New here? <Link to="/tai-chi-company/join">Start your free account</Link></p>
            </form>
        </div>
    );
};

export default Login;
