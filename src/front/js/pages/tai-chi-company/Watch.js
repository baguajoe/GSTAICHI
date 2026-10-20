import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { apiFetch, formatDuration, toParagraphs } from "../../component/tai-chi-company/api";
import PlaceholderPlayer from "../../component/tai-chi-company/PlaceholderPlayer";
import { VideoBadges } from "../../component/tai-chi-company/VideoCard";

const FONT_SIZES = [18, 20, 22, 25, 28, 32];
const FONT_KEY = "tccAboutFontSize";

const readFontIndex = () => {
    try {
        const saved = Number(localStorage.getItem(FONT_KEY));
        return FONT_SIZES[saved] ? saved : 2;
    } catch (e) {
        return 2;
    }
};

const AboutThisForm = ({ text }) => {
    const [sizeIndex, setSizeIndex] = useState(readFontIndex);
    const paragraphs = toParagraphs(text);
    if (paragraphs.length === 0) return null;

    const change = (step) => {
        const next = Math.min(FONT_SIZES.length - 1, Math.max(0, sizeIndex + step));
        setSizeIndex(next);
        try {
            localStorage.setItem(FONT_KEY, String(next));
        } catch (e) {
            // Remembering the size is only a convenience
        }
    };

    return (
        <section className="tcc-section tcc-about">
            <div className="tcc-about-header">
                <h2>About This Form</h2>
                <div className="tcc-font-buttons" role="group" aria-label="Text size">
                    <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => change(-1)}
                        disabled={sizeIndex === 0} aria-label="Make text smaller">A-</button>
                    <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => change(1)}
                        disabled={sizeIndex === FONT_SIZES.length - 1} aria-label="Make text larger">A+</button>
                </div>
            </div>
            <div className="tcc-about-text" style={{ fontSize: `${FONT_SIZES[sizeIndex]}px` }}>
                {paragraphs.map((p, i) => <p key={i}>{p}</p>)}
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
                    <p>Log in, or start a free account and choose a plan, to watch it.</p>
                    <div className="tcc-button-row">
                        <Link to="/tai-chi-company/join" className="custom-btn1 tcc-btn">See the plans</Link>
                        <Link to="/tai-chi-company/login" className="tcc-btn tcc-btn-outline">Log in</Link>
                    </div>
                </>
            )}
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
            {video.locked ? <UpgradeMessage video={video} /> : <PlaceholderPlayer video={video} />}

            <h1 className="tcc-watch-title">{video.title}</h1>
            <VideoBadges video={video} />
            {duration && <p className="tcc-video-duration">Length: {duration}</p>}
            {video.short_description && <p className="tcc-lead">{video.short_description}</p>}

            <AboutThisForm text={video.long_description} />

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
