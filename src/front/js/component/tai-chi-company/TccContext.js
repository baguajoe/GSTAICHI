import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { apiFetch, getToken, setToken } from "./api";

// Shared data for every Tai Chi Company page: site settings, tiers/plans and the signed-in member.
const TccContext = createContext(null);

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
        loadSite, refreshUser, login, logout, tierName, sectionLabel
    };
    return <TccContext.Provider value={value}>{children}</TccContext.Provider>;
};
