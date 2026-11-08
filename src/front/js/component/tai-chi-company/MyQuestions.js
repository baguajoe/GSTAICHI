import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTcc } from "./TccContext";
import { apiFetch, toParagraphs } from "./api";
import { QuestionVideoPlayer } from "./QuestionVideo";

const shortDate = (iso) => iso
    ? new Date(`${iso}${iso.endsWith("Z") ? "" : "Z"}`).toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" })
    : "";

// Account page: the member's own questions to the teacher, Waiting or Answered, with any answer.
const MyQuestions = () => {
    const { settings, user } = useTcc();
    const name = settings.teacher_name || "Vincent";
    const [questions, setQuestions] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        apiFetch("/api/tcc/questions/mine").then(setQuestions).catch(e => setError(e.message));
    }, [user.id]);

    useEffect(() => {
        // Opened from "See my questions" or an answer email: scroll here once the list is in
        if (questions && window.location.hash === "#my-questions") {
            const el = document.getElementById("my-questions");
            if (el) el.scrollIntoView({ behavior: "smooth" });
        }
    }, [questions]);

    return (
        <section className="tcc-section" id="my-questions">
            <h2>My questions</h2>
            {error && <p className="tcc-error" role="alert">{error}</p>}
            {!questions && !error && <p>Loading…</p>}
            {questions && questions.length === 0 && (
                <p>
                    You have not asked {name} anything yet.{" "}
                    {user.is_paying_member
                        ? <Link to="/tai-chi-company/ask-vincent">Ask {name} a question</Link>
                        : <>Asking is included with every paid plan.</>}
                </p>
            )}
            {questions && questions.length > 0 && (
                <>
                    {user.is_paying_member && (
                        <p><Link to="/tai-chi-company/ask-vincent" className="tcc-btn tcc-btn-outline">Ask {name} another question</Link></p>
                    )}
                    <ul className="tcc-studio-list tcc-my-questions">
                        {questions.map(q => (
                            <li key={q.id} className="tcc-studio-item">
                                <p className="tcc-question-meta">
                                    <span className={`tcc-badge ${q.status === "answered" ? "tcc-badge-free" : "tcc-badge-soon"}`}>
                                        {q.status === "answered" ? "Answered" : "Waiting"}
                                    </span>
                                    {" "}Sent {shortDate(q.created_at)}
                                </p>
                                {q.subject && <h3 className="tcc-question-subject">{q.subject}</h3>}
                                {q.lesson && (
                                    <p className="tcc-field-hint">
                                        About <Link to={`/tai-chi-company/watch/${q.lesson.slug}`}>{q.lesson.title}</Link>
                                        {q.video_time ? ` at ${q.video_time}` : ""}
                                    </p>
                                )}
                                <blockquote className="tcc-question-text">{q.question}</blockquote>
                                <div className={q.member_video ? "tcc-qa-row" : undefined}>
                                {q.member_video && <QuestionVideoPlayer questionId={q.id} video={q.member_video} title="Your video" />}
                                {q.status === "answered" ? (
                                    <div className="tcc-answer">
                                        <p className="tcc-answer-title">{name}'s answer{q.answered_at ? ` (${shortDate(q.answered_at)})` : ""}</p>
                                        {q.answer_note && toParagraphs(q.answer_note).map((p, i) => <p key={i} className="tcc-answer-text">{p}</p>)}
                                        {q.answer_video && (q.answer_video.status === "Published"
                                            ? <Link to={`/tai-chi-company/watch/${q.answer_video.slug}`} className="custom-btn1 tcc-btn">Watch the answer</Link>
                                            : <p>{name} answered with a video that is being prepared. You will get an email when it is ready.</p>)}
                                        {!q.answer_note && !q.answer_video && <p>{name} answered you by email.</p>}
                                    </div>
                                ) : <p className="tcc-field-hint">{name} will answer as soon as he can.</p>}
                                </div>
                            </li>
                        ))}
                    </ul>
                </>
            )}
        </section>
    );
};

export default MyQuestions;
