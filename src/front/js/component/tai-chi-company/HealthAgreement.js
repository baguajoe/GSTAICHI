import React, { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useTcc } from "./TccContext";
import { apiFetch } from "./api";
import Overlay from "./Overlay";
import { HealthDisclaimerText, isLegalPage } from "./legal";

// Shown once to a signed-in member who has not agreed yet (members who joined before sign-up asked).
// It stays hidden on the Terms, Privacy, Refunds and Health pages so they can be read first.
const HealthAgreement = () => {
    const { user, setUser, logout } = useTcc();
    const location = useLocation();
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState(null);
    const box = useRef(null);
    const show = !!user && !user.agreed_terms_at && !isLegalPage(location.pathname);

    useEffect(() => {
        if (show && box.current) {
            const first = box.current.querySelector("button");
            if (first) first.focus();
        }
    }, [show]);

    if (!show) return null;

    const agree = async () => {
        setBusy(true);
        setError(null);
        try {
            const result = await apiFetch("/api/tcc/agree-terms", { method: "POST" });
            setUser(result.user);
        } catch (e) {
            setError(e.message);
        }
        setBusy(false);
    };

    return (
        <Overlay>
            <div className="tcc-dialog-backdrop">
                <div className="tcc-dialog tcc-health-dialog" role="dialog" aria-modal="true" aria-labelledby="tcc-health-title" ref={box}>
                    <h2 id="tcc-health-title">Before you practice</h2>
                    <HealthDisclaimerText />
                    <p>
                        By pressing "I agree" you confirm that you have read this health disclaimer and agree to
                        the <Link to="/tai-chi-company/terms">Terms of Use</Link>.
                        {" "}See also our <Link to="/tai-chi-company/privacy">Privacy Policy</Link>.
                    </p>
                    {error && <p className="tcc-error" role="alert">{error}</p>}
                    <div className="tcc-button-row">
                        <button type="button" className="custom-btn1 tcc-btn tcc-btn-big" disabled={busy} onClick={agree}>
                            {busy ? "Saving…" : "I agree"}
                        </button>
                        <button type="button" className="tcc-btn tcc-btn-outline" onClick={logout}>Log out</button>
                    </div>
                </div>
            </div>
        </Overlay>
    );
};

export default HealthAgreement;
