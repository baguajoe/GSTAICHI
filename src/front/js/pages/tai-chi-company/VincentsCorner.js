import React, { useEffect, useState } from "react";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch } from "../../component/tai-chi-company/api";
import VideoCard from "../../component/tai-chi-company/VideoCard";
import AskTeacher from "../../component/tai-chi-company/AskTeacher";

// The teacher's short videos: tips, corrections, explanations and answers to member questions.
const VincentsCorner = () => {
    const { settings, user, userLoaded } = useTcc();
    const [videos, setVideos] = useState(null);
    const [error, setError] = useState(null);
    const [category, setCategory] = useState("all");

    const load = () => {
        setError(null);
        apiFetch("/api/tcc/videos")
            .then(data => {
                const corner = data.videos.filter(v => v.section === settings.corner_section);
                corner.sort((a, b) => (b.publish_at || "").localeCompare(a.publish_at || "") || b.id - a.id);
                setVideos(corner);
            })
            .catch(e => setError(e.message));
    };

    useEffect(() => {
        if (userLoaded) load();
    }, [userLoaded, user && user.id]);

    const categories = [{ key: "all", label: "All" }, ...(settings.corner_categories || []).map(c => ({ key: c, label: c }))];
    const shown = !videos ? [] : category === "all" ? videos : videos.filter(v => v.category === category);

    return (
        <div className="tcc-page">
            <h1>{settings.corner_name}</h1>
            <p className="tcc-lead">
                Short videos from {settings.teacher_name}: tips, corrections, common mistakes, explanations,
                and answers to members' questions. Included with every paid plan.
            </p>

            <div className="tcc-tabs" role="group" aria-label="Show videos by type">
                {categories.map(c => (
                    <button key={c.key} type="button" aria-pressed={category === c.key}
                        className={`tcc-tab${category === c.key ? " active" : ""}`} onClick={() => setCategory(c.key)}>
                        {c.label}
                    </button>
                ))}
            </div>

            {error && <p className="tcc-error" role="alert">{error}</p>}
            {!videos && !error && <p>Loading…</p>}
            {videos && shown.length === 0 && (
                <p className="tcc-notice">
                    {videos.length === 0
                        ? `${settings.teacher_name}'s first videos are coming soon.`
                        : "There are no videos of this type yet."}
                </p>
            )}
            {shown.length > 0 && (
                <div className="tcc-video-grid">
                    {shown.map(v => <VideoCard key={v.id} video={v} />)}
                </div>
            )}

            <AskTeacher />
        </div>
    );
};

export default VincentsCorner;
