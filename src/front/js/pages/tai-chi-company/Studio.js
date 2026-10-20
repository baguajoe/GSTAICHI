import React, { useState } from "react";
import { Navigate } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import StudioVideos from "../../component/tai-chi-company/StudioVideos";
import StudioArticles from "../../component/tai-chi-company/StudioArticles";
import StudioQuestions from "../../component/tai-chi-company/StudioQuestions";

// Teacher Studio: upload and manage videos, write articles, answer members' questions.
const Studio = () => {
    const { user, userLoaded, settings } = useTcc();
    const [tab, setTab] = useState("videos");
    const [prefill, setPrefill] = useState(null);

    if (!userLoaded) return <p className="tcc-page tcc-center">Loading…</p>;
    if (!user) return <Navigate to="/tai-chi-company/login" replace state={{ from: "/tai-chi-company/studio" }} />;
    if (user.role !== "teacher" && user.role !== "admin") {
        return <div className="tcc-page tcc-narrow"><h1>Studio</h1><p className="tcc-notice">The Studio is for teachers.</p></div>;
    }

    const answerWithVideo = (question) => {
        setPrefill({
            questionId: question.id,
            defaults: { section: settings.corner_section, category: "Q&A", title: `Answer: ${question.question.slice(0, 70)}` }
        });
        setTab("videos");
    };

    const tabs = [["videos", "Videos"], ["articles", "Articles"], ["questions", `Questions for ${settings.teacher_name}`]];
    return (
        <div className="tcc-page tcc-studio">
            <h1>Studio</h1>
            <div className="tcc-tabs tcc-studio-tabs" role="tablist" aria-label="Studio sections">
                {tabs.map(([key, label]) => (
                    <button key={key} type="button" role="tab" aria-selected={tab === key}
                        className={`tcc-tab${tab === key ? " active" : ""}`} onClick={() => setTab(key)}>{label}</button>
                ))}
            </div>
            {tab === "videos" && <StudioVideos prefill={prefill} onPrefillUsed={() => setPrefill(null)} />}
            {tab === "articles" && <StudioArticles />}
            {tab === "questions" && <StudioQuestions onAnswerWithVideo={answerWithVideo} />}
        </div>
    );
};

export default Studio;
