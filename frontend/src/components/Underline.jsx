import styles from "./Underline.module.css";

/** The hand-drawn yellow stroke that highlights the featured animal's name (the only illustration of the design). */
export default function Underline({ children }) {
  return (
    <span className={styles.wrap}>
      {children}
      <svg viewBox="0 0 220 20" preserveAspectRatio="none" aria-hidden="true">
        <path d="M4 13 C 60 4, 150 4, 216 11" />
      </svg>
    </span>
  );
}
