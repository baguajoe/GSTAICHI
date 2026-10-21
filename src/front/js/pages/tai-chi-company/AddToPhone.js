import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { useInstallPrompt, detectDevice, iosBrowser } from "../../component/tai-chi-company/homeScreenApp";
import {
    IphoneSteps, AndroidSteps, ComputerSteps, OpenInSafariNotice
} from "../../component/tai-chi-company/InstallApp";

const AddToPhone = () => {
    const { settings } = useTcc();
    const { canInstall, installed, install } = useInstallPrompt();
    const [justInstalled, setJustInstalled] = useState(false);
    const device = detectDevice();
    const isApple = device === "iphone" || device === "ipad";
    const appName = settings.app_name;

    if (installed && !justInstalled) {
        return (
            <div className="tcc-page tcc-narrow">
                <h1>Install the app</h1>
                <p className="tcc-success">You are already using the {appName} app. There is nothing else to do.</p>
                <Link to="/tai-chi-company/library" className="custom-btn1 tcc-btn">Go to the Library</Link>
            </div>
        );
    }

    const iphone = (
        <section className="tcc-section" id="iphone">
            <h2>iPhone and iPad</h2>
            {isApple && iosBrowser() === "open-safari" && <OpenInSafariNotice />}
            <IphoneSteps appName={appName} device={device} />
        </section>
    );
    const android = (
        <section className="tcc-section" id="android">
            <h2>Android phones and tablets</h2>
            <AndroidSteps appName={appName} />
        </section>
    );

    return (
        <div className="tcc-page">
            <h1>Install {appName} on your phone or computer</h1>
            <p className="tcc-lead">
                Put an icon on your home screen (or your computer's desktop), so you can open {appName} with one tap,
                just like any other app. It is free and takes less than a minute. Nothing is downloaded from an app store.
            </p>

            {canInstall && !justInstalled && (
                <div className="tcc-notice tcc-section">
                    <p><strong>Your browser can do this for you.</strong> Tap the button below, then tap <strong>Install</strong>.</p>
                    <button type="button" className="custom-btn1 tcc-btn tcc-btn-big"
                        onClick={async () => setJustInstalled(await install())}>
                        Install the app
                    </button>
                </div>
            )}
            {justInstalled && <p className="tcc-success" role="status">Done! Look for the {appName} icon on your home screen.</p>}

            <p>
                Jump to: <a href="#iphone" className="tcc-text-link">iPhone and iPad</a>
                {" · "}
                <a href="#android" className="tcc-text-link">Android</a>
                {" · "}
                <a href="#computer" className="tcc-text-link">Computer</a>
            </p>

            {device === "android" ? <>{android}{iphone}</> : <>{iphone}{android}</>}

            <section className="tcc-section" id="computer">
                <h2>Computers</h2>
                <p>
                    In <strong>Google Chrome</strong> or <strong>Microsoft Edge</strong>, click <strong>Install the app</strong> at
                    the top of any {appName} page, then click <strong>Install</strong>.
                </p>
                {device === "computer" && <ComputerSteps appName={appName} />}
            </section>

            <section className="tcc-section tcc-notice">
                <h2>Need a hand?</h2>
                <p>
                    Call us at <a href={`tel:${(settings.contact_phone || "").replace(/[^\d+]/g, "")}`}>{settings.contact_phone}</a> and
                    we will walk you through it, step by step.
                </p>
            </section>
        </div>
    );
};

export default AddToPhone;
