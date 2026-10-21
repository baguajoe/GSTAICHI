// "Auto-format" for plain pasted text: decides, line by line, what each short standalone line should become.
// Pure functions (no editor code), so the rules can be checked on their own.

const MAX_HEADING_LENGTH = 80;
const MAX_HEADING_WORDS = 12;
const ENDS_LIKE_A_SENTENCE = /[.,;:!]$/;

const shortLine = (text) => text.length <= MAX_HEADING_LENGTH && text.split(/\s+/).length <= MAX_HEADING_WORDS
    && !ENDS_LIKE_A_SENTENCE.test(text);

// "1. Softness Controls Hardness" or "2) Tranquility Controls Action"
const NUMBERED = /^\d{1,2}[.)]\s+\S/;
// "a. Yielding and striking at the same time" or "B. Leverage or borrowing"
const LETTERED = /^[A-Za-z][.)]\s+\S/;
// A whole line in quotation marks, optionally followed by who said it: "…" — Lao Tzu
const QUOTED = /^["“'‘][^"“”]{8,}["”'’](?:\s*[—–-]+\s*[^"“”]{1,60})?$/;

// Returns "heading", "subheading", "quote" or null for one line of text
export const classifyLine = (raw) => {
    const text = (raw || "").trim();
    if (!text) return null;
    if (NUMBERED.test(text) && shortLine(text)) return "heading";
    if (LETTERED.test(text) && shortLine(text)) return "subheading";
    if (QUOTED.test(text) && text.length <= 400) return "quote";
    return null;
};

// lines: [{ text, formatted }] where formatted means the line already has a heading, list or quote.
// Returns [{ index, kind }] for the lines to change.
export const autoFormatPlan = (lines) => lines
    .map((line, index) => ({ index, kind: line.formatted ? null : classifyLine(line.text) }))
    .filter(change => change.kind);
