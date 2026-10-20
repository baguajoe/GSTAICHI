import React from "react";

// Shown instead of the player while a video has not been uploaded yet. Never a broken player.
const PlaceholderPlayer = () => (
    <div className="tcc-player" role="img" aria-label="This video is coming soon">
        <div className="tcc-player-message">
            <p className="tcc-player-title">Coming Soon</p>
            <p>This video is being prepared and will be ready to watch here soon.</p>
        </div>
    </div>
);

export default PlaceholderPlayer;
