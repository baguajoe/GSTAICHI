import React from "react";

// Large labelled input used by every Tai Chi Company form.
const FormField = ({ id, label, hint, ...inputProps }) => (
    <div className="tcc-field">
        <label htmlFor={id}>{label}</label>
        {hint && <p className="tcc-field-hint" id={`${id}-hint`}>{hint}</p>}
        <input id={id} className="tcc-input" aria-describedby={hint ? `${id}-hint` : undefined} {...inputProps} />
    </div>
);

export const FormMessage = ({ error, success }) => (
    <>
        {error && <p className="tcc-error" role="alert">{error}</p>}
        {success && <p className="tcc-success" role="status">{success}</p>}
    </>
);

export default FormField;
