import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { getAnimal, requestAdoption } from "../../api/public";
import Button from "../../components/Button";
import { Checkbox, Choices, FormError, Note, TextInput, formStyles } from "../../components/Form";
import Icon from "../../components/Icon";
import { ErrorMessage, Loading } from "../../components/PageState";
import PersonFields, { emptyPerson, personPayload } from "../../components/PersonFields";
import Photo from "../../components/Photo";
import { money } from "../../lib/format";
import { useApi, useSubmit } from "../../lib/useApi";
import { useOrganization } from "../../organization/OrganizationProvider";
import styles from "./Forms.module.css";

const HOUSING = [["apartment", "Departamento"], ["house", "Casa"], ["house_with_yard", "Casa con patio"]];

export default function AdoptionRequest() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { organization } = useOrganization();
  const { data: animal, error, loading } = useApi(() => getAnimal(slug), [slug]);
  const [person, setPerson] = useState(emptyPerson);
  const [details, setDetails] = useState({ housing: "apartment", has_other_pets: false, message: "" });
  const [submit, { sending, error: sendError, fieldErrors }] = useSubmit((data) => requestAdoption(slug, data));

  if (loading) return <Loading />;
  if (error) return <ErrorMessage error={error} />;

  const onSubmit = async (event) => {
    event.preventDefault();
    const result = await submit({ ...personPayload(person), ...details });
    if (result) navigate("/gracias", { state: { kind: "adoption", message: result.detail } });
  };

  const fee = organization?.adoption_fee || 0;

  return (
    <div className={styles.narrow}>
      <Link to={`/animales/${animal.slug}`} className={styles.muted}><Icon name="back" /> Volver a {animal.name}</Link>
      <div className={styles.who}>
        <span className={styles.whoPhoto}><Photo photo={animal.cover} seed={animal.id} alt={`Foto de ${animal.name}`} /></span>
        <div className={styles.head}>
          <p className={styles.eyebrow}>Solicitud de adopción</p>
          <h1>Quiero adoptar a {animal.name}</h1>
        </div>
      </div>
      <p className={styles.muted}>Solo necesitamos lo básico. Después te llamamos para conocerte y coordinar una visita.</p>

      <form className={formStyles.form} onSubmit={onSubmit} noValidate>
        <PersonFields value={person} onChange={setPerson} errors={fieldErrors} />
        <Choices legend="¿Dónde vives?" name="housing" options={HOUSING} value={details.housing} onChange={(housing) => setDetails({ ...details, housing })} />
        <Choices
          legend="¿Tienes otros animales?"
          name="pets"
          options={[["no", "No"], ["si", "Sí"]]}
          value={details.has_other_pets ? "si" : "no"}
          onChange={(v) => setDetails({ ...details, has_other_pets: v === "si" })}
        />
        <TextInput
          label="¿Algo que quieras contarnos?"
          optional
          multiline
          value={details.message}
          onChange={(e) => setDetails({ ...details, message: e.target.value })}
          error={fieldErrors.message}
        />
        {fee > 0 && (
          <Note>La adopción tiene un aporte de <b>{money(fee)}</b>, que se paga directamente a la fundación al firmar el contrato. Ayuda a cuidar al resto de los animales.</Note>
        )}
        <Checkbox
          label={`Acepto que ${organization?.name || "la fundación"} guarde mis datos para gestionar mi solicitud.`}
          checked={person.consent}
          onChange={(consent) => setPerson({ ...person, consent })}
          error={fieldErrors.consent}
        />
        <FormError message={sendError} />
        <Button type="submit" block disabled={sending}>{sending ? "Enviando…" : "Enviar solicitud"}</Button>
      </form>
    </div>
  );
}
