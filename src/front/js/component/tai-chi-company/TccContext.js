import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { apiFetch, getToken, setToken } from "./api";
import { clearPending, confirmOnce, readPending, retryDelay, RETRY_FOR_MS, savePending } from "./activation";

// Shared data for every Tai Chi Company page: site settings, tiers/plans and the signed-in member.
const TccContext = createContext(null);

// Who members contact for help (shown in the app's help lines)
export const HELP_EMAIL = "chu.v@usa.com";

export const useTcc = () => useContext(TccContext);

export const TccProvider = ({ children }) => {
    const [settings, setSettings] = useState(null);
    const [tiers, setTiers] = useState([]);
    const [user, setUser] = useState(null);
    const [userLoaded, setUserLoaded] = useState(false);
    const [loadError, setLoadError] = useState(null);

    const loadSite = useCallback(async () => {
        setLoadError(null);
        try {
            const [settingsData, tiersData] = await Promise.all([
                apiFetch("/api/tcc/settings", { auth: false }),
                apiFetch("/api/tcc/tiers", { auth: false })
            ]);
            setSettings(settingsData);
            setTiers(tiersData);
        } catch (e) {
            setLoadError(e.message);
        }
    }, []);

    const refreshUser = useCallback(async () => {
        if (!getToken()) {
            setUser(null);
            setUserLoaded(true);
            return null;
        }
        try {
            const me = await apiFetch("/api/tcc/me");
            setUser(me);
            return me;
        } catch (e) {
            // An expired or rejected token means the member is signed out
            if (e.status === 401 || e.status === 403 || e.status === 422) setToken(null);
            setUser(null);
            return null;
        } finally {
            setUserLoaded(true);
        }
    }, []);

    useEffect(() => {
        loadSite();
        refreshUser();
    }, [loadSite, refreshUser]);

    // A PayPal subscription waiting for the server to confirm it:
    // null, or { state: "activating" | "slow" | "failed" | "done", message, result }
    const [activation, setActivation] = useState(null);
    const activationRun = useRef(null);

    const runActivation = useCallback(async (subscriptionId) => {
        if (activationRun.current === subscriptionId) return; // already retrying this one
        activationRun.current = subscriptionId;
        setActivation({ state: "activating" });
        const started = Date.now();
        try {
            for (let attempt = 0; ; attempt++) {
                const outcome = await confirmOnce(subscriptionId);
                if (outcome.result) {
                    clearPending();
                    if (outcome.result.user) setUser(outcome.result.user);
                    setActivation({ state: "done", message: outcome.result.msg, result: outcome.result });
                    return;
                }
                if (outcome.error) {
                    clearPending();
                    setActivation({ state: "failed", message: outcome.error });
                    return;
                }
                if (Date.now() - started > RETRY_FOR_MS) {
                    // Kept in the browser: the next visit tries again (and the server finishes it at sign-in)
                    setActivation({ state: "slow" });
                    return;
                }
                await new Promise(resolve => setTimeout(resolve, retryDelay(attempt)));
            }
        } finally {
            activationRun.current = null;
        }
    }, []);

    // Called by the PayPal button as soon as PayPal approves the subscription
    const startActivation = useCallback((subscriptionId, userId) => {
        savePending(subscriptionId, userId);
        runActivation(subscriptionId);
    }, [runActivation]);

    const clearActivation = useCallback(() => setActivation(null), []);

    // After a page reload (or signing in again), carry on with a subscription PayPal approved earlier
    useEffect(() => {
        if (!user) return;
        const pending = readPending(user.id);
        if (pending) runActivation(pending.subscriptionId);
    }, [user && user.id, runActivation]);

    const login = async (email, password) => {
        const data = await apiFetch("/api/login", { method: "POST", body: { email, password }, auth: false });
        setToken(data.token);
        setUser(data.user);
        return data.user;
    };

    const logout = () => {
        setToken(null);
        setUser(null);
    };

    const tierName = (rank) => {
        const tier = tiers.find(t => t.rank === rank);
        return tier ? tier.name : null;
    };

    const sectionLabel = (key) => {
        const section = ((settings && settings.video_sections) || []).find(s => s.key === key);
        return section ? section.label : key;
    };

    const value = {
        settings, tiers, user, setUser, userLoaded, loadError,
        loadSite, refreshUser, login, logout, tierName, sectionLabel,
        activation, startActivation, clearActivation
    };
    return <TccContext.Provider value={value}>{children}</TccContext.Provider>;
};
