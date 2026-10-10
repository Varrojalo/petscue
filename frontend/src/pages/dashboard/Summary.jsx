import { getSummary } from "../../api/dashboard";
import { useAuth } from "../../auth/AuthProvider";
import { ErrorMessage, Loading } from "../../components/PageState";
import VisitsChart from "../../components/VisitsChart";
import { useApi } from "../../lib/useApi";
import styles from "./Dashboard.module.css";

function today() {
  const text = new Date().toLocaleDateString("es-CL", { weekday: "long", day: "numeric", month: "long" });
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export default function Summary() {
  const { user } = useAuth();
  const { data, error, loading } = useApi(getSummary);
  if (loading) return <Loading />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <>
      <div className={styles.head}>
        <p className={styles.eyebrow}>{today()}</p>
        <h1>Hola, {user.name.split(" ")[0]}</h1>
      </div>

      <div className={styles.kpis}>
        <div className={styles.kpi}>
          <b>{data.animals_in_care}</b>
          <span>Animales a cargo</span>
          <small>{data.in_foster_homes} en casa de acogida</small>
        </div>
        <div className={`${styles.kpi} ${data.new_adoption_requests ? styles.alert : ""}`}>
          <b>{data.new_adoption_requests}</b>
          <span>Solicitudes nuevas</span>
          <small>{data.new_adoption_requests ? "Por revisar" : "Todo al día"}</small>
        </div>
        <div className={styles.kpi}>
          <b>{data.adoptions_this_year}</b>
          <span>Adopciones este año</span>
          <small>Contratos firmados</small>
        </div>
        <div className={styles.kpi}>
          <b>{data.active_members}</b>
          <span>Socios activos</span>
          <small>Incluye padrinos</small>
        </div>
      </div>

      <div className={styles.split}>
        <section className={styles.panel}>
          <div className={styles.panelHead}>
            <h2>Visitas y tiempo en la fundación</h2>
            <p>Visitas de los últimos 30 días a cada ficha, junto al tiempo que lleva cada animal con ustedes.</p>
          </div>
          <VisitsChart rows={data.visits_chart} />
        </section>
        <section className={styles.panel}>
          <div className={styles.panelHead}>
            <h2>Últimas solicitudes de adopción</h2>
          </div>
          {data.recent_requests.length === 0 ? (
            <p className={styles.muted}>Todavía no llegan solicitudes.</p>
          ) : (
            <ul className={styles.list}>
              {data.recent_requests.map((r) => (
                <li key={r.id}>
                  <b>{r.person}</b>
                  <span>Quiere adoptar a {r.animal} · {r.status}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </>
  );
}
