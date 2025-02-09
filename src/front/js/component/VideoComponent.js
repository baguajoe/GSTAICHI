// VideoComponent.js - A reusable component for embedding Vimeo videos inside a responsive Bootstrap card

import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';

const VideoComponent = ({ src, title, description = "" }) => {
    return (
        <div className="card mb-4 col-4" style={{ borderRadius: '8px', boxShadow: '0 2px 5px rgba(0, 0, 0, 0.2)', maxWidth: '540px', margin: '0 auto' }}>
            <div className="card-body">
                <h5 className="card-title text-center">{title}</h5>
                <div style={{ position: 'relative', paddingTop: '56.25%' }}> {/* 16:9 Aspect Ratio */}
                    <iframe
                        src={src}
                        title={title}
                        width="100%"
                        height="100%"
                        frameBorder="0"
                        allow="autoplay; fullscreen; picture-in-picture; clipboard-write; encrypted-media"
                        style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
                    ></iframe>
                </div>
                {description && <p className="card-text text-center">{description}</p>}
            </div>
        </div>
    );
};

export default VideoComponent;