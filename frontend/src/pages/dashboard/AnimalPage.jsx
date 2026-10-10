import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import * as api from "../../api/dashboard";
import Button from "../../components/Button";
import { Checkbox, Choices, FormError, Select, TextInput, formStyles } from "../../components/Form";
import Icon from "../../components/Icon";
import { ErrorMessage, Loading } from "../../components/PageState";
import Photo from "../../components/Photo";
import { money } from "../../lib/format";
import { useApi, useSubmit } from "../../lib/useApi";
import page from "./Dashboard.module.css";
import styles from "./AnimalPage.module.css";

const SEX = [["female", "Hembra"], ["male", "Macho"], ["unknown", "Desconocido"]];
const SIZE = [["small", "Pequeño"], ["medium", "Mediano"], ["large", "Grande"]];
const IN_CARE = ["available", "foster", "treatment"];
const todayISO = () => new Date().toISOString().slice(0, 10);

const blank = {
  name: "", species_id: "", sex: "unknown", size: "medium", birth_date_approx: "", intake_date: todayISO(), in_treatment: false,
  quote: "", story: "", vaccinated: false, sterilized: false, microchip_number: "", sponsorship_amount: 0, trait_ids: [],
};

function fromAnimal(a) {
  return {
    name: a.name, species_id: String(a.species.id), sex: a.sex_code, size: a.size_code, birth_date_approx: a.birth_date_approx,
    intake_date: a.intake_date, in_treatment: a.in_treatment, quote: a.quote, story: a.story, vaccinated: a.vaccinated,
    sterilized: a.sterilized, microchip_number: a.microchip_number, sponsorship_amount: a.sponsorship_amount, trait_ids: a.trait_ids,
  };
}

/** Name, health and story of the animal. Used both to add a new one and to edit it. */
function AnimalForm({ animal, onSaved }) {
  const species = useApi(api.getSpecies);
  const [traits, setTraits] = useState([]);
  const [newTrait, setNewTrait] = useState("");
  const [form, setForm] = useState(animal ? fromAnimal(animal) : blank);
  const [saved, setSaved] = useState(false);
  const [submit, { sending, error, fieldErrors }] = useSubmit((data) => (animal ? api.updateAnimal(animal.id, data) : api.createAnimal(data)));

  useEffect(() => {
    api.getTraits().then(setTraits).catch(() => {});
  }, []);

  const set = (key) => (event) => setForm({ ...form, [key]: event.target.value });
  const options = (species.data || []).filter((s) => s.is_active || String(s.id) === form.species_id);

  const addTrait = async () => {
    const label = newTrait.trim();
    if (!label) return;
    const existing = traits.find((t) => t.label.toLowerCase() === label.toLowerCase());
    const trait = existing || (await api.createTrait(label).catch(() => null));
    if (!trait) return;
    if (!existing) setTraits([...traits, trait]);
    setForm((f) => ({ ...f, trait_ids: f.trait_ids.includes(trait.id) ? f.trait_ids : [...f.trait_ids, trait.id] }));
    setNewTrait("");
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setSaved(false);
    const result = await submit({
      ...form, species_id: Number(form.species_id) || 0, sponsorship_amount: Number(form.sponsorship_amount) || 0,
    });
    if (result) {
      setSaved(true);
      onSaved(result);
    }
  };

  return (
    <form className={`${formStyles.form} ${page.panel}`} onSubmit={onSubmit} noValidate>
      <h2 className={styles.sectionTitle}>Datos del animal</h2>
      <div className={formStyles.row}>
        <TextInput label="Nombre" value={form.name} onChange={set("name")} error={fieldErrors.name} />
        <Select label="Especie" value={form.species_id} onChange={set("species_id")} error={fieldErrors.species_id}>
          <option value="">Elige la especie</option>
          {options.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </Select>
      </div>
      <Choices legend="Sexo" name="sex" options={SEX} value={form.sex} onChange={(sex) => setForm({ ...form, sex })} />
      <Choices legend="Tamaño" name="size" options={SIZE} value={form.size} onChange={(size) => setForm({ ...form, size })} />
      <div className={formStyles.row}>
        <TextInput label="Fecha de nacimiento aproximada" type="date" max={todayISO()} value={form.birth_date_approx} onChange={set("birth_date_approx")} error={fieldErrors.birth_date_approx} hint="Si no la sabes, una aproximación sirve: la edad se calcula sola" />
        <TextInput label="Llegó a la fundación el" type="date" max={todayISO()} value={form.intake_date} onChange={set("intake_date")} error={fieldErrors.intake_date} />
      </div>
      <div className={styles.checks}>
        <Checkbox label="Vacunas al día" checked={form.vaccinated} onChange={(vaccinated) => setForm({ ...form, vaccinated })} />
        <Checkbox label="Esterilizado" checked={form.sterilized} onChange={(sterilized) => setForm({ ...form, sterilized })} />
        <Checkbox label="En tratamiento veterinario" checked={form.in_treatment} onChange={(in_treatment) => setForm({ ...form, in_treatment })} />
      </div>
      <div className={formStyles.row}>
        <TextInput label="Número de microchip" optional value={form.microchip_number} onChange={set("microchip_number")} error={fieldErrors.microchip_number} />
        <TextInput label="Padrinazgo mensual" type="number" min="0" step="500" inputMode="numeric" value={form.sponsorship_amount} onChange={set("sponsorship_amount")} error={fieldErrors.sponsorship_amount} hint={`Se muestra en la ficha: ${money(form.sponsorship_amount)} al mes. 0 = sin padrinazgo`} />
      </div>
      <TextInput label="Frase destacada" optional value={form.quote} onChange={set("quote")} error={fieldErrors.quote} hint="Una frase corta que lo describa, aparece grande en la ficha" />
      <TextInput label="Su historia" optional multiline value={form.story} onChange={set("story")} error={fieldErrors.story} />
      <div className={formStyles.fieldset}>
        <span className={formStyles.label}>Rasgos</span>
        <div className={formStyles.chips}>
          {traits.map((t) => (
            <label key={t.id} className={formStyles.chip}>
              <input
                type="checkbox"
                checked={form.trait_ids.includes(t.id)}
                onChange={() => setForm((f) => ({ ...f, trait_ids: f.trait_ids.includes(t.id) ? f.trait_ids.filter((id) => id !== t.id) : [...f.trait_ids, t.id] }))}
              />
              {t.label}
            </label>
          ))}
        </div>
        <div className={styles.inline}>
          <input className={formStyles.input} placeholder="Nuevo rasgo, por ejemplo: Le gusta el agua" value={newTrait} onChange={(e) => setNewTrait(e.target.value)} aria-label="Nuevo rasgo" />
          <Button variant="ghost" size="small" onClick={addTrait}><Icon name="plus" /> Agregar</Button>
        </div>
      </div>
      <FormError message={error} />
      {saved && <p className={styles.ok} role="status"><Icon name="check" /> Cambios guardados</p>}
      <Button type="submit" disabled={sending}>{sending ? "Guardando…" : animal ? "Guardar cambios" : "Crear y seguir con las fotos"}</Button>
    </form>
  );
}

/** Upload, order (the first one is the main photo) and delete photos. */
function Photos({ animal, onChange }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [confirm, setConfirm] = useState(null);
  const photos = animal.photos;

  const run = async (task) => {
    setBusy(true);
    setError(null);
    try {
      await task();
      onChange();
    } catch (e) {
      setError(e.detail || e.message);
    } finally {
      setBusy(false);
      setConfirm(null);
    }
  };

  const upload = (files) => run(async () => {
    for (const file of files) await api.uploadPhoto(animal.id, file);
  });
  const move = (index, step) => run(() => {
    const ids = photos.map((p) => p.id);
    [ids[index], ids[index + step]] = [ids[index + step], ids[index]];
    return api.reorderPhotos(animal.id, ids);
  });

  return (
    <section className={page.panel}>
      <h2 className={styles.sectionTitle}>Fotos</h2>
      <p className={page.muted}>La primera es la foto principal en la web. Usa las flechas para cambiar el orden.</p>
      {photos.length > 0 && (
        <ol className={styles.photos}>
          {photos.map((p, i) => (
            <li key={p.id}>
              <span className={styles.photo}><Photo photo={p} seed={animal.id} alt={`Foto ${i + 1} de ${animal.name}`} /></span>
              {i === 0 && <span className={styles.main}>Principal</span>}
              <span className={styles.photoActions}>
                <button type="button" disabled={busy || i === 0} onClick={() => move(i, -1)} aria-label="Mover antes"><Icon name="up" /></button>
                <button type="button" disabled={busy || i === photos.length - 1} onClick={() => move(i, 1)} aria-label="Mover después"><Icon name="down" /></button>
                {confirm === p.id ? (
                  <button type="button" className={styles.danger} disabled={busy} onClick={() => run(() => api.deletePhoto(animal.id, p.id))}>¿Borrar?</button>
                ) : (
                  <button type="button" disabled={busy} onClick={() => setConfirm(p.id)} aria-label="Borrar foto"><Icon name="trash" /></button>
                )}
              </span>
            </li>
          ))}
        </ol>
      )}
      <label className={styles.upload}>
        <Icon name="camera" size="28" />
        <span><b>{busy ? "Subiendo…" : "Subir fotos"}</b><small>JPG, PNG o WEBP. Puedes elegir varias a la vez</small></span>
        <input type="file" accept="image/jpeg,image/png,image/webp" multiple className="sr-only" disabled={busy} onChange={(e) => upload([...e.target.files])} />
      </label>
      <FormError message={error} />
    </section>
  );
}

/** Foster home, home-page highlight and exits: only while the animal is in the organization's care. */
function Care({ animal, onChange }) {
  const homes = useApi(api.getFosterHomes);
  const [home, setHome] = useState(animal.foster_home ? String(animal.foster_home.id) : "");
  const [exit, setExit] = useState(null);
  const [act, { sending, error }] = useSubmit(async (task) => {
    await task();
    onChange();
    return true;
  });

  return (
    <section className={page.panel}>
      <h2 className={styles.sectionTitle}>Cuidado y portada</h2>
      <div className={styles.inline}>
        <Select label="Casa de acogida" value={home} onChange={(e) => setHome(e.target.value)} hint="Solo aparecen personas del equipo marcadas como casa de acogida">
          <option value="">En el refugio (sin casa de acogida)</option>
          {(homes.data || []).map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
        </Select>
        <Button variant="ghost" size="small" disabled={sending || home === (animal.foster_home ? String(animal.foster_home.id) : "")} onClick={() => act(() => api.setFosterHome(animal.id, home ? Number(home) : null))}>
          Guardar
        </Button>
      </div>
      <div className={styles.inline}>
        <span>{animal.featured ? `${animal.name} es el protagonista de la portada.` : "Destacarlo lo muestra en grande en la portada de la web."}</span>
        <Button variant={animal.featured ? "ghost" : "accent"} size="small" disabled={sending} onClick={() => act(() => (animal.featured ? api.unfeatureAnimal(animal.id) : api.featureAnimal(animal.id)))}>
          <Icon name="star" /> {animal.featured ? "Quitar de la portada" : "Destacar en la portada"}
        </Button>
      </div>
      {exit ? (
        <div className={formStyles.form}>
          <Choices legend="Motivo de la salida" name="exit-kind" options={[["deceased", "Falleció"], ["transferred", "Trasladado a otra organización"]]} value={exit.kind} onChange={(kind) => setExit({ ...exit, kind })} />
          <TextInput label="Fecha" type="date" max={todayISO()} value={exit.exit_date} onChange={(e) => setExit({ ...exit, exit_date: e.target.value })} />
          <TextInput label="Nota" optional multiline value={exit.notes} onChange={(e) => setExit({ ...exit, notes: e.target.value })} placeholder="Por ejemplo: trasladado a Fundación Huellas del Sur" />
          <div className={styles.inline}>
            <Button disabled={sending} onClick={() => act(() => api.registerExit(animal.id, exit)).then((ok) => ok && setExit(null))}>Registrar salida</Button>
            <Button variant="ghost" onClick={() => setExit(null)}>Cancelar</Button>
          </div>
        </div>
      ) : (
        <div>
          <Button variant="ghost" size="small" onClick={() => setExit({ kind: "deceased", exit_date: todayISO(), notes: "" })}>Registrar salida (fallecimiento o traslado)</Button>
          <p className={page.muted}>La saca de la web, de la casa de acogida y de la portada. No cuenta como adopción.</p>
        </div>
      )}
      <FormError message={error} />
    </section>
  );
}

/** Internal history: adoptions and returns. Never shown on the website. */
function History({ animal, onChange }) {
  const [returning, setReturning] = useState(null);
  const [act, { sending, error, fieldErrors }] = useSubmit(async () => {
    await api.registerReturn(returning.id, { returned_at: returning.returned_at, reason: returning.reason });
    setReturning(null);
    onChange();
    return true;
  });

  return (
    <section className={page.panel}>
      <h2 className={styles.sectionTitle}>Historial interno</h2>
      <p className={page.muted}>Solo lo ve el equipo. Nunca se muestra en la web.</p>
      {animal.exit && (
        <p className={styles.exit}><b>{animal.exit.kind}</b> el {animal.exit.exit_date}. {animal.exit.notes}</p>
      )}
      {animal.adoptions.length === 0 ? (
        <p className={page.muted}>No tiene adopciones registradas.</p>
      ) : (
        <ul className={page.list}>
          {animal.adoptions.map((a) => (
            <li key={a.id}>
              <b>{a.person} · {a.status}</b>
              <span>
                {a.contract_signed_at ? `Contrato: ${a.contract_signed_at}` : "Sin contrato todavía"}
                {a.returned_at ? ` · Devuelto el ${a.returned_at}: ${a.return_reason}` : ""}
              </span>
              {a.status_code === "signed" && returning?.id !== a.id && (
                <Button variant="ghost" size="small" onClick={() => setReturning({ id: a.id, returned_at: todayISO(), reason: "" })}>
                  <Icon name="undo" /> Registrar devolución
                </Button>
              )}
              {returning?.id === a.id && (
                <div className={formStyles.form}>
                  <TextInput label="Fecha de devolución" type="date" max={todayISO()} value={returning.returned_at} onChange={(e) => setReturning({ ...returning, returned_at: e.target.value })} />
                  <TextInput label="¿Por qué lo devolvieron?" multiline value={returning.reason} onChange={(e) => setReturning({ ...returning, reason: e.target.value })} error={fieldErrors.reason} />
                  <div className={styles.inline}>
                    <Button disabled={sending} onClick={() => act()}>Registrar devolución</Button>
                    <Button variant="ghost" onClick={() => setReturning(null)}>Cancelar</Button>
                  </div>
                  <p className={page.muted}>Al registrarla, {animal.name} vuelve a estar a cargo de la fundación y aparece en la web.</p>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
      <FormError message={error} />
    </section>
  );
}

export default function AnimalPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = id === "nuevo";
  const [version, setVersion] = useState(0);
  const { data: animal, error, loading } = useApi(() => (isNew ? Promise.resolve(null) : api.getAnimal(id)), [id, version]);
  const reload = () => setVersion((v) => v + 1);

  if (error) return <ErrorMessage error={error} />;
  // Right after creating, or when switching animals, the data on hand may still be the previous one.
  if (!isNew && (!animal || String(animal.id) !== id)) return <Loading />;

  return (
    <>
      <Link to="/dashboard/animales" className={styles.back}><Icon name="back" /> Volver a animales</Link>
      <div className={page.head}>
        <div>
          <h1>{isNew ? "Añadir animal" : animal.name}</h1>
          {!isNew && <p className={page.muted}>{animal.status} · {animal.visits_last_30_days} visitas en 30 días · {animal.days_in_organization} días con la fundación</p>}
        </div>
        {!isNew && IN_CARE.includes(animal.status_code) && <Button variant="ghost" size="small" to={`/animales/${animal.slug}`}><Icon name="eye" /> Ver en la web</Button>}
      </div>
      <div className={page.split}>
        <AnimalForm key={animal?.id || "new"} animal={animal} onSaved={(saved) => (isNew ? navigate(`/dashboard/animales/${saved.id}`, { replace: true }) : reload())} />
        {!isNew && (
          <div className={styles.side}>
            <Photos animal={animal} onChange={reload} />
            {IN_CARE.includes(animal.status_code) && <Care key={`care-${version}`} animal={animal} onChange={reload} />}
            <History animal={animal} onChange={reload} />
          </div>
        )}
      </div>
    </>
  );
}
