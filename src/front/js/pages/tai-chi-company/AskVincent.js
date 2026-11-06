import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch } from "../../component/tai-chi-company/api";
import FormField, { FormMessage } from "../../component/tai-chi-company/FormField";
import UpgradeToWatch from "../../component/tai-chi-company/UpgradeToWatch";

const MAX_SUBJECT = 150;
const MAX_QUESTION = 2000;
const TIME_PATTERN = /^(\d{1,2}:)?\d{1,3}[:.][0-5]\d$/;

const longDay = (iso) => iso
    ? new Date(`${iso}${iso.endsWith("Z") ? "" : "Z"}`).toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" })
    : null;

// "Ask Vincent": paying members send a question by email to the teacher (his address is never shown).
// Free members and visitors see what asking includes and the plans.
const AskVincent = () => {
    const { settings, user, userLoaded, sectionLabel } = useTcc();
    const name = settings.teacher_name || "Vincent";
    const empty = { subject: "", question: "", lesson_video_id: "", video_time: "" };
    const [form, setForm] = useState(empty);
    const [lessons, setLessons] = useState([]);
    const [allowance, setAllowance] = useState(null);
    const [error, setError] = useState(null);
    const [sent, setSent] = useState(null);
    const [busy, setBusy] = useState(false);
    const canAsk = user && user.is_paying_member;

    useEffect(() => {
        if (!canAsk) return;
        apiFetch("/api/tcc/questions/allowance").then(setAllowance).catch(() => setAllowance(null));
        apiFetch("/api/tcc/videos")
            .then(data => setLessons(data.videos.filter(v => !v.coming_soon)))
            .catch(() => setLessons([]));
    }, [canAsk]);

    const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

    const send = async (e) => {
        e.preventDefault();
        setError(null);
        const subject = form.subject.trim();
        const question = form.question.trim();
        if (!subject) return setError("Please write a short subject, for example \"Single Whip\".");
        if (question.length < 10) return setError("Please write your question (at least a few words).");
        if (question.length > MAX_QUESTION) return setError(`Please keep your question under ${MAX_QUESTION} characters.`);
        if (form.lesson_video_id && form.video_time.trim() && !TIME_PATTERN.test(form.video_time.trim())) {
            return setError("Please write the time like this: 12:30 (minutes and seconds), or leave it empty.");
        }
        setBusy(true);
        try {
            const result = await apiFetch("/api/tcc/questions", {
                method: "POST",
                body: {
                    subject, question,
                    lesson_video_id: form.lesson_video_id ? Number(form.lesson_video_id) : null,
                    video_time: form.lesson_video_id ? form.video_time.trim() : ""
                }
            });
            setSent(result.msg);
            setForm(empty);
            setAllowance(a => a ? { ...a, remaining: result.remaining } : a);
            window.scrollTo({ top: 0, behavior: "smooth" });
        } catch (err) {
            setError(err.message);
            if (err.data && err.data.weekly_limit) setAllowance(a => a ? { ...a, remaining: 0, next_at: err.data.next_at } : a);
        }
        setBusy(false);
    };

    // Lessons grouped by section, in library order
    const groups = [];
    lessons.forEach(v => {
        const label = sectionLabel(v.section) || "Other";
        let group = groups.find(g => g.label === label);
        if (!group) groups.push(group = { label, videos: [] });
        group.videos.push(v);
    });

    const intro = (
        <p className="tcc-lead">
            Have a question about your practice? Send it to {name}. He reads every question himself,
            and some answers become short videos in {settings.corner_name || "the corner"}.
        </p>
    );

    if (!userLoaded) return <p className="tcc-page tcc-center">Loading…</p>;

    if (!canAsk) {
        return (
            <div className="tcc-page tcc-narrow tcc-ask-page">
                <h1>Ask {name}</h1>
                {intro}
                <UpgradeToWatch
                    title={`Upgrade to ask ${name} your questions`}
                    reason={`Asking ${name} is included with every paid plan.`}
                    freeLine={`You are on the Free plan. Choose a plan below to send ${name} your questions.`} />
            </div>
        );
    }

    if (sent) {
        return (
            <div className="tcc-page tcc-narrow tcc-ask-page">
                <h1>Ask {name}</h1>
                <div className="tcc-ask-thanks" role="status">
                    <p className="tcc-ask-thanks-title">{sent}</p>
                    <p>You will find his answer on your Account page, under <strong>My questions</strong>.</p>
                </div>
                <div className="tcc-button-row tcc-left">
                    <Link to="/tai-chi-company/account#my-questions" className="custom-btn1 tcc-btn">See my questions</Link>
                    {allowance && allowance.remaining > 0 && (
                        <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => setSent(null)}>Ask another question</button>
                    )}
                </div>
            </div>
        );
    }

    const limitReached = allowance && allowance.remaining <= 0;

    return (
        <div className="tcc-page tcc-narrow tcc-ask-page">
            <h1>Ask {name}</h1>
            {intro}
            <p>You can send up to {allowance ? allowance.per_week : 3} questions a week.
                {allowance && !limitReached && <> You have <strong>{allowance.remaining}</strong> left this week.</>}</p>

            {limitReached ? (
                <div className="tcc-notice" role="status">
                    <p>You have sent {allowance.per_week} questions this week. Thank you! {name} will answer them as soon as he can.</p>
                    <p>You can send your next question on <strong>{longDay(allowance.next_at)}</strong>.</p>
                    <Link to="/tai-chi-company/account#my-questions" className="custom-btn1 tcc-btn">See my questions</Link>
                </div>
            ) : (
                <form onSubmit={send} className="tcc-form tcc-ask-form" noValidate>
                    <FormField id="ask-subject" label="Subject" name="subject" value={form.subject} onChange={update}
                        hint='A few words, for example "Single Whip" or "Knee pain".' maxLength={MAX_SUBJECT} required />

                    <div className="tcc-field">
                        <label htmlFor="ask-question">Your question</label>
                        <p className="tcc-field-hint" id="ask-question-hint">Please write one question at a time.</p>
                        <textarea id="ask-question" name="question" className="tcc-input tcc-textarea" rows={7}
                            aria-describedby="ask-question-hint ask-question-count" maxLength={MAX_QUESTION}
                            value={form.question} onChange={update} required />
                        <p className="tcc-field-hint tcc-count" id="ask-question-count">{form.question.length} of {MAX_QUESTION} characters</p>
                    </div>

                    <div className="tcc-field">
                        <label htmlFor="ask-lesson">Which lesson is this about? (optional)</label>
                        <select id="ask-lesson" name="lesson_video_id" className="tcc-input" value={form.lesson_video_id} onChange={update}>
                            <option value="">Not about one lesson</option>
                            {groups.map(g => (
                                <optgroup key={g.label} label={g.label}>
                                    {g.videos.map(v => <option key={v.id} value={v.id}>{v.title}</option>)}
                                </optgroup>
                            ))}
                        </select>
                    </div>

                    {form.lesson_video_id && (
                        <FormField id="ask-time" label="Time in the video (optional)" name="video_time" value={form.video_time}
                            onChange={update} hint="Minutes and seconds, for example 12:30." inputMode="numeric"
                            placeholder="12:30" maxLength={8} />
                    )}

                    <FormMessage error={error} />
                    <button type="submit" className="custom-btn1 tcc-btn" disabled={busy}>
                        {busy ? "Sending…" : `Send my question to ${name}`}
                    </button>
                </form>
            )}
        </div>
    );
};

export default AskVincent;
