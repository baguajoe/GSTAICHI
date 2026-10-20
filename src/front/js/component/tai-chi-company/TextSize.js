import React, { useState } from "react";

// A+ / A- text size buttons. The chosen size is remembered on this device.
const SIZES = [18, 20, 22, 25, 28, 32];
const DEFAULT_INDEX = 2;
const KEY = "tccTextSize";

const readIndex = () => {
    try {
        const saved = Number(localStorage.getItem(KEY));
        return SIZES[saved] ? saved : DEFAULT_INDEX;
    } catch (e) {
        return DEFAULT_INDEX;
    }
};

export const useTextSize = () => {
    const [index, setIndex] = useState(readIndex);
    const change = (step) => {
        const next = Math.min(SIZES.length - 1, Math.max(0, index + step));
        setIndex(next);
        try {
            localStorage.setItem(KEY, String(next));
        } catch (e) {
            // Remembering the size is only a convenience
        }
    };
    return { fontSize: SIZES[index], smaller: () => change(-1), larger: () => change(1),
        atMin: index === 0, atMax: index === SIZES.length - 1 };
};

export const TextSizeButtons = ({ size }) => (
    <div className="tcc-font-buttons" role="group" aria-label="Text size">
        <button type="button" className="tcc-btn tcc-btn-outline" onClick={size.smaller}
            disabled={size.atMin} aria-label="Make text smaller">A-</button>
        <button type="button" className="tcc-btn tcc-btn-outline" onClick={size.larger}
            disabled={size.atMax} aria-label="Make text larger">A+</button>
    </div>
);

const IMAGE_LINE = /^!\[(.*?)\]\((https?:\/\/[^\s)]+)\)$/;

// Plain text with blank lines between paragraphs; a line like ![caption](https://...) is a picture.
export const RichText = ({ text }) => {
    const blocks = (text || "").split(/\n\s*\n/).map(b => b.trim()).filter(Boolean);
    return blocks.map((block, i) => {
        const image = IMAGE_LINE.exec(block);
        if (image) {
            return (
                <figure key={i} className="tcc-figure">
                    <img src={image[2]} alt={image[1]} loading="lazy" />
                    {image[1] && <figcaption>{image[1]}</figcaption>}
                </figure>
            );
        }
        return <p key={i}>{block}</p>;
    });
};
