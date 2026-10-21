// Small fetch helpers for the Tai Chi Company app. The sign-in token is kept in
// localStorage so members stay signed in between visits (it expires after 7 days).

const TOKEN_KEY = "token";

export const getToken = () => {
    try {
        return localStorage.getItem(TOKEN_KEY);
    } catch (e) {
        return null;
    }
};

export const setToken = (token) => {
    try {
        if (token) localStorage.setItem(TOKEN_KEY, token);
        else localStorage.removeItem(TOKEN_KEY);
    } catch (e) {
        // Storage can be blocked (private browsing); the member just stays signed in for this visit
    }
};

const FRIENDLY_ERROR = "Something went wrong. Please check your internet connection and try again.";

// Returns the parsed JSON. Throws an Error with a plain-language message and a .status.
// body is sent as JSON, or as it is when it is FormData (file uploads).
export const apiFetch = async (path, { method = "GET", body, auth = true } = {}) => {
    const headers = {};
    const isForm = typeof FormData !== "undefined" && body instanceof FormData;
    if (body !== undefined && !isForm) headers["Content-Type"] = "application/json";
    const token = auth ? getToken() : null;
    if (token) headers["Authorization"] = `Bearer ${token}`;

    let response;
    try {
        response = await fetch(`${process.env.BACKEND_URL}${path}`, {
            method,
            headers,
            body: body === undefined || isForm ? body : JSON.stringify(body)
        });
    } catch (e) {
        throw Object.assign(new Error(FRIENDLY_ERROR), { status: 0 });
    }

    let data = null;
    try {
        data = await response.json();
    } catch (e) {
        data = null;
    }
    if (response.status === 429) {
        throw Object.assign(new Error("You have tried this too many times. Please wait a while and try again."), { status: 429 });
    }
    if (!response.ok) {
        const message = (data && (data.msg || data.error)) || FRIENDLY_ERROR;
        throw Object.assign(new Error(message), { status: response.status, data });
    }
    return data;
};

export const formatPrice = (price) => `$${Number(price).toFixed(2)}`;

export const formatDuration = (seconds) => {
    if (!seconds) return null;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.round((seconds % 3600) / 60);
    if (hours) return `${hours} hr ${minutes} min`;
    return `${minutes} min`;
};

// Splits text on blank lines so paragraph breaks are kept.
export const toParagraphs = (text) =>
    (text || "").split(/\n\s*\n/).map(p => p.trim()).filter(Boolean);
