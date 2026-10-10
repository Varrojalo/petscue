import Button from "./Button";
import styles from "./PageState.module.css";

export function Loading({ label = "Cargando…" }) {
  return <p className={styles.loading} aria-live="polite">{label}</p>;
}

export function ErrorMessage({ error, title = "No pudimos cargar esta página" }) {
  return (
    <div className={styles.box} role="alert">
      <h2>{title}</h2>
      <p>{error?.detail || error?.message || "Intenta de nuevo en unos minutos."}</p>
      <Button variant="ghost" onClick={() => window.location.reload()}>Intentar de nuevo</Button>
    </div>
  );
}

export function Empty({ title, children }) {
  return (
    <div className={styles.box}>
      <h2>{title}</h2>
      {children}
    </div>
  );
}
