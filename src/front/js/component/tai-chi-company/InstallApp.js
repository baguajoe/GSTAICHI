import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useTcc, HELP_EMAIL } from "./TccContext";
import Overlay from "./Overlay";
import { useInstallPrompt, detectDevice, iosBrowser, androidBrowser, computerBrowser, installGuide } from "./homeScreenApp";
import {
    SafariStep, IphoneShareStep, IphoneAddStep, ConfirmStep, HomeScreenStep, AndroidMenuStep, AndroidAddStep,
    SamsungMenuStep, SamsungAddPageStep, SamsungHomeScreenStep
} from "./PhonePictures";

// "Install the app": one click where the browser can install it itself (Android, Chrome, Edge), otherwise a
// pop-up with pictures. The same steps are used on the /tai-chi-company/add-to-phone help page.

const BANNER_DISMISSED_KEY = "tcc-install-banner-dismissed";

export const Step = ({ number, title, children, picture }) => (
    <li className={picture ? "tcc-step" : "tcc-step tcc-step-nopic"}>
        <div className="tcc-step-text">
            <h3><span className="tcc-step-number">Step {number}</span> {title}</h3>
            {children}
        </div>
        {picture && <div className="tcc-step-picture">{picture}</div>}
    </li>
);

const PHONE_PASTE = "Copied. Now open Safari, tap the address bar at the top, and choose Paste and Go.";

const CopyLink = ({ copiedMessage = PHONE_PASTE }) => {
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
            {copied && <p className="tcc-success" role="status">{copiedMessage}</p>}
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
        <p>
            Use <strong>Chrome</strong>. If you see an <strong>Install app</strong> button or message, tap it, then
            tap <strong>Install</strong>. If not, follow these steps:
        </p>
        <ol className="tcc-steps">
            <Step number={1} title="Tap the menu button" picture={<AndroidMenuStep />}>
                <p>In <strong>Chrome</strong>, look at the top right corner of the screen. Tap the button with <strong>three dots</strong> (⋮).</p>
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

export const SamsungSteps = ({ appName, showFinish = true }) => (
    <>
        <ol className="tcc-steps">
            <Step number={1} title="Tap the menu button" picture={<SamsungMenuStep />}>
                <p>In <strong>Samsung Internet</strong>, look at the bottom right corner of the screen. Tap the button with <strong>three lines</strong> (☰).</p>
            </Step>
            <Step number={2} title={'Tap "Add page to"'} picture={<SamsungAddPageStep />}>
                <p>A menu opens. Tap <strong>Add page to</strong>.</p>
            </Step>
            <Step number={3} title={'Tap "Home screen"'} picture={<SamsungHomeScreenStep />}>
                <p>A short list opens. Tap <strong>Home screen</strong>.</p>
            </Step>
            <Step number={4} title={'Tap "Add"'} picture={<ConfirmStep appName={appName} button="Add" />}>
                <p>A box shows the name <strong>{appName}</strong>. Tap <strong>Add</strong>.</p>
            </Step>
        </ol>
        {showFinish && <FinishNote appName={appName} />}
    </>
);

// Shown on Android in a browser we have no steps for
const OpenInChromeNotice = () => (
    <div className="tcc-notice tcc-install-warning" role="alert">
        <p><strong>First, open this page in Chrome.</strong></p>
        <p>
            We don't have steps for the browser you are using. Copy the link below, then open
            the <strong>Chrome</strong> app and paste it into the address bar.
        </p>
        <CopyLink copiedMessage="Copied. Now open Chrome, tap the address bar at the top, and paste the link." />
    </div>
);

// thisDevice: the member is reading this on the phone the steps are for, so we can pick that browser's steps
const AndroidGuide = ({ appName, showFinish, thisDevice }) => {
    const browser = thisDevice && detectDevice() === "android" ? androidBrowser() : null;
    if (browser === "samsung") return <SamsungSteps appName={appName} showFinish={showFinish} />;
    return (
        <>
            {browser === "other" && <OpenInChromeNotice />}
            <AndroidSteps appName={appName} showFinish={showFinish} />
            {!browser && (
                <p className="tcc-small-note">
                    Using <strong>Samsung Internet</strong>? Tap the <strong>three lines</strong> (☰) at the bottom right,
                    then <strong>Add page to</strong>, then <strong>Home screen</strong>.
                </p>
            )}
        </>
    );
};

const FinishNote = ({ appName }) => (
    <div className="tcc-step tcc-step-finish">
        <div className="tcc-step-text">
            <h3>That's it</h3>
            <p>The <strong>{appName}</strong> icon is now on your home screen, like any other app. Tap it whenever you want to practice.</p>
        </div>
        <div className="tcc-step-picture"><HomeScreenStep appName={appName} /></div>
    </div>
);

export const BookmarkNote = () => (
    <p className="tcc-bookmark-note">
        <strong>You don't have to install it.</strong> Bookmarking the page works the same.
    </p>
);

// The macOS notice some members see the first time they open the app installed from Chrome or Edge
export const MacDataAccessNotice = ({ appName }) => (
    <div className="tcc-notice tcc-install-warning">
        <p><strong>If your Mac shows "Data Access Blocked"</strong></p>
        <p>
            Your Mac may show a message saying an app "tried to access your data from other apps". This is a normal
            Mac security notice. Nothing is wrong.
        </p>
        <p>
            Click <strong>Manage</strong> in that message (or open <strong>System Settings</strong>, then <strong>Privacy &amp; Security</strong>,
            then <strong>App Management</strong>) and turn on <strong>{appName}</strong>. Then open {appName} again.
        </p>
    </div>
);

// thisDevice: the member is reading this on the device the steps are for, so browser warnings apply
export const MacSafariSteps = ({ appName, thisDevice = true }) => {
    const inSafari = !thisDevice || computerBrowser() === "mac-safari";
    return (
        <>
            {!inSafari && (
                <div className="tcc-notice tcc-install-warning">
                    <p>You are not using Safari right now. Copy the link, then open <strong>Safari</strong> (the blue compass) and paste it into the address bar.</p>
                    <CopyLink copiedMessage="Copied. Now open Safari, click the address bar at the top, press Command (⌘) and V together, then press Return." />
                </div>
            )}
            <ol className="tcc-steps">
                <Step number={1} title="Open this site in Safari">
                    <p>Open the <strong>Safari</strong> app (the blue compass) and go to <strong>gstaichi.org/tai-chi-company</strong>.</p>
                </Step>
                <Step number={2} title={'Click "File", then "Add to Dock"'}>
                    <p>In the menu bar at the very top of the screen, click <strong>File</strong>. Then click <strong>Add to Dock</strong>.</p>
                </Step>
                <Step number={3} title={'Click "Add"'}>
                    <p>
                        A box shows the name <strong>{appName}</strong>. Click <strong>Add</strong>.
                        Its icon appears in your Dock at the bottom of the screen.
                    </p>
                </Step>
            </ol>
            <p className="tcc-small-note">
                Don't see <strong>Add to Dock</strong>? It needs macOS Sonoma (14) or newer. You can use Chrome instead
                (see "Mac with Chrome or Edge"), or simply bookmark the page.
            </p>
        </>
    );
};

export const MacChromeSteps = ({ appName }) => (
    <ol className="tcc-steps">
        <Step number={1} title={'Click "Install the app"'}>
            <p>
                Open this site in <strong>Chrome</strong> or <strong>Edge</strong>. Click <strong>Install the app</strong> at
                the top of any {appName} page, then click <strong>Install</strong>.
            </p>
            <p>
                If nothing happens, click the <strong>install icon</strong> at the right end of the address bar (a small
                screen with an arrow), or open the browser menu (the three dots in the top right corner) and look for <strong>Install</strong>.
            </p>
        </Step>
        <Step number={2} title="If your Mac shows a security message">
            <MacDataAccessNotice appName={appName} />
        </Step>
        <Step number={3} title="Open it any time">
            <p>{appName} opens in its own window. You will find it in your <strong>Dock</strong> or in <strong>Launchpad</strong>.</p>
        </Step>
    </ol>
);

export const WindowsSteps = ({ appName, thisDevice = true }) => {
    const browser = computerBrowser();
    return (
        <>
            {thisDevice && browser !== "chrome" && browser !== "edge" && (
                <div className="tcc-notice tcc-install-warning">
                    <p>This browser cannot install apps. Open this site in <strong>Google Chrome</strong> or <strong>Microsoft Edge</strong> instead.</p>
                </div>
            )}
            <ol className="tcc-steps">
                <Step number={1} title="Open this site in Chrome or Edge">
                    <p>Use <strong>Google Chrome</strong> or <strong>Microsoft Edge</strong>.</p>
                </Step>
                <Step number={2} title={'Click "Install the app"'}>
                    <p>
                        Click <strong>Install the app</strong> at the top of any {appName} page, then click <strong>Install</strong>.
                        If nothing happens, click the <strong>install icon</strong> at the right end of the address bar, or open the
                        browser menu (the three dots in the top right corner) and look for <strong>Install</strong>.
                    </p>
                </Step>
                <Step number={3} title="Open it any time">
                    <p>{appName} opens in its own window. You will find it on your desktop or in the <strong>Start</strong> menu.</p>
                </Step>
            </ol>
        </>
    );
};

// Every device, in the order the help page lists them. "quick" is the one-line version for the pop-up.
export const INSTALL_GUIDES = [
    { key: "mac-safari", title: "Mac with Safari (recommended on Mac)", quick: <>Open gstaichi.org/tai-chi-company in <strong>Safari</strong>, then click <strong>File</strong>, then <strong>Add to Dock</strong>.</> },
    { key: "mac-chrome", title: "Mac with Chrome or Edge", quick: <>Click <strong>Install the app</strong>. If your Mac says "Data Access Blocked", that is a normal security notice: click <strong>Manage</strong> and turn on the app, then open it again.</> },
    { key: "iphone", title: "iPhone and iPad", quick: <>In <strong>Safari</strong>, tap the <strong>Share</strong> button, then <strong>Add to Home Screen</strong>.</> },
    { key: "android", title: "Android phones and tablets", quick: <>In <strong>Chrome</strong>, tap <strong>Install app</strong> (or tap the ⋮ menu, then <strong>Add to Home screen</strong>). In <strong>Samsung Internet</strong>, tap the ☰ menu at the bottom right, then <strong>Add page to</strong>, then <strong>Home screen</strong>.</> },
    { key: "windows", title: "Windows computers", quick: <>In <strong>Chrome</strong> or <strong>Edge</strong>, click <strong>Install the app</strong>.</> },
];

// This device's guide first, then the rest
export const orderedGuides = (first) => [
    ...INSTALL_GUIDES.filter(g => g.key === first),
    ...INSTALL_GUIDES.filter(g => g.key !== first),
];

export const GuideSteps = ({ guide, appName, showFinish = true, thisDevice = true }) => {
    const device = detectDevice();
    const isApple = device === "iphone" || device === "ipad";
    if (guide === "iphone") {
        return (
            <>
                {thisDevice && isApple && iosBrowser() === "open-safari" && <OpenInSafariNotice />}
                <IphoneSteps appName={appName} device={device} showFinish={showFinish} />
            </>
        );
    }
    if (guide === "android") return <AndroidGuide appName={appName} showFinish={showFinish} thisDevice={thisDevice} />;
    if (guide === "mac-safari") return <MacSafariSteps appName={appName} thisDevice={thisDevice} />;
    if (guide === "mac-chrome") return <MacChromeSteps appName={appName} />;
    return <WindowsSteps appName={appName} thisDevice={thisDevice} />;
};

// installedNow: the browser's own install prompt just succeeded on a Mac, so only the macOS notice is shown
const InstallDialog = ({ onClose, installedNow = false }) => {
    const { settings } = useTcc();
    const appName = settings.app_name;
    const guide = installGuide();
    const [mine, ...others] = orderedGuides(guide);
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
                        <h2 id="tcc-install-title">{installedNow ? `${appName} is installed` : `Install ${appName}`}</h2>
                        <button type="button" className="tcc-btn tcc-btn-outline" onClick={onClose}>Close</button>
                    </div>
                    {installedNow ? (
                        <MacDataAccessNotice appName={appName} />
                    ) : (
                        <>
                            <p className="tcc-install-for">Steps for this device: <strong>{mine.title}</strong></p>
                            <GuideSteps guide={guide} appName={appName} showFinish={false} />
                            <BookmarkNote />
                            <details className="tcc-install-other">
                                <summary>Using a different device?</summary>
                                <ul>
                                    {others.map(g => <li key={g.key}><strong>{g.title}:</strong> {g.quick}</li>)}
                                </ul>
                            </details>
                        </>
                    )}
                    <p className="tcc-install-help">
                        <Link to="/tai-chi-company/add-to-phone" onClick={onClose} className="tcc-text-link">
                            See the full help page
                        </Link>
                        <> or email Vincent at <a href={`mailto:${HELP_EMAIL}`}>{HELP_EMAIL}</a> and we will walk you through it.</>
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
    const { promptAvailableSoon, installed, install } = useInstallPrompt();
    const [showSteps, setShowSteps] = useState(false);
    const [checking, setChecking] = useState(false);
    if (installed) return null;

    const onClick = async () => {
        setChecking(true);
        const available = await promptAvailableSoon();
        setChecking(false);
        if (available) await install();
        else setShowSteps(true);
    };
    const className = variant === "nav" ? "tcc-nav-link tcc-nav-install"
        : variant === "big" ? "custom-btn1 tcc-btn tcc-btn-big"
        : "custom-btn1 tcc-btn";
    return (
        <>
            <button type="button" className={className} onClick={onClick} disabled={checking}>
                <span><i className="fas fa-download" aria-hidden="true"></i> {checking ? "One moment…" : label}</span>
            </button>
            {showSteps && <InstallDialog onClose={() => setShowSteps(false)} />}
        </>
    );
};

// Rendered once by TccLayout, which stays on screen when install buttons disappear after installing
export const MacInstalledNotice = () => {
    const { showMacNotice, dismissMacNotice } = useInstallPrompt();
    return showMacNotice ? <InstallDialog installedNow onClose={dismissMacNotice} /> : null;
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
