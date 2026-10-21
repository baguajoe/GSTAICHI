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

// Android/Chrome/Edge fire this once, possibly before any install button is on screen, so keep it here.
let deferredPrompt = null;
let installedThisVisit = false;
const installListeners = new Set();
const notifyInstall = () => installListeners.forEach(fn => fn(n => n + 1));
if (typeof window !== "undefined") {
    window.addEventListener("beforeinstallprompt", (e) => {
        e.preventDefault();
        deferredPrompt = e;
        notifyInstall();
    });
    window.addEventListener("appinstalled", () => {
        deferredPrompt = null;
        installedThisVisit = true;
        notifyInstall();
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

// canInstall: the browser offered its own one-click install prompt (Android, Chrome, Edge).
// installed: running as the installed app, or installed during this visit; install buttons hide then.
export const useInstallPrompt = () => {
    const [, rerender] = useState(0);
    useEffect(() => {
        installListeners.add(rerender);
        return () => installListeners.delete(rerender);
    }, []);
    const install = async () => {
        const promptEvent = deferredPrompt;
        if (!promptEvent) return false;
        deferredPrompt = null;  // the browser allows each prompt to be shown only once
        promptEvent.prompt();
        const choice = await promptEvent.userChoice;
        if (choice.outcome === "accepted") installedThisVisit = true;
        notifyInstall();
        return choice.outcome === "accepted";
    };
    return { canInstall: !!deferredPrompt, installed: installedThisVisit || isRunningAsApp(), install };
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

// iPhone and iPad: whether this browser can add the site to the home screen.
// "safari"; "other" (Chrome, Edge or Firefox, which can from iOS 16.4); or "open-safari" for older iOS
// and for browsers built into other apps (Facebook, Instagram, Google...), which cannot.
export const iosBrowser = () => {
    const ua = navigator.userAgent || "";
    if (/FBAN|FBAV|Instagram|LinkedInApp|Snapchat|Pinterest|Line\/|GSA\//.test(ua)) return "open-safari";
    if (/CriOS|EdgiOS|FxiOS/.test(ua)) {
        const version = ua.match(/OS (\d+)_(\d+)/);
        const major = version ? Number(version[1]) : 0;
        const minor = version ? Number(version[2]) : 0;
        return major > 16 || (major === 16 && minor >= 4) ? "other" : "open-safari";
    }
    return /Safari\//.test(ua) && /Version\//.test(ua) ? "safari" : "open-safari";
};

// Computers: which install instructions apply when the browser did not offer its own prompt
export const computerBrowser = () => {
    const ua = navigator.userAgent || "";
    if (/Firefox\//.test(ua)) return "firefox";
    if (/Edg\//.test(ua)) return "edge";
    if (/Chrome\//.test(ua)) return "chrome";
    if (/Safari\//.test(ua) && /Macintosh/.test(ua)) return "mac-safari";
    return "other";
};
