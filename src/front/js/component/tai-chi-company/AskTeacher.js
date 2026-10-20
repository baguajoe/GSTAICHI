import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTcc } from "./TccContext";
import { apiFetch } from "./api";
import { FormMessage } from "./FormField";

// "Ask Vincent": paying members send a question; their questions and answers are listed below.
const AskTeacher = () => {
    const { settings, user } = useTcc();
    const [text, setText] = useState("");
    const [mine, setMine] = useState([]);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [busy, setBusy] = useState(false);
    const canAsk = user && user.is_paying_member;

    useEffect(() => {
        if (canAsk) apiFetch("/api/tcc/questions/mine").then(setMine).catch(() => {});
    }, [canAsk]);

    const send = async (e) => {
        e.preventDefault();
        setError(null);
        setSuccess(null);
        setBusy(true);
        try {
            const result = await apiFetch("/api/tcc/questions", { method: "POST", body: { question: text } });
            setSuccess(result.msg);
            setText("");
            setMine([result.question, ...mine]);
        } catch (err) {
            setError(err.message);
        }
        setBusy(false);
    };

    return (
        <section className="tcc-section tcc-ask">
            <h2>Ask {settings.teacher_name}</h2>
            {!canAsk ? (
                <p>
                    Members can send {settings.teacher_name} questions about their practice. Some are answered with a
                    short video here. {user ? <Link to="/tai-chi-company/account">Choose a plan</Link> : <Link to="/tai-chi-company/join">Choose a plan</Link>} to ask.
                </p>
            ) : (
                <form onSubmit={send} noValidate>
                    <label htmlFor="ask-text">Your question</label>
                    <p className="tcc-field-hint">For example: "In Single Whip, where should my weight be?" Please write one question at a time.</p>
                    <textarea id="ask-text" className="tcc-input tcc-textarea" rows={4} maxLength={2000} value={text} onChange={e => setText(e.target.value)} />
                    <FormMessage error={error} success={success} />
                    <button type="submit" className="custom-btn1 tcc-btn" disabled={busy || text.trim().length < 10}>
                        Send my question
                    </button>
                </form>
            )}
            {canAsk && mine.length > 0 && (
                <>
                    <h3 className="tcc-section">Your questions</h3>
                    <ul className="tcc-studio-list">
                        {mine.map(q => (
                            <li key={q.id} className="tcc-studio-item">
                                <blockquote className="tcc-question-text">{q.question}</blockquote>
                                {q.status === "answered" ? (
                                    <>
                                        {q.answer_note && <p>{q.answer_note}</p>}
                                        {q.answer_video && (q.answer_video.status === "Published"
                                            ? <Link to={`/tai-chi-company/watch/${q.answer_video.slug}`} className="custom-btn1 tcc-btn">Watch the answer</Link>
                                            : <p className="tcc-success">Answered with a video that is being prepared. You will get an email when it is ready.</p>)}
                                    </>
                                ) : <p className="tcc-field-hint">Sent. Waiting for an answer.</p>}
                            </li>
                        ))}
                    </ul>
                </>
            )}
        </section>
    );
};

export default AskTeacher;
