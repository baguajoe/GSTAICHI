import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useTcc } from "./TccContext";
import Overlay from "./Overlay";
import { useInstallPrompt, detectDevice, iosBrowser, computerBrowser } from "./homeScreenApp";
import {
    SafariStep, IphoneShareStep, IphoneAddStep, ConfirmStep, HomeScreenStep, AndroidMenuStep, AndroidAddStep
} from "./PhonePictures";

// "Install the app": one click where the browser can install it itself (Android, Chrome, Edge), otherwise a
// pop-up with pictures. The same steps are used on the /tai-chi-company/add-to-phone help page.

const BANNER_DISMISSED_KEY = "tcc-install-banner-dismissed";

export const Step = ({ number, title, children, picture }) => (
    <li className="tcc-step">
        <div className="tcc-step-text">
            <h3><span className="tcc-step-number">Step {number}</span> {title}</h3>
            {children}
        </div>
        {picture && <div className="tcc-step-picture">{picture}</div>}
    </li>
);

const CopyLink = () => {
    const [copied, setCopied] = useState(false);
    const copy = async () => {
        try {
            await navigator.clipboard.writeText(window.location.href);
            setCopied(true);
        } catch (e) {
            setCopied(false);
        }
    };
    return (
        <>
            <button type="button" className="tcc-btn tcc-btn-outline" onClick={copy}>Copy the link to this page</button>
            {copied && <p className="tcc-success" role="status">Copied. Now open Safari, tap the address bar at the top, and choose Paste and Go.</p>}
        </>
    );
};

// Shown on iPhone and iPad in a browser that cannot add apps to the home screen
export const OpenInSafariNotice = () => (
    <div className="tcc-notice tcc-install-warning" role="alert">
        <p><strong>First, open this page in Safari.</strong></p>
        <p>
            The browser you are using cannot add apps to your home screen. Copy the link below, then open
            the <strong>Safari</strong> app (the blue compass) and paste it into the address bar.
        </p>
        <CopyLink />
    </div>
);

export const IphoneSteps = ({ appName, device, showFinish = true }) => {
    const shareWhere = device === "ipad" ? "at the top of the screen" : "at the bottom of the screen (on iPad, the top)";
    return (
        <>
            <ol className="tcc-steps">
                <Step number={1} title="Open this site in Safari" picture={<SafariStep />}>
                    <p>Use the <strong>Safari</strong> app (the blue compass). Chrome also works on newer iPhones.</p>
                </Step>
                <Step number={2} title="Tap the Share button" picture={<IphoneShareStep />}>
                    <p>Look {shareWhere}. Tap the button that looks like a <strong>square with an arrow pointing up</strong>.</p>
                </Step>
                <Step number={3} title={'Scroll down and tap "Add to Home Screen"'} picture={<IphoneAddStep />}>
                    <p>A menu slides up. Slide your finger up on the menu to scroll down, then tap <strong>Add to Home Screen</strong>.</p>
                </Step>
                <Step number={4} title={'Tap "Add"'} picture={<ConfirmStep appName={appName} button="Add" />}>
                    <p>You will see the name <strong>{appName}</strong>. Tap <strong>Add</strong> in the top right corner.</p>
                </Step>
            </ol>
            {showFinish && <FinishNote appName={appName} />}
        </>
    );
};

export const AndroidSteps = ({ appName, showFinish = true }) => (
    <>
        <ol className="tcc-steps">
            <Step number={1} title="Tap the menu button" picture={<AndroidMenuStep />}>
                <p>In <strong>Chrome</strong>, look at the top right corner of the screen. Tap the button with <strong>three dots</strong>.</p>
            </Step>
            <Step number={2} title={'Tap "Add to Home screen" or "Install app"'} picture={<AndroidAddStep />}>
                <p>A menu opens. Tap <strong>Add to Home screen</strong>. On some phones it is called <strong>Install app</strong>.</p>
            </Step>
            <Step number={3} title={'Tap "Install" or "Add"'} picture={<ConfirmStep appName={appName} button="Install" />}>
                <p>A box shows the name <strong>{appName}</strong>. Tap <strong>Install</strong> (or <strong>Add</strong>).</p>
            </Step>
        </ol>
        {showFinish && <FinishNote appName={appName} />}
    </>
);

const FinishNote = ({ appName }) => (
    <div className="tcc-step tcc-step-finish">
        <div className="tcc-step-text">
            <h3>That's it</h3>
            <p>The <strong>{appName}</strong> icon is now on your home screen, like any other app. Tap it whenever you want to practice.</p>
        </div>
        <div className="tcc-step-picture"><HomeScreenStep appName={appName} /></div>
    </div>
);

export const ComputerSteps = ({ appName }) => {
    const browser = computerBrowser();
    if (browser === "mac-safari") {
        return <p>In the menu bar at the top of the screen, click <strong>File</strong>, then <strong>Add to Dock</strong>, then <strong>Add</strong>. {appName} will appear in your Dock.</p>;
    }
    if (browser === "chrome" || browser === "edge") {
        return (
            <p>
                Click the <strong>install icon</strong> at the right end of the address bar (a small screen with an arrow),
                or open the browser menu (the three dots in the top right) and look
                for <strong>Install {appName}</strong>. If you do not see it, {appName} may already be installed on this computer.
            </p>
        );
    }
    return <p>This browser cannot install apps. Open this site in <strong>Google Chrome</strong> or <strong>Microsoft Edge</strong>, then click <strong>Install the app</strong> again.</p>;
};

const InstallDialog = ({ onClose }) => {
    const { settings } = useTcc();
    const appName = settings.app_name;
    const device = detectDevice();
    const isApple = device === "iphone" || device === "ipad";
    const box = useRef(null);

    useEffect(() => {
        const first = box.current && box.current.querySelector("button");
        if (first) first.focus();
        const onKey = (e) => { if (e.key === "Escape") onClose(); };
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, []);

    return (
        <Overlay>
            <div className="tcc-dialog-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
                <div className="tcc-dialog tcc-install-dialog" role="dialog" aria-modal="true" aria-labelledby="tcc-install-title" ref={box}>
                    <div className="tcc-install-dialog-top">
                        <h2 id="tcc-install-title">Install {appName}</h2>
                        <button type="button" className="tcc-btn tcc-btn-outline" onClick={onClose}>Close</button>
                    </div>
                    {isApple && iosBrowser() === "open-safari" && <OpenInSafariNotice />}
                    {isApple && <IphoneSteps appName={appName} device={device} showFinish={false} />}
                    {device === "android" && <AndroidSteps appName={appName} showFinish={false} />}
                    {device === "computer" && <ComputerSteps appName={appName} />}
                    <p className="tcc-install-help">
                        <Link to="/tai-chi-company/add-to-phone" onClick={onClose} className="tcc-text-link">
                            See the full help page
                        </Link>
                        {settings.contact_phone && <> or call us at {settings.contact_phone} and we will walk you through it.</>}
                    </p>
                    <div className="tcc-button-row">
                        <button type="button" className="custom-btn1 tcc-btn" onClick={onClose}>Done</button>
                    </div>
                </div>
            </div>
        </Overlay>
    );
};

// Hidden once the app is installed. variant "nav" looks like a menu item, "big" is a large page button,
// anything else a normal button.
export const InstallButton = ({ variant = "big", label = "Install the app" }) => {
    const { canInstall, installed, install } = useInstallPrompt();
    const [showSteps, setShowSteps] = useState(false);
    if (installed) return null;

    const onClick = async () => {
        if (canInstall) await install();
        else setShowSteps(true);
    };
    const className = variant === "nav" ? "tcc-nav-link tcc-nav-install"
        : variant === "big" ? "custom-btn1 tcc-btn tcc-btn-big"
        : "custom-btn1 tcc-btn";
    return (
        <>
            <button type="button" className={className} onClick={onClick}>
                <span><i className="fas fa-download" aria-hidden="true"></i> {label}</span>
            </button>
            {showSteps && <InstallDialog onClose={() => setShowSteps(false)} />}
        </>
    );
};

const bannerDismissed = () => {
    try {
        return localStorage.getItem(BANNER_DISMISSED_KEY) === "1";
    } catch (e) {
        return false;
    }
};

// Shown on the Library until the member installs the app or closes the banner
export const InstallBanner = () => {
    const { settings } = useTcc();
    const { installed } = useInstallPrompt();
    const [dismissed, setDismissed] = useState(bannerDismissed);
    if (installed || dismissed) return null;

    const dismiss = () => {
        try {
            localStorage.setItem(BANNER_DISMISSED_KEY, "1");
        } catch (e) {
            // Private browsing: the banner just comes back next visit
        }
        setDismissed(true);
    };
    return (
        <section className="tcc-install-banner" aria-label="Install the app">
            <p>Install <strong>{settings.app_name}</strong> on your phone or computer for one-tap access.</p>
            <div className="tcc-button-row tcc-left">
                <InstallButton variant="normal" />
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={dismiss}>No thanks</button>
            </div>
        </section>
    );
};
