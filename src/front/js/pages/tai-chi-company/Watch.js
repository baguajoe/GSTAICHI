import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch, formatDuration } from "../../component/tai-chi-company/api";
import PlaceholderPlayer from "../../component/tai-chi-company/PlaceholderPlayer";
import ProtectedPlayer from "../../component/tai-chi-company/ProtectedPlayer";
import { VideoBadges } from "../../component/tai-chi-company/VideoCard";
import { useTextSize, TextSizeButtons } from "../../component/tai-chi-company/TextSize";
import { ArticleContent } from "../../component/tai-chi-company/ArticleView";
import UpgradeToWatch from "../../component/tai-chi-company/UpgradeToWatch";

const AboutThisForm = ({ html }) => {
    const size = useTextSize();
    if (!html) return null;
    return (
        <section className="tcc-section tcc-about">
            <div className="tcc-about-header">
                <h2>About This Form</h2>
                <TextSizeButtons size={size} />
            </div>
            <div className="tcc-about-text" style={{ fontSize: `${size.fontSize}px` }}>
                <ArticleContent html={html} />
            </div>
        </section>
    );
};

const SignInToWatch = () => {
    return (
    <div className="tcc-upgrade" role="note">
        <p className="tcc-player-title">Please log in to watch</p>
        <p>This is a free lesson. Create a free account to watch the free lessons. No payment needed.</p>
        <div className="tcc-button-row">
            <Link to="/tai-chi-company/join?plan=free" className="custom-btn1 tcc-btn">Create free account</Link>
            <Link to="/tai-chi-company/login" className="tcc-btn tcc-btn-outline">Log in</Link>
        </div>
    </div>
    );
};

const Watch = () => {
    const { slug } = useParams();
    const { user, userLoaded } = useTcc();
    const [video, setVideo] = useState(null);
    const [error, setError] = useState(null);
    const [reload, setReload] = useState(0);

    useEffect(() => {
        if (!userLoaded) return;
        setVideo(null);
        setError(null);
        apiFetch(`/api/tcc/videos/${encodeURIComponent(slug)}`)
            .then(setVideo)
            .catch(e => setError(e.message));
        window.scrollTo(0, 0);
    }, [slug, userLoaded, user && user.id, reload]);

    if (error) {
        return (
            <div className="tcc-page tcc-center">
                <p className="tcc-error" role="alert">{error}</p>
                <Link to="/tai-chi-company/library" className="custom-btn1 tcc-btn">Back to the Library</Link>
            </div>
        );
    }
    if (!video) return <p className="tcc-page tcc-center">Loading…</p>;

    const duration = formatDuration(video.duration_seconds);

    return (
        <div className="tcc-page">
            <p><Link to="/tai-chi-company/library" className="tcc-text-link">&larr; Back to the Library</Link></p>
            {video.locked ? <UpgradeToWatch tierRank={video.tier_rank} onUpgraded={() => setReload(r => r + 1)} />
                : video.coming_soon ? <PlaceholderPlayer />
                : !user ? <SignInToWatch />
                : <ProtectedPlayer key={video.slug} video={video} />}

            <h1 className="tcc-watch-title">{video.title}</h1>
            <VideoBadges video={video} />
            {duration && <p className="tcc-video-duration">Length: {duration}</p>}
            {video.short_description && <p className="tcc-lead">{video.short_description}</p>}

            <AboutThisForm html={video.long_description_html} />

            {video.up_next.length > 0 && (
                <section className="tcc-section">
                    <h2>Up next</h2>
                    <ul className="tcc-up-next">
                        {video.up_next.map(v => (
                            <li key={v.id}>
                                <Link to={`/tai-chi-company/watch/${v.slug}`}>
                                    <span className="tcc-up-next-title">{v.title}</span>
                                    <VideoBadges video={v} />
                                </Link>
                            </li>
                        ))}
                    </ul>
                </section>
            )}
        </div>
    );
};

export default Watch;
