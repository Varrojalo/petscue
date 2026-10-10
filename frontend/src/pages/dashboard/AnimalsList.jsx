import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";

import { getAnimals } from "../../api/dashboard";
import Button from "../../components/Button";
import Icon from "../../components/Icon";
import { Empty, ErrorMessage, Loading } from "../../components/PageState";
import Photo from "../../components/Photo";
import { age } from "../../lib/format";
import page from "./Dashboard.module.css";
import styles from "./Animals.module.css";

const FILTERS = [
  ["", "Todos"], ["available", "Disponibles"], ["foster", "En acogida"], ["treatment", "En tratamiento"],
  ["adopted", "Adoptados"], ["exited", "Salidas"],
];

export default function AnimalsList() {
  const [params, setParams] = useSearchParams();
  const status = params.get("estado") || "";
  const [search, setSearch] = useState(params.get("buscar") || "");
  const [state, setState] = useState({ items: [], count: 0, page: 1, loading: true, error: null });

  const load = (pageNumber, append) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    getAnimals({ status, q: params.get("buscar") || "", page: pageNumber })
      .then((data) => setState((s) => ({ items: append ? [...s.items, ...data.items] : data.items, count: data.count, page: pageNumber, loading: false, error: null })))
      .catch((error) => setState((s) => ({ ...s, loading: false, error })));
  };

  useEffect(() => {
    load(1, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  const update = (changes) => {
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    setParams(next, { replace: true });
  };

  return (
    <>
      <div className={page.head}>
        <div>
          <h1>Animales</h1>
          <p className={page.muted}>Los adoptados y las salidas no se muestran en la web, pero se conservan con su historial.</p>
        </div>
        <Button to="/dashboard/animales/nuevo"><Icon name="plus" /> Añadir animal</Button>
      </div>

      <div className={styles.toolbar}>
        <div className={styles.chips} role="group" aria-label="Estado">
          {FILTERS.map(([value, label]) => (
            <button key={value} type="button" className={styles.chip} aria-pressed={status === value} onClick={() => update({ estado: value })}>{label}</button>
          ))}
        </div>
        <form className={styles.search} role="search" onSubmit={(e) => { e.preventDefault(); update({ buscar: search.trim() }); }}>
          <label className="sr-only" htmlFor="animal-search">Buscar por nombre o microchip</label>
          <input id="animal-search" type="search" placeholder="Buscar por nombre o microchip" value={search} onChange={(e) => setSearch(e.target.value)} />
          <Button type="submit" variant="ghost" size="small"><Icon name="search" /> Buscar</Button>
        </form>
      </div>

      {state.error && <ErrorMessage error={state.error} />}
      {!state.error && state.loading && state.items.length === 0 && <Loading />}
      {!state.error && !state.loading && state.items.length === 0 && (
        <Empty title="No hay animales en esta vista">
          <p>Cambia el filtro o añade un animal.</p>
        </Empty>
      )}
      {state.items.length > 0 && (
        <section className={page.panel}>
          <p className={page.muted} aria-live="polite">{state.count} {state.count === 1 ? "animal" : "animales"}</p>
          <ul className={styles.rows}>
            {state.items.map((a) => (
              <li key={a.id} className={styles.row}>
                <span className={styles.thumb}><Photo photo={a.cover} seed={a.id} alt={`Foto de ${a.name}`} /></span>
                <div className={styles.info}>
                  <strong>
                    {a.name}
                    {a.featured && <span className={styles.featured}><Icon name="star" size="0.9em" /> Portada</span>}
                  </strong>
                  <span className={styles.meta}>
                    {a.species.name} · {age(a.age_months)}
                    <span><Icon name="eye" size="1em" /> {a.visits_last_30_days} visitas</span>
                    <span><Icon name="clock" size="1em" /> {a.days_in_organization} días</span>
                  </span>
                  <span className={styles.meta}>
                    <span className={`${styles.status} ${styles[a.status_code]}`}>{a.status}</span>
                    {a.returns_count > 0 && <span className={styles.returns}><Icon name="undo" size="1em" /> Devuelto {a.returns_count} {a.returns_count === 1 ? "vez" : "veces"}</span>}
                    {a.foster_home && <span>Acogida: {a.foster_home}</span>}
                  </span>
                </div>
                <Link to={`/dashboard/animales/${a.id}`} className={styles.open}><Icon name="edit" /> Ver y editar</Link>
              </li>
            ))}
          </ul>
          {state.items.length < state.count && (
            <Button variant="ghost" onClick={() => load(state.page + 1, true)} disabled={state.loading}>
              {state.loading ? "Cargando…" : "Ver más"}
            </Button>
          )}
        </section>
      )}
    </>
  );
}
