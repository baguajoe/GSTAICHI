import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch } from "../../component/tai-chi-company/api";
import TierCards, { IntervalToggle, FoundingBanner } from "../../component/tai-chi-company/TierCards";
import PlaceholderPlayer from "../../component/tai-chi-company/PlaceholderPlayer";
import { VideoThumbnail } from "../../component/tai-chi-company/VideoCard";

const Landing = () => {
    const { settings } = useTcc();
    const [billing, setBilling] = useState("month");
    const [sample, setSample] = useState(null);

    useEffect(() => {
        apiFetch("/api/tcc/videos")
            .then(data => setSample(data.videos.find(v => v.is_free_sample) || null))
            .catch(() => setSample(null));
    }, []);

    // The levels; Qigong and the teacher's corner are listed separately below
    const sectionLabels = (settings.video_sections || [])
        .filter(s => s.key !== "qigong" && s.key !== settings.corner_section)
        .map(s => s.label);

    return (
        <div className="tcc-page">
            <section className="tcc-hero">
                <h1>{settings.app_name}</h1>
                <p className="tcc-lead">
                    Learn and practice Tai Chi Chuan at home, at your own pace, with video lessons
                    {settings.school_name ? ` from ${settings.school_name}` : ""}.
                </p>
                <Link to="/tai-chi-company/join" className="custom-btn1 tcc-btn tcc-btn-big">Start your free account</Link>
            </section>

            <FoundingBanner />

            <section className="tcc-section">
                <h2>What's included</h2>
                <ul className="tcc-included">
                    <li><strong>Videos by level</strong>{sectionLabels.length > 0 && `: ${sectionLabels.join(", ")}`}</li>
                    <li><strong>A Qigong section</strong> for all members</li>
                    {settings.corner_name && (
                        <li><strong>{settings.corner_name}</strong>: short videos from {settings.teacher_name} with tips, corrections and answers to your questions</li>
                    )}
                    <li><strong>Member articles</strong> on forms, history, health and more</li>
                    <li><strong>New content added every month</strong></li>
                </ul>
            </section>

            <section className="tcc-section">
                <h2>Choose your level</h2>
                <IntervalToggle interval={billing} onChange={setBilling} />
                <TierCards interval={billing} />
            </section>

            {sample && (
                <section className="tcc-section">
                    <h2>Watch a free sample</h2>
                    <h3>{sample.title}</h3>
                    {sample.coming_soon ? <PlaceholderPlayer /> : (
                        <Link to={`/tai-chi-company/watch/${sample.slug}`} className="tcc-sample-preview">
                            <VideoThumbnail video={sample} />
                            <span className="custom-btn1 tcc-btn tcc-btn-big">Watch the free sample</span>
                        </Link>
                    )}
                    {sample.short_description && <p className="tcc-sample-desc">{sample.short_description}</p>}
                    <Link to={`/tai-chi-company/watch/${sample.slug}`} className="tcc-text-link">
                        Go to the free sample page
                    </Link>
                </section>
            )}

            <section className="tcc-section tcc-center">
                <Link to="/tai-chi-company/join" className="custom-btn1 tcc-btn tcc-btn-big">Start your free account</Link>
            </section>
        </div>
    );
};

export default Landing;
