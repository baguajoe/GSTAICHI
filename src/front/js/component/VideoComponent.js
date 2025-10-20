// VideoComponent.js - A reusable component for embedding Vimeo videos inside a responsive Bootstrap card

import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import '../../styles/videoComponent.css';

const VideoComponent = ({ src, title, description = "" }) => {
    return (
        <div className="video-card-wrapper">
            <div className="card video-card">
                <div className="card-body">
                    <h5 className="card-title text-center video-title">{title}</h5>
                    <div className="video-container">
                        <iframe
                            src={src}
                            title={title}
                            width="100%"
                            height="100%"
                            frameBorder="0"
                            allow="autoplay; fullscreen; picture-in-picture; clipboard-write; encrypted-media"
                            allowFullScreen
                            className="video-iframe"
                        ></iframe>
                    </div>
                    {description && <p className="card-text text-center video-description">{description}</p>}
                </div>
            </div>
        </div>
    );
};

export default VideoComponent;