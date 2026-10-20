import { useEffect, useState } from "react";

// Makes /tai-chi-company installable as a home-screen app (PWA).
// The manifest is built by the backend from SiteSettings, so the app name and color are never hard-coded.
// Icons and the service worker are static files in public/ (tcc-icons/, tcc-sw.js).

const setHeadTag = (selector, create) => {
    let el = document.head.querySelector(selector);
    if (!el) {
        el = create();
        document.head.appendChild(el);
    }
    return el;
};

const link = (rel, href) => {
    const el = setHeadTag(`link[rel="${rel}"]`, () => Object.assign(document.createElement("link"), { rel }));
    el.href = href;
};

const meta = (name, content) => {
    const el = setHeadTag(`meta[name="${name}"]`, () => Object.assign(document.createElement("meta"), { name }));
    el.content = content;
};

// Android/Chrome fires this once, possibly before the help page is open, so keep it here.
let deferredPrompt = null;
const promptListeners = new Set();
if (typeof window !== "undefined") {
    window.addEventListener("beforeinstallprompt", (e) => {
        e.preventDefault();
        deferredPrompt = e;
        promptListeners.forEach(fn => fn(e));
    });
    window.addEventListener("appinstalled", () => {
        deferredPrompt = null;
        promptListeners.forEach(fn => fn(null));
    });
}

export const useHomeScreenApp = (settings) => {
    useEffect(() => {
        if (!settings) return;
        link("manifest", `${process.env.BACKEND_URL}/api/tcc/manifest.webmanifest`);
        link("apple-touch-icon", "/tcc-icons/apple-touch-icon.png");
        meta("apple-mobile-web-app-capable", "yes");
        meta("mobile-web-app-capable", "yes");
        meta("apple-mobile-web-app-title", settings.app_name);
        meta("theme-color", settings.primary_color);
        if ("serviceWorker" in navigator) {
            navigator.serviceWorker.register("/tcc-sw.js", { scope: "/tai-chi-company/" }).catch(() => {
                // Without the service worker the site still works; it just can't show the offline page
            });
        }
    }, [settings]);
};

// For the help page: the Android install prompt, if the browser offered one.
export const useInstallPrompt = () => {
    const [promptEvent, setPromptEvent] = useState(deferredPrompt);
    useEffect(() => {
        promptListeners.add(setPromptEvent);
        return () => promptListeners.delete(setPromptEvent);
    }, []);
    const install = async () => {
        if (!promptEvent) return false;
        promptEvent.prompt();
        const choice = await promptEvent.userChoice;
        deferredPrompt = null;
        setPromptEvent(null);
        return choice.outcome === "accepted";
    };
    return { canInstall: !!promptEvent, install };
};

export const isRunningAsApp = () =>
    (window.matchMedia && window.matchMedia("(display-mode: standalone)").matches) || window.navigator.standalone === true;

export const detectDevice = () => {
    const ua = navigator.userAgent || "";
    if (/iPhone|iPod/.test(ua)) return "iphone";
    // iPadOS reports itself as a Mac; a touch screen gives it away
    if (/iPad/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1)) return "ipad";
    if (/Android/.test(ua)) return "android";
    return "computer";
};
