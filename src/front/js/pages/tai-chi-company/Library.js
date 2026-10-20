import React, { useEffect, useState } from "react";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch } from "../../component/tai-chi-company/api";
import VideoCard from "../../component/tai-chi-company/VideoCard";

const Library = () => {
    const { settings, user, userLoaded } = useTcc();
    const [library, setLibrary] = useState(null);
    const [error, setError] = useState(null);
    const [tab, setTab] = useState("all");

    const load = () => {
        setError(null);
        apiFetch("/api/tcc/videos").then(setLibrary).catch(e => setError(e.message));
    };

    // Reload when the member signs in or out, because locks depend on their plan
    useEffect(() => {
        if (userLoaded) load();
    }, [userLoaded, user && user.id]);

    const tabs = [{ key: "all", label: "All" }, ...(settings.video_sections || [])];

    if (error) {
        return (
            <div className="tcc-page tcc-center">
                <p className="tcc-error" role="alert">{error}</p>
                <button type="button" className="custom-btn1 tcc-btn" onClick={load}>Try again</button>
            </div>
        );
    }
    if (!library) return <p className="tcc-page tcc-center">Loading the library…</p>;

    const bySlug = Object.fromEntries(library.videos.map(v => [v.slug, v]));
    const newThisMonth = library.new_this_month.map(slug => bySlug[slug]).filter(Boolean);
    const fromTeacher = library.latest_from_teacher.map(slug => bySlug[slug]).filter(Boolean);
    const shown = tab === "all" ? library.videos : library.videos.filter(v => v.section === tab);
    const tabLabel = tabs.find(t => t.key === tab).label;

    return (
        <div className="tcc-page">
            <h1>Library</h1>

            {newThisMonth.length > 0 && (
                <section className="tcc-section">
                    <h2>New This Month</h2>
                    <div className="tcc-video-row">
                        {newThisMonth.map(v => <VideoCard key={v.id} video={v} />)}
                    </div>
                </section>
            )}

            {fromTeacher.length > 0 && (
                <section className="tcc-section">
                    <h2>Latest from {settings.teacher_name}</h2>
                    <div className="tcc-video-row">
                        {fromTeacher.map(v => <VideoCard key={v.id} video={v} />)}
                    </div>
                </section>
            )}

            <section className="tcc-section">
                <div className="tcc-tabs" role="tablist" aria-label="Video levels">
                    {tabs.map(t => (
                        <button
                            key={t.key}
                            type="button"
                            role="tab"
                            aria-selected={tab === t.key}
                            className={`tcc-tab${tab === t.key ? " active" : ""}`}
                            onClick={() => setTab(t.key)}
                        >
                            {t.label}
                        </button>
                    ))}
                </div>
                <h2>{tab === "all" ? "All videos" : `${tabLabel} videos`}</h2>
                {shown.length === 0 ? (
                    <p>There are no videos here yet. New videos are added every month.</p>
                ) : (
                    <div className="tcc-video-grid">
                        {shown.map(v => <VideoCard key={v.id} video={v} />)}
                    </div>
                )}
            </section>
        </div>
    );
};

export default Library;
