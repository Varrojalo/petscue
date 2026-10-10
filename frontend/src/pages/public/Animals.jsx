import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";

import { getAnimals } from "../../api/public";
import Button from "../../components/Button";
import { Select } from "../../components/Form";
import { Empty, ErrorMessage, Loading } from "../../components/PageState";
import PetCard from "../../components/PetCard";
import { useOrganization } from "../../organization/OrganizationProvider";
import styles from "./Animals.module.css";

const SIZES = [["small", "Pequeño"], ["medium", "Mediano"], ["large", "Grande"]];

export default function Animals() {
  const { organization } = useOrganization();
  const [params, setParams] = useSearchParams();
  const filters = { species: params.get("especie") || "", size: params.get("tamano") || "", life_stage: params.get("etapa") || "" };
  const [pages, setPages] = useState({ items: [], count: 0, page: 1, loading: true, error: null });

  const key = `${filters.species}|${filters.size}|${filters.life_stage}`;
  useEffect(() => {
    setPages({ items: [], count: 0, page: 1, loading: true, error: null });
    getAnimals({ ...filters, page: 1 })
      .then((data) => setPages({ items: data.items, count: data.count, page: 1, loading: false, error: null }))
      .catch((error) => setPages((p) => ({ ...p, loading: false, error })));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const loadMore = () => {
    const next = pages.page + 1;
    setPages((p) => ({ ...p, loading: true }));
    getAnimals({ ...filters, page: next })
      .then((data) => setPages((p) => ({ ...p, items: [...p.items, ...data.items], page: next, loading: false })))
      .catch((error) => setPages((p) => ({ ...p, loading: false, error })));
  };

  const update = (changes) => {
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    setParams(next, { replace: true });
  };

  const species = organization?.species || [];
  const selectedSpecies = species.find((s) => String(s.id) === filters.species);

  return (
    <>
      <div className={styles.head}>
        <h1>Buscan familia</h1>
        <p className={styles.muted}>Toca a cualquiera para conocer su historia y pedir la adopción.</p>
      </div>

      <div className={styles.filters}>
        <div className={styles.chips} role="group" aria-label="Especie">
          <button type="button" className={styles.chip} aria-pressed={!filters.species} onClick={() => update({ especie: "", etapa: "" })}>Todos</button>
          {species.map((s) => (
            <button key={s.id} type="button" className={styles.chip} aria-pressed={filters.species === String(s.id)} onClick={() => update({ especie: String(s.id), etapa: "" })}>
              {s.plural_name}
            </button>
          ))}
        </div>
        <div className={styles.selects}>
          <Select label="Tamaño" value={filters.size} onChange={(e) => update({ tamano: e.target.value })}>
            <option value="">Cualquier tamaño</option>
            {SIZES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </Select>
          <Select
            label="Edad"
            value={filters.life_stage}
            onChange={(e) => update({ etapa: e.target.value })}
            disabled={!selectedSpecies}
            hint={selectedSpecies ? undefined : "Elige primero una especie"}
          >
            <option value="">Cualquier edad</option>
            {(selectedSpecies?.life_stages || []).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </Select>
        </div>
      </div>

      {pages.error && <ErrorMessage error={pages.error} />}
      {!pages.error && pages.loading && pages.items.length === 0 && <Loading />}
      {!pages.error && !pages.loading && pages.items.length === 0 && (
        <Empty title="No hay animales con esos filtros">
          <Button variant="ghost" onClick={() => setParams({}, { replace: true })}>Quitar filtros</Button>
        </Empty>
      )}
      {pages.items.length > 0 && (
        <>
          <p className={styles.count} aria-live="polite">{pages.count} {pages.count === 1 ? "animal" : "animales"}</p>
          <div className={styles.grid}>
            {pages.items.map((animal) => <PetCard key={animal.id} animal={animal} />)}
          </div>
          {pages.items.length < pages.count && (
            <Button variant="ghost" onClick={loadMore} disabled={pages.loading} className={styles.more}>
              {pages.loading ? "Cargando…" : "Ver más animales"}
            </Button>
          )}
        </>
      )}
    </>
  );
}
