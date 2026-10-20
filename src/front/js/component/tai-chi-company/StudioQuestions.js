import React, { useEffect, useState } from "react";
import { useTcc } from "./TccContext";
import { apiFetch } from "./api";
import { FormMessage } from "./FormField";

const QuestionCard = ({ question, cornerVideos, onAnswerWithVideo, onChanged }) => {
    const [videoId, setVideoId] = useState("");
    const [note, setNote] = useState(question.answer_note || "");
    const [open, setOpen] = useState(false);
    const [error, setError] = useState(null);

    const send = async () => {
        setError(null);
        try {
            await apiFetch(`/api/tcc/studio/questions/${question.id}/answer`, {
                method: "POST", body: { video_id: videoId ? Number(videoId) : undefined, answer_note: note }
            });
            onChanged("The answer is saved. The member will get an email when it is ready to watch.");
        } catch (e) {
            setError(e.message);
        }
    };
    const reopen = async () => {
        await apiFetch(`/api/tcc/studio/questions/${question.id}/reopen`, { method: "POST" });
        onChanged("The question is marked as new again.");
    };

    return (
        <li className="tcc-studio-item">
            <p className="tcc-question-meta">
                <strong>{question.member ? question.member.name || question.member.email : "A member"}</strong>
                {" · "}{new Date(`${question.created_at}Z`).toLocaleDateString(undefined, { dateStyle: "medium" })}
            </p>
            <blockquote className="tcc-question-text">{question.question}</blockquote>
            {question.status === "answered" ? (
                <>
                    <p className="tcc-success">
                        Answered{question.answer_video ? ` with the video "${question.answer_video.title}" (${question.answer_video.status})` : ""}.
                    </p>
                    {question.answer_note && <p>{question.answer_note}</p>}
                    <button type="button" className="tcc-btn tcc-btn-outline" onClick={reopen}>Mark as new again</button>
                </>
            ) : (
                <>
                    <div className="tcc-button-row tcc-left">
                        <button type="button" className="custom-btn1 tcc-btn" onClick={() => onAnswerWithVideo(question)}>Answer with a new video</button>
                        <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => setOpen(!open)}>
                            {open ? "Close" : "Answer with an existing video or a few words"}
                        </button>
                    </div>
                    {open && (
                        <div className="tcc-section">
                            <div className="tcc-field">
                                <label htmlFor={`q-video-${question.id}`}>Video that answers it (optional)</label>
                                <select id={`q-video-${question.id}`} className="tcc-input" value={videoId} onChange={e => setVideoId(e.target.value)}>
                                    <option value="">No video</option>
                                    {cornerVideos.map(v => <option key={v.id} value={v.id}>{v.title} ({v.studio_status})</option>)}
                                </select>
                            </div>
                            <div className="tcc-field">
                                <label htmlFor={`q-note-${question.id}`}>A few words for the member (optional)</label>
                                <textarea id={`q-note-${question.id}`} className="tcc-input tcc-textarea" rows={3} value={note} onChange={e => setNote(e.target.value)} />
                            </div>
                            <FormMessage error={error} />
                            <button type="button" className="custom-btn1 tcc-btn" onClick={send}>Send the answer</button>
                        </div>
                    )}
                </>
            )}
        </li>
    );
};

const StudioQuestions = ({ onAnswerWithVideo }) => {
    const { settings } = useTcc();
    const [status, setStatus] = useState("new");
    const [questions, setQuestions] = useState(null);
    const [cornerVideos, setCornerVideos] = useState([]);
    const [message, setMessage] = useState(null);
    const [error, setError] = useState(null);

    const load = () => {
        apiFetch(`/api/tcc/studio/questions?status=${status}`).then(setQuestions).catch(e => setError(e.message));
        apiFetch("/api/tcc/studio/videos")
            .then(vs => setCornerVideos(vs.filter(v => v.section === settings.corner_section && v.status !== "placeholder")))
            .catch(() => {});
    };
    useEffect(() => { setQuestions(null); load(); }, [status]);

    return (
        <section>
            <p className="tcc-lead">Questions members sent with the "Ask {settings.teacher_name}" form.</p>
            <FormMessage error={error} success={message} />
            <div className="tcc-tabs" role="group" aria-label="Show questions">
                {[["new", "New"], ["answered", "Answered"]].map(([key, label]) => (
                    <button key={key} type="button" aria-pressed={status === key} className={`tcc-tab${status === key ? " active" : ""}`}
                        onClick={() => setStatus(key)}>{label}</button>
                ))}
            </div>
            {!questions && !error && <p>Loading…</p>}
            {questions && questions.length === 0 && <p className="tcc-notice">{status === "new" ? "No new questions." : "No answered questions yet."}</p>}
            <ul className="tcc-studio-list">
                {(questions || []).map(q => (
                    <QuestionCard key={q.id} question={q} cornerVideos={cornerVideos} onAnswerWithVideo={onAnswerWithVideo}
                        onChanged={(msg) => { setMessage(msg); load(); }} />
                ))}
            </ul>
        </section>
    );
};

export default StudioQuestions;
