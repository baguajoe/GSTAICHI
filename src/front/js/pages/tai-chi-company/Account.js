import React, { useRef, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch, setToken } from "../../component/tai-chi-company/api";
import FormField, { FormMessage } from "../../component/tai-chi-company/FormField";
import MyPlan from "../../component/tai-chi-company/MyPlan";
import MyQuestions from "../../component/tai-chi-company/MyQuestions";
import { InstallButton } from "../../component/tai-chi-company/InstallApp";
import { useInstallPrompt } from "../../component/tai-chi-company/homeScreenApp";

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
        <form onSubmit={submit} className="tcc-form tcc-form-left tcc-section" noValidate>
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

const MAX_PHOTO_BYTES = 10 * 1024 * 1024;

// Photo and name. Private: only the member sees them (there is no member list).
const ProfileDetails = () => {
    const { user, setUser } = useTcc();
    const [name, setName] = useState(user.name || "");
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [busy, setBusy] = useState(false);
    const fileInput = useRef(null);

    const run = async (work) => {
        setError(null);
        setSuccess(null);
        setBusy(true);
        try {
            const result = await work();
            setUser(result.user);
            setSuccess(result.msg);
        } catch (err) {
            setError(err.message);
        }
        setBusy(false);
    };

    const saveName = (e) => {
        e.preventDefault();
        run(() => apiFetch("/api/tcc/profile", { method: "PUT", body: { name } }));
    };

    const choosePhoto = (e) => {
        const file = e.target.files && e.target.files[0];
        e.target.value = "";
        if (!file) return;
        if (!file.type.startsWith("image/")) return setError("Please choose a photo (JPG or PNG).");
        if (file.size > MAX_PHOTO_BYTES) return setError("This picture is bigger than 10 MB. Please choose a smaller one.");
        const body = new FormData();
        body.append("photo", file);
        run(() => apiFetch("/api/tcc/profile/photo", { method: "POST", body }));
    };

    const removePhoto = () => run(() => apiFetch("/api/tcc/profile/photo", { method: "DELETE" }));
    const initial = (user.name || user.email || "?").trim().charAt(0).toUpperCase();

    return (
        <section className="tcc-section tcc-profile">
            <h2>Your profile</h2>
            <p className="tcc-field-hint">Only you can see your profile. Other members never see your name, photo or email.</p>
            <div className="tcc-profile-photo-row">
                {user.photo_url
                    ? <img src={user.photo_url} alt="Your profile photo" className="tcc-profile-photo" />
                    : <span className="tcc-profile-photo tcc-profile-initial" aria-hidden="true">{initial}</span>}
                <div className="tcc-button-row tcc-left">
                    <input ref={fileInput} type="file" accept="image/*" className="tcc-visually-hidden" id="profile-photo-input"
                        onChange={choosePhoto} tabIndex={-1} />
                    <button type="button" className="tcc-btn tcc-btn-outline" disabled={busy} onClick={() => fileInput.current.click()}>
                        {busy ? "Please wait…" : user.photo_url ? "Change photo" : "Add a photo (optional)"}
                    </button>
                    {user.photo_url && (
                        <button type="button" className="tcc-btn tcc-btn-outline" disabled={busy} onClick={removePhoto}>Remove photo</button>
                    )}
                </div>
            </div>
            <form onSubmit={saveName} className="tcc-form tcc-form-left" noValidate>
                <FormField id="profile-name" label="Your name" name="name" autoComplete="name" maxLength={120}
                    value={name} onChange={e => setName(e.target.value)} />
                <button type="submit" className="custom-btn1 tcc-btn" disabled={busy || name.trim() === (user.name || "")}>Save name</button>
            </form>
            <FormMessage error={error} success={success} />
        </section>
    );
};

const ChangeEmail = () => {
    const { user, setUser } = useTcc();
    const [open, setOpen] = useState(false);
    const [form, setForm] = useState({ new_email: "", password: "" });
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [busy, setBusy] = useState(false);

    const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

    const submit = async (e) => {
        e.preventDefault();
        setError(null);
        setSuccess(null);
        if (!form.new_email.includes("@")) return setError("Please enter a valid email address.");
        setBusy(true);
        try {
            const result = await apiFetch("/api/tcc/change-email", { method: "POST", body: form });
            setToken(result.token); // sign-ins are tied to the email address
            setUser(result.user);
            setSuccess(result.msg);
            setForm({ new_email: "", password: "" });
            setOpen(false);
        } catch (err) {
            setError(err.message);
        }
        setBusy(false);
    };

    return (
        <section className="tcc-section">
            <h2>Your email address</h2>
            <p className="tcc-plan-line"><strong>{user.email}</strong></p>
            <FormMessage success={success} />
            {!open ? (
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => { setOpen(true); setSuccess(null); }}>Change my email address</button>
            ) : (
                <form onSubmit={submit} className="tcc-form tcc-form-left" noValidate>
                    <FormField id="new-email" label="New email address" name="new_email" type="email" autoComplete="email"
                        value={form.new_email} onChange={update} required />
                    <FormField id="email-password" label="Your password" name="password" type="password"
                        autoComplete="current-password" hint="To keep your account safe, please type your password."
                        value={form.password} onChange={update} required />
                    <FormMessage error={error} />
                    <div className="tcc-button-row tcc-left">
                        <button type="submit" className="custom-btn1 tcc-btn" disabled={busy}>{busy ? "Saving…" : "Change email"}</button>
                        <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => { setOpen(false); setError(null); }}>Cancel</button>
                    </div>
                </form>
            )}
        </section>
    );
};

const EmailPreferences = () => {
    const { settings, user, setUser } = useTcc();
    const [error, setError] = useState(null);
    const [saved, setSaved] = useState(null);
    const name = settings.teacher_name || "Vincent";

    const toggle = async (field, value) => {
        setError(null);
        setSaved(null);
        setUser({ ...user, [field]: value });
        try {
            const result = await apiFetch("/api/tcc/profile", { method: "PUT", body: { [field]: value } });
            setUser(result.user);
            setSaved("Saved.");
        } catch (err) {
            setUser({ ...user, [field]: !value });
            setError(err.message);
        }
    };

    const choices = [
        ["email_new_videos", "Email me when new videos are added"],
        ["email_answers", `Email me when ${name} answers my questions`]
    ];

    return (
        <section className="tcc-section">
            <h2>Emails</h2>
            {choices.map(([field, label]) => (
                <label key={field} className="tcc-check">
                    <input type="checkbox" checked={user[field] !== false} onChange={e => toggle(field, e.target.checked)} />
                    <span>{label}</span>
                </label>
            ))}
            <FormMessage error={error} success={saved} />
        </section>
    );
};

const Account = () => {
    const { settings, user, userLoaded, logout } = useTcc();
    const navigate = useNavigate();
    const { installed } = useInstallPrompt();

    if (!userLoaded) return <p className="tcc-page tcc-center">Loading…</p>;
    if (!user) return <Navigate to="/tai-chi-company/login" replace state={{ from: "/tai-chi-company/account" }} />;

    const signOut = () => {
        logout();
        navigate("/tai-chi-company");
    };

    return (
        <div className="tcc-page tcc-narrow">
            <h1>Your Account</h1>

            <ProfileDetails />

            <ChangeEmail />

            <MyPlan />

            <EmailPreferences />

            <MyQuestions />

            <ChangePassword />

            {!installed && (
                <section className="tcc-section">
                    <h2>Install the app</h2>
                    <p>Put {settings.app_name} on your phone or computer, so you can open it with one tap.</p>
                    <InstallButton />
                </section>
            )}

            <section className="tcc-section">
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={signOut}>Log out</button>
            </section>
            <p className="tcc-form-alt"><Link to="/tai-chi-company/add-to-phone">Help installing the app</Link></p>
            <p className="tcc-form-alt"><Link to="/tai-chi-company/terms">Terms of Use</Link></p>
        </div>
    );
};

export default Account;
