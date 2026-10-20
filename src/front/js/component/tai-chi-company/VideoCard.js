import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useTcc } from "./TccContext";
import { formatDuration } from "./api";

export const VideoThumbnail = ({ video }) => {
    const { sectionLabel } = useTcc();
    const [broken, setBroken] = useState(false);
    if (video.thumbnail_url && !broken) {
        return <img src={video.thumbnail_url} alt="" className="tcc-thumb" loading="lazy" onError={() => setBroken(true)} />;
    }
    return (
        <div className="tcc-thumb tcc-thumb-placeholder" aria-hidden="true">
            <span>{sectionLabel(video.section)}</span>
        </div>
    );
};

export const VideoBadges = ({ video }) => (
    <div className="tcc-badges">
        {video.is_free_sample && <span className="tcc-badge tcc-badge-free">Free sample</span>}
        {video.coming_soon && <span className="tcc-badge tcc-badge-soon">Coming Soon</span>}
        {video.locked && (
            <span className="tcc-badge tcc-badge-locked">
                <i className="fas fa-lock" aria-hidden="true"></i> Upgrade to watch
            </span>
        )}
    </div>
);

const VideoCard = ({ video }) => {
    const duration = formatDuration(video.duration_seconds);
    return (
        <Link to={`/tai-chi-company/watch/${video.slug}`} className="tcc-video-card">
            <VideoThumbnail video={video} />
            <div className="tcc-video-card-body">
                <VideoBadges video={video} />
                <h3 className="tcc-video-title">{video.title}</h3>
                {duration && <p className="tcc-video-duration">Length: {duration}</p>}
                {video.short_description && <p className="tcc-video-desc">{video.short_description}</p>}
            </div>
        </Link>
    );
};

export default VideoCard;
