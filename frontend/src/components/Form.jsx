import { useId } from "react";

import styles from "./Form.module.css";

/** Label, optional hint and the error message right under the field, as the backend sends it. */
export function Field({ label, hint, error, optional, children, id }) {
  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={id}>
        {label} {optional && <small className={styles.optional}>(opcional)</small>}
      </label>
      {children}
      {hint && !error && <small className={styles.hint}>{hint}</small>}
      {error && <small className={styles.error} role="alert">{error}</small>}
    </div>
  );
}

export function TextInput({ label, hint, error, optional, multiline, ...props }) {
  const id = useId();
  const Tag = multiline ? "textarea" : "input";
  return (
    <Field label={label} hint={hint} error={error} optional={optional} id={id}>
      <Tag id={id} className={`${styles.input} ${error ? styles.invalid : ""}`} aria-invalid={!!error} rows={multiline ? 3 : undefined} {...props} />
    </Field>
  );
}

export function Select({ label, hint, error, optional, children, ...props }) {
  const id = useId();
  return (
    <Field label={label} hint={hint} error={error} optional={optional} id={id}>
      <select id={id} className={`${styles.input} ${error ? styles.invalid : ""}`} aria-invalid={!!error} {...props}>
        {children}
      </select>
    </Field>
  );
}

/** Big tappable options. `multiple` uses checkboxes instead of radio buttons. */
export function Choices({ legend, name, options, value, onChange, multiple = false, error }) {
  const selected = multiple ? value || [] : value;
  const toggle = (option) => {
    if (!multiple) return onChange(option);
    onChange(selected.includes(option) ? selected.filter((v) => v !== option) : [...selected, option]);
  };
  return (
    <fieldset className={styles.fieldset}>
      <legend className={styles.label}>{legend}</legend>
      <div className={styles.chips}>
        {options.map(([optionValue, optionLabel]) => (
          <label key={optionValue} className={styles.chip}>
            <input
              type={multiple ? "checkbox" : "radio"}
              name={name}
              checked={multiple ? selected.includes(optionValue) : selected === optionValue}
              onChange={() => toggle(optionValue)}
            />
            {optionLabel}
          </label>
        ))}
      </div>
      {error && <small className={styles.error} role="alert">{error}</small>}
    </fieldset>
  );
}

export function Checkbox({ label, checked, onChange, error }) {
  return (
    <div>
      <label className={styles.check}>
        <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
        <span>{label}</span>
      </label>
      {error && <small className={styles.error} role="alert">{error}</small>}
    </div>
  );
}

export function FormError({ message }) {
  if (!message) return null;
  return <p className={styles.formError} role="alert">{message}</p>;
}

export function Note({ children }) {
  return <p className={styles.note}>{children}</p>;
}

export const formStyles = styles;
