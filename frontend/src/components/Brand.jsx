import { useBigText } from "../lib/useBigText";
import styles from "./Brand.module.css";

export function Logo({ organization }) {
  const initial = (organization?.name || "P").replace(/^(Fundación|Asociación|Agrupación|ONG)\s+/i, "")[0]?.toUpperCase();
  return (
    <span className={styles.logo}>
      {organization?.logo_url ? <img src={organization.logo_url} alt="" /> : initial}
    </span>
  );
}

export function BigTextButton() {
  const [big, setBig] = useBigText();
  return (
    <button type="button" className={styles.bigText} aria-pressed={big} onClick={() => setBig(!big)} title="Letra más grande">
      Aa<span className="sr-only"> · letra más grande</span>
    </button>
  );
}
