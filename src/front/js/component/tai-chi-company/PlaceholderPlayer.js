import React from "react";

// Stand-in for the protected video player, which comes in a later phase.
const PlaceholderPlayer = ({ video }) => (
    <div className="tcc-player" role="img" aria-label={`Video player for ${video.title}`}>
        <div className="tcc-player-message">
            {video.coming_soon ? (
                <>
                    <p className="tcc-player-title">Coming Soon</p>
                    <p>This video is being prepared and will be ready to watch here soon.</p>
                </>
            ) : (
                <p className="tcc-player-title">The video player is coming soon.</p>
            )}
        </div>
    </div>
);

export default PlaceholderPlayer;
