import styles from "./Photo.module.css";

// Warm tones for animals without photos yet, chosen from the animal's id so each one keeps its own.
const TONES = [
  ["#E7AE72", "#C98A4E", "#A7C79B", "#55855D", "#2F4B39"],
  ["#9A6A48", "#6E4930", "#A9B98E", "#5E6F4B", "#35402C"],
  ["#A7ABB3", "#7C7F86", "#E9D9B8", "#B79B72", "#6D5A42"],
  ["#E9BD84", "#D9A066", "#BFD8E6", "#7EA6BD", "#48667A"],
  ["#3A3A40", "#26262B", "#F1DFC0", "#C9A77A", "#8A6B47"],
];

/** An animal's photo; while there is none, a soft placeholder in the same shape. */
export default function Photo({ photo, seed = 0, alt, large = false, className = "" }) {
  if (photo) {
    return <img className={`${styles.photo} ${className}`} src={large ? photo.url : photo.thumbnail_url} alt={alt} loading="lazy" />;
  }
  const [f1, f2, a, b, c] = TONES[seed % TONES.length];
  return (
    <span className={`${styles.photo} ${styles.placeholder} ${className}`} style={{ "--f1": f1, "--f2": f2, "--a": a, "--b": b, "--c": c }} role="img" aria-label={`${alt} (sin foto todavía)`} />
  );
}
