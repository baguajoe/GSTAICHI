import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useTcc, HELP_EMAIL } from "../../component/tai-chi-company/TccContext";
import { useInstallPrompt, installGuide } from "../../component/tai-chi-company/homeScreenApp";
import {
    GuideSteps, BookmarkNote, orderedGuides
} from "../../component/tai-chi-company/InstallApp";

const AddToPhone = () => {
    const { settings } = useTcc();
    const { canInstall, installed, install } = useInstallPrompt();
    const [justInstalled, setJustInstalled] = useState(false);
    const guides = orderedGuides(installGuide());
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

    return (
        <div className="tcc-page">
            <h1>Install {appName} on your phone or computer</h1>
            <p className="tcc-lead">
                Put an icon on your home screen (or your computer's desktop), so you can open {appName} with one tap,
                just like any other app. It is free and takes less than a minute. Nothing is downloaded from an app store.
            </p>
            <BookmarkNote />

            {canInstall && !justInstalled && (
                <div className="tcc-notice tcc-section">
                    <p><strong>Your browser can do this for you.</strong> Tap the button below, then tap <strong>Install</strong>.</p>
                    <button type="button" className="custom-btn1 tcc-btn tcc-btn-big"
                        onClick={async () => setJustInstalled(await install())}>
                        Install the app
                    </button>
                </div>
            )}
            {justInstalled && <p className="tcc-success" role="status">Done! Look for the {appName} icon on your home screen, or on a computer in your Dock, desktop or Start menu.</p>}

            <p>
                Jump to:{" "}
                {guides.map((g, i) => (
                    <React.Fragment key={g.key}>
                        {i > 0 && " · "}
                        <a href={`#${g.key}`} className="tcc-text-link">{g.title}</a>
                    </React.Fragment>
                ))}
            </p>

            {guides.map((g, i) => (
                <section className="tcc-section" id={g.key} key={g.key}>
                    <h2>{g.title}{i === 0 && <span className="tcc-your-device"> (this device)</span>}</h2>
                    <GuideSteps guide={g.key} appName={appName} thisDevice={i === 0} />
                </section>
            ))}

            <section className="tcc-section tcc-notice">
                <h2>Need a hand?</h2>
                <p>
                    Email Vincent at <a href={`mailto:${HELP_EMAIL}`}>{HELP_EMAIL}</a> and
                    we will walk you through it, step by step.
                </p>
            </section>
        </div>
    );
};

export default AddToPhone;
