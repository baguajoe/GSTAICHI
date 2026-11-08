import { useEffect, useState } from "react";

// Makes /tai-chi-company installable as a home-screen app (PWA).
// The manifest, icons and service worker are static files on the website itself (public/manifest.webmanifest,
// tcc-icons/, tcc-sw.js), linked from template.html, so the browser sees them from the moment any page opens.
// The manifest's name and color are therefore fixed there: changing them in SiteSettings does not change them.
// The iPhone home-screen name and the browser's theme color still follow SiteSettings, below.

const setHeadTag = (selector, create) => {
    let el = document.head.querySelector(selector);
    if (!el) {
        el = create();
        document.head.appendChild(el);
    }
    return el;
};

const meta = (name, content) => {
    const el = setHeadTag(`meta[name="${name}"]`, () => Object.assign(document.createElement("meta"), { name }));
    el.content = content;
};

// Android/Chrome/Edge fire this once, possibly before any install button is on screen, so keep it here.
let deferredPrompt = null;
let installedThisVisit = false;
let macNoticePending = false;  // installed from Chrome or Edge on a Mac: explain macOS's "Data Access Blocked" notice
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
    if ("serviceWorker" in navigator) {
        // Registered on every page, because a member often arrives on the home page first
        navigator.serviceWorker.register("/tcc-sw.js", { scope: "/tai-chi-company/" }).catch(() => {
            // Without the service worker the site still works; it just can't show the offline page
        });
    }
}

// A browser that offers its own install prompt can take a few seconds after the page opens to do so.
// A click in that time waits briefly for it. The wait stays short because the browser only lets the
// prompt open soon after the click.
const PROMPT_ARRIVES_WITHIN_MS = 8000;
const LONGEST_CLICK_WAIT_MS = 2000;

const promptAvailableSoon = () => {
    if (deferredPrompt) return Promise.resolve(true);
    const timeLeft = PROMPT_ARRIVES_WITHIN_MS - performance.now();
    if (!("onbeforeinstallprompt" in window) || timeLeft <= 0) return Promise.resolve(false);
    return new Promise((resolve) => {
        const finish = () => {
            clearTimeout(timer);
            installListeners.delete(finish);
            resolve(!!deferredPrompt);
        };
        const timer = setTimeout(finish, Math.min(timeLeft, LONGEST_CLICK_WAIT_MS));
        installListeners.add(finish);
    });
};

export const useHomeScreenApp = (settings) => {
    useEffect(() => {
        if (!settings) return;
        meta("apple-mobile-web-app-title", settings.app_name);
        meta("theme-color", settings.primary_color);
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
        if (choice.outcome === "accepted") {
            installedThisVisit = true;
            if (installGuide() === "mac-chrome") macNoticePending = true;
        }
        notifyInstall();
        return choice.outcome === "accepted";
    };
    const dismissMacNotice = () => {
        macNoticePending = false;
        notifyInstall();
    };
    return {
        canInstall: !!deferredPrompt, promptAvailableSoon, installed: installedThisVisit || isRunningAsApp(), install,
        showMacNotice: macNoticePending, dismissMacNotice,
    };
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

// Android: which install instructions apply when the browser did not offer its own prompt.
// Samsung Internet's address also says "Chrome", so it is checked first. "other" is any browser better
// replaced by Chrome, including browsers built into other apps (Facebook, Instagram, Google...).
export const androidBrowser = () => {
    const ua = navigator.userAgent || "";
    if (/SamsungBrowser\//.test(ua)) return "samsung";
    if (/; wv\)|FBAN|FBAV|Instagram|GSA\/|EdgA\/|OPR\/|Firefox\/|YaBrowser\/|MiuiBrowser\/|UCBrowser\/|DuckDuckGo\//.test(ua)) return "other";
    return /Chrome\//.test(ua) ? "chrome" : "other";
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

// Which set of install steps fits this device, so the install pop-up and help page can show it first:
// "iphone" (iPhone and iPad), "android", "mac-safari", "mac-chrome" (Chrome, Edge or another Chrome-based
// browser on a Mac) or "windows" (Windows and any other computer)
export const installGuide = () => {
    const device = detectDevice();
    if (device === "iphone" || device === "ipad") return "iphone";
    if (device === "android") return "android";
    if (/Macintosh/.test(navigator.userAgent || "")) {
        const browser = computerBrowser();
        return browser === "chrome" || browser === "edge" ? "mac-chrome" : "mac-safari";
    }
    return "windows";
};
