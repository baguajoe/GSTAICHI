import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { useInstallPrompt, isRunningAsApp, detectDevice } from "../../component/tai-chi-company/homeScreenApp";
import {
    IphoneShareStep, IphoneAddStep, ConfirmStep, HomeScreenStep, AndroidMenuStep, AndroidAddStep
} from "../../component/tai-chi-company/PhonePictures";

const Step = ({ number, title, children, picture }) => (
    <li className="tcc-step">
        <div className="tcc-step-text">
            <h3><span className="tcc-step-number">Step {number}</span> {title}</h3>
            {children}
        </div>
        <div className="tcc-step-picture">{picture}</div>
    </li>
);

const IphoneSteps = ({ appName }) => (
    <section className="tcc-section" id="iphone">
        <h2>iPhone and iPad</h2>
        <p>Use the <strong>Safari</strong> app (the blue compass). This does not work from other browsers on iPhone.</p>
        <ol className="tcc-steps">
            <Step number={1} title="Tap the Share button" picture={<IphoneShareStep />}>
                <p>Look at the bottom of the screen (on iPad, the top). Tap the button that looks like a square with an arrow pointing up.</p>
            </Step>
            <Step number={2} title={'Tap "Add to Home Screen"'} picture={<IphoneAddStep />}>
                <p>A menu slides up. You may need to slide your finger up to scroll down. Tap <strong>Add to Home Screen</strong>.</p>
            </Step>
            <Step number={3} title={'Tap "Add"'} picture={<ConfirmStep appName={appName} button="Add" />}>
                <p>You will see the name <strong>{appName}</strong>. Tap <strong>Add</strong> in the top right corner.</p>
            </Step>
            <Step number={4} title="Open it from your home screen" picture={<HomeScreenStep appName={appName} />}>
                <p>The <strong>{appName}</strong> icon is now on your home screen, like any other app. Tap it whenever you want to practice.</p>
            </Step>
        </ol>
    </section>
);

const AndroidSteps = ({ appName }) => (
    <section className="tcc-section" id="android">
        <h2>Android phones and tablets</h2>
        <p>Use the <strong>Chrome</strong> app.</p>
        <ol className="tcc-steps">
            <Step number={1} title="Tap the menu button" picture={<AndroidMenuStep />}>
                <p>Look at the top right corner of the screen. Tap the button with <strong>three dots</strong>.</p>
            </Step>
            <Step number={2} title={'Tap "Add to Home screen" or "Install app"'} picture={<AndroidAddStep />}>
                <p>A menu opens. Tap <strong>Add to Home screen</strong>. On some phones it is called <strong>Install app</strong>.</p>
            </Step>
            <Step number={3} title={'Tap "Install" or "Add"'} picture={<ConfirmStep appName={appName} button="Install" />}>
                <p>A box shows the name <strong>{appName}</strong>. Tap <strong>Install</strong> (or <strong>Add</strong>).</p>
            </Step>
            <Step number={4} title="Open it from your home screen" picture={<HomeScreenStep appName={appName} />}>
                <p>The <strong>{appName}</strong> icon is now on your home screen. Tap it whenever you want to practice.</p>
            </Step>
        </ol>
    </section>
);

const AddToPhone = () => {
    const { settings } = useTcc();
    const { canInstall, install } = useInstallPrompt();
    const [installed, setInstalled] = useState(false);
    const device = detectDevice();
    const appName = settings.app_name;

    if (isRunningAsApp()) {
        return (
            <div className="tcc-page tcc-narrow">
                <h1>Add to your phone</h1>
                <p className="tcc-success">You are already using the {appName} app. There is nothing else to do.</p>
                <Link to="/tai-chi-company/library" className="custom-btn1 tcc-btn">Go to the Library</Link>
            </div>
        );
    }

    const iphoneFirst = device !== "android";
    return (
        <div className="tcc-page">
            <h1>Add {appName} to your phone</h1>
            <p className="tcc-lead">
                Put an icon on your phone or tablet's home screen, so you can open {appName} with one tap,
                just like any other app. It is free and takes less than a minute. Nothing is downloaded from an app store.
            </p>

            {canInstall && !installed && (
                <div className="tcc-notice tcc-section">
                    <p><strong>Your phone can do this for you.</strong> Tap the button below, then tap <strong>Install</strong>.</p>
                    <button type="button" className="custom-btn1 tcc-btn tcc-btn-big"
                        onClick={async () => setInstalled(await install())}>
                        Add to my home screen
                    </button>
                </div>
            )}
            {installed && <p className="tcc-success" role="status">Done! Look for the {appName} icon on your home screen.</p>}

            <p>
                Jump to: <a href="#iphone" className="tcc-text-link">iPhone and iPad</a>
                {" · "}
                <a href="#android" className="tcc-text-link">Android</a>
            </p>

            {iphoneFirst ? <IphoneSteps appName={appName} /> : <AndroidSteps appName={appName} />}
            {iphoneFirst ? <AndroidSteps appName={appName} /> : <IphoneSteps appName={appName} />}

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
