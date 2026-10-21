import React, { useState } from "react";

// A+ / A- text size buttons. The chosen size is remembered on this device. Never below 19px.
const SIZES = [19, 20, 22, 25, 28, 32];
const DEFAULT_INDEX = 2;
const KEY = "tccTextSize";

const readIndex = () => {
    try {
        const saved = localStorage.getItem(KEY);
        return saved !== null && SIZES[Number(saved)] ? Number(saved) : DEFAULT_INDEX;
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
