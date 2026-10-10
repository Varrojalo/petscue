import { useState } from "react";
import { Link } from "react-router";

import { niceMax, ticks } from "../lib/scale";
import styles from "./VisitsChart.module.css";

const ORDERS = {
  most: ["Más vistos", (a, b) => b.visits_last_30_days - a.visits_last_30_days],
  least: ["Menos vistos", (a, b) => a.visits_last_30_days - b.visits_last_30_days],
  longest: ["Más tiempo", (a, b) => b.days_in_organization - a.days_in_organization],
};
const VISIBLE = 10;

function timeLabel(days) {
  if (days < 30) return `${days} ${days === 1 ? "día" : "días"}`;
  const months = Math.floor(days / 30.4);
  if (months < 12) return `${months} ${months === 1 ? "mes" : "meses"}`;
  const years = Math.floor(months / 12);
  const rest = months % 12;
  return `${years} ${years === 1 ? "año" : "años"}${rest ? ` ${rest} m` : ""}`;
}

/**
 * Visits in the last 30 days next to the time each animal has been in the organization.
 * Drawn with plain elements so text grows with the "Aa" button and colors follow the theme.
 */
export default function VisitsChart({ rows }) {
  const [order, setOrder] = useState("most");
  const [all, setAll] = useState(false);
  const sorted = [...rows].sort(ORDERS[order][1]);
  const shown = all ? sorted : sorted.slice(0, VISIBLE);
  const maxVisits = niceMax(Math.max(0, ...rows.map((r) => r.visits_last_30_days)));
  const maxDays = niceMax(Math.max(0, ...rows.map((r) => r.days_in_organization)));

  if (rows.length === 0) return <p className={styles.empty}>Todavía no hay animales a cargo de la fundación.</p>;

  return (
    <div className={styles.chart}>
      <div className={styles.orders} role="group" aria-label="Ordenar">
        {Object.entries(ORDERS).map(([key, [label]]) => (
          <button key={key} type="button" aria-pressed={order === key} onClick={() => setOrder(key)}>{label}</button>
        ))}
      </div>
      <ul className={styles.rows}>
        {shown.map((row) => (
          <li key={row.animal_id} className={styles.row}>
            <Link to={`/dashboard/animales/${row.animal_id}`} className={styles.name}>{row.name}</Link>
            <span className={styles.bars} aria-hidden="true">
              <span className={styles.track}><span className={styles.visits} style={{ width: `${(row.visits_last_30_days / maxVisits) * 100}%` }} /></span>
              <span className={`${styles.track} ${styles.thin}`}><span className={styles.time} style={{ width: `${(row.days_in_organization / maxDays) * 100}%` }} /></span>
            </span>
            <span className={styles.values}>
              <b>{row.visits_last_30_days.toLocaleString("es-CL")}</b> visitas
              <small>{timeLabel(row.days_in_organization)}</small>
            </span>
          </li>
        ))}
      </ul>
      {rows.length > VISIBLE && (
        <button type="button" className={styles.toggle} onClick={() => setAll(!all)}>
          {all ? "Ver menos" : `Ver los ${rows.length} animales`}
        </button>
      )}
      <div className={styles.legend}>
        <span><i className={styles.visits} /> Visitas (escala de {ticks(maxVisits).map((t) => t.toLocaleString("es-CL")).join(" · ")})</span>
        <span><i className={styles.time} /> Tiempo en la fundación (hasta {timeLabel(maxDays)})</span>
      </div>
    </div>
  );
}
