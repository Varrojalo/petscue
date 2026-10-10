import { Link } from "react-router";

import { age } from "../lib/format";
import styles from "./PetCard.module.css";
import Photo from "./Photo";

export default function PetCard({ animal }) {
  return (
    <Link to={`/animales/${animal.slug}`} className={styles.card}>
      <span className={styles.photo}>
        <Photo photo={animal.cover} seed={animal.id} alt={`Foto de ${animal.name}`} />
        {animal.in_foster_home && <span className={styles.tag}>En casa de acogida</span>}
        {!animal.in_foster_home && animal.in_treatment && <span className={`${styles.tag} ${styles.treatment}`}>En tratamiento</span>}
      </span>
      <span className={styles.name}>{animal.name}</span>
      <span className={styles.meta}>{animal.sex} · {age(animal.age_months)} · {animal.size}</span>
    </Link>
  );
}
