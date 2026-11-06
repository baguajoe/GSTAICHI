import React from "react";
import { LegalPage, HealthDisclaimerText } from "../../component/tai-chi-company/legal";

const HealthDisclaimer = () => (
    <LegalPage title="Health Disclaimer" sections={[{ heading: "Before you practice", body: <HealthDisclaimerText /> }]} />
);

export default HealthDisclaimer;
