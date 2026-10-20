import React from "react";
import { useTcc } from "../../component/tai-chi-company/TccContext";
import { toParagraphs } from "../../component/tai-chi-company/api";

const Terms = () => {
    const { settings } = useTcc();
    const paragraphs = toParagraphs(settings.terms_of_service_text);
    return (
        <div className="tcc-page tcc-narrow">
            <h1>Terms of Use</h1>
            {paragraphs.length > 0
                ? <div className="tcc-terms">{paragraphs.map((p, i) => <p key={i}>{p}</p>)}</div>
                : <p>The terms of use have not been added yet.</p>}
        </div>
    );
};

export default Terms;
