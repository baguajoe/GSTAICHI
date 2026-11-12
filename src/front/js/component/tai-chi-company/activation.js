// After PayPal approves a subscription, the server checks it with PayPal before giving access. PayPal can take a
// while to activate a new subscription, so the ID is kept in the browser and the check is repeated (also after a
// page reload) until the plan is active. The server keeps the ID too, so the next sign-in can finish the job.
import { apiFetch } from "./api";

const KEY = "tcc_pending_subscription";
const KEEP_FOR_MS = 7 * 24 * 60 * 60 * 1000; // older than this, the server (webhook, sign-in) has long taken over
export const RETRY_FOR_MS = 10 * 60 * 1000; // per page visit

export const readPending = (userId) => {
    try {
        const value = JSON.parse(localStorage.getItem(KEY) || "null");
        if (!value || !value.subscriptionId) return null;
        if (Date.now() - (value.savedAt || 0) > KEEP_FOR_MS) {
            localStorage.removeItem(KEY);
            return null;
        }
        return userId === undefined || value.userId === userId ? value : null;
    } catch (e) {
        return null;
    }
};

export const savePending = (subscriptionId, userId) => {
    try {
        localStorage.setItem(KEY, JSON.stringify({ subscriptionId, userId, savedAt: Date.now() }));
    } catch (e) {
        // Storage blocked (private browsing): the retries still run for this visit and the server has the ID
    }
};

export const clearPending = () => {
    try {
        localStorage.removeItem(KEY);
    } catch (e) {
        // nothing to clear
    }
};

// 3 seconds at first, then less often
export const retryDelay = (attempt) => (attempt < 5 ? 3000 : attempt < 15 ? 10000 : 30000);

// "Try again" answers: PayPal not active yet (202 pending), PayPal or our server unreachable, too many tries,
// signed out for a moment. Anything else (another member's subscription, not one of our plans) is final.
const RETRY_STATUSES = [0, 401, 408, 429, 500, 502, 503, 504];

// One confirm attempt. Returns { result } when active, { pending: true } to try again, or { error } when final.
export const confirmOnce = async (subscriptionId) => {
    try {
        const result = await apiFetch("/api/tcc/subscription/confirm", { method: "POST", body: { subscription_id: subscriptionId } });
        return result && result.pending ? { pending: true } : { result };
    } catch (e) {
        if ((e.data && e.data.pending) || RETRY_STATUSES.includes(e.status)) return { pending: true, status: e.status };
        return { error: e.message };
    }
};
