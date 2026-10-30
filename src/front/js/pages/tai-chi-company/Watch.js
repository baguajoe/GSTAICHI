import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch, formatDuration } from "../../component/tai-chi-company/api";
import PlaceholderPlayer from "../../component/tai-chi-company/PlaceholderPlayer";
import ProtectedPlayer from "../../component/tai-chi-company/ProtectedPlayer";
import { VideoBadges } from "../../component/tai-chi-company/VideoCard";
import { useTextSize, TextSizeButtons } from "../../component/tai-chi-company/TextSize";
import { ArticleContent } from "../../component/tai-chi-company/ArticleView";

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

const UpgradeMessage = ({ video }) => {
    const { user, tierName } = useTcc();
    const needed = tierName(video.tier_rank);
    return (
        <div className="tcc-upgrade" role="note">
            <p className="tcc-player-title">This video is part of the {needed ? `${needed} plan` : "member library"}.</p>
            {user ? (
                <>
                    <p>Upgrade your plan to watch it. Plan changes are coming soon.</p>
                    <Link to="/tai-chi-company/join" className="custom-btn1 tcc-btn">See the plans</Link>
                </>
            ) : (
                <>
                    <p>Log in, or join and choose a plan, to watch it.</p>
                    <div className="tcc-button-row">
                        <Link to="/tai-chi-company/join" className="custom-btn1 tcc-btn">See the plans</Link>
                        <Link to="/tai-chi-company/login" className="tcc-btn tcc-btn-outline">Log in</Link>
                    </div>
                </>
            )}
        </div>
    );
};

const SignInToWatch = () => {
    const { settings } = useTcc();
    return (
    <div className="tcc-upgrade" role="note">
        <p className="tcc-player-title">Please log in to watch</p>
        <p>This is a free lesson. Create an account to watch the free lessons.</p>
        <div className="tcc-button-row">
            <Link to="/tai-chi-company/join" className="custom-btn1 tcc-btn">Join {settings.app_name}</Link>
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

    useEffect(() => {
        if (!userLoaded) return;
        setVideo(null);
        setError(null);
        apiFetch(`/api/tcc/videos/${encodeURIComponent(slug)}`)
            .then(setVideo)
            .catch(e => setError(e.message));
        window.scrollTo(0, 0);
    }, [slug, userLoaded, user && user.id]);

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
            {video.locked ? <UpgradeMessage video={video} />
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
