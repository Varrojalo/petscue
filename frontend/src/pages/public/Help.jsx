import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";

import { getAnimals, getAvailabilityOptions, sendApplication } from "../../api/public";
import Button from "../../components/Button";
import { Checkbox, Choices, FormError, Note, Select, TextInput, formStyles } from "../../components/Form";
import Icon from "../../components/Icon";
import PersonFields, { emptyPerson, personPayload } from "../../components/PersonFields";
import { money } from "../../lib/format";
import { useApi, useSubmit } from "../../lib/useApi";
import { useOrganization } from "../../organization/OrganizationProvider";
import styles from "./Forms.module.css";

/** Every animal that can be sponsored (the list is paginated, so it is read page by page). */
async function allAnimals() {
  const items = [];
  for (let page = 1; ; page += 1) {
    const data = await getAnimals({ page });
    items.push(...data.items);
    if (items.length >= data.count || data.items.length === 0) return items;
  }
}

export default function Help() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { organization } = useOrganization();
  const how = params.get("como");
  const animals = useApi(allAnimals);
  const availability = useApi(getAvailabilityOptions);
  const tiers = organization?.membership_tiers || [];

  const [roles, setRoles] = useState({ member: how !== "voluntario", volunteer: how === "voluntario" });
  const [membership, setMembership] = useState({
    kind: how === "padrino" ? "sponsorship" : "donation",
    monthly_amount: "",
    animal_id: params.get("animal") || "",
    custom: "",
  });
  const [availabilityIds, setAvailabilityIds] = useState([]);
  const [person, setPerson] = useState(emptyPerson);
  const [submit, { sending, error, fieldErrors }] = useSubmit(sendApplication);

  useEffect(() => {
    if (!membership.monthly_amount && tiers.length) setMembership((m) => ({ ...m, monthly_amount: String(tiers[Math.min(1, tiers.length - 1)].monthly_amount) }));
  }, [tiers, membership.monthly_amount]);

  const sponsored = (animals.data || []).find((a) => String(a.id) === String(membership.animal_id));

  const onSubmit = async (event) => {
    event.preventDefault();
    const payload = { ...personPayload(person), membership: null, volunteer: null };
    if (roles.member) {
      const amount = membership.kind === "sponsorship"
        ? sponsored?.sponsorship_amount
        : Number(membership.monthly_amount === "otro" ? membership.custom : membership.monthly_amount);
      payload.membership = {
        kind: membership.kind,
        monthly_amount: amount || 0,
        animal_id: membership.kind === "sponsorship" ? Number(membership.animal_id) || null : null,
      };
    }
    if (roles.volunteer) payload.volunteer = { availability_ids: availabilityIds };
    const result = await submit(payload);
    if (result) navigate("/gracias", { state: { kind: "application", message: result.detail } });
  };

  return (
    <div className={styles.narrow}>
      <div className={styles.head}>
        <h1>Súmate a {organization?.name || "la fundación"}</h1>
        <p className={styles.muted}>
          Aquí solo dejas tu solicitud. El equipo te contactará para conocerte, y los aportes se coordinan directamente con la fundación: no pagas nada en esta página.
        </p>
      </div>

      <form className={formStyles.form} onSubmit={onSubmit} noValidate>
        <fieldset className={styles.section} style={{ border: 0, padding: 0, margin: 0 }}>
          <legend className={formStyles.label}>¿Cómo quieres ayudar? Puedes elegir las dos.</legend>
          <div className={styles.options}>
            <label className={styles.option}>
              <input type="checkbox" checked={roles.member} onChange={(e) => setRoles({ ...roles, member: e.target.checked })} />
              <span className={styles.optionIcon}><Icon name="heart" /></span>
              <span><b>Como socio</b><small>Aportas recursos: una cuota mensual para la fundación o el padrinazgo de un animal.</small></span>
            </label>
            <label className={styles.option}>
              <input type="checkbox" checked={roles.volunteer} onChange={(e) => setRoles({ ...roles, volunteer: e.target.checked })} />
              <span className={styles.optionIcon}><Icon name="hand" /></span>
              <span><b>Como voluntario</b><small>Aportas tu tiempo: refugio, paseos, ferias y traslados.</small></span>
            </label>
          </div>
        </fieldset>

        {roles.member && (
          <div className={styles.section}>
            <Choices
              legend="¿Cómo quieres aportar?"
              name="kind"
              options={[["donation", "A la fundación"], ["sponsorship", "Apadrinando a un animal"]]}
              value={membership.kind}
              onChange={(kind) => setMembership({ ...membership, kind })}
            />
            {membership.kind === "donation" ? (
              <>
                <Choices
                  legend="Aporte mensual"
                  name="amount"
                  options={[...tiers.map((t) => [String(t.monthly_amount), money(t.monthly_amount)]), ["otro", "Otro monto"]]}
                  value={membership.monthly_amount}
                  onChange={(monthly_amount) => setMembership({ ...membership, monthly_amount })}
                />
                {membership.monthly_amount === "otro" && (
                  <TextInput label="¿Cuánto al mes?" type="number" inputMode="numeric" min="1" value={membership.custom} onChange={(e) => setMembership({ ...membership, custom: e.target.value })} />
                )}
              </>
            ) : (
              <Select
                label="¿A quién quieres apadrinar?"
                value={membership.animal_id}
                onChange={(e) => setMembership({ ...membership, animal_id: e.target.value })}
                hint={sponsored ? `El padrinazgo de ${sponsored.name} es de ${money(sponsored.sponsorship_amount)} al mes y cubre su alimento.` : undefined}
              >
                <option value="">Elige un animal</option>
                {(animals.data || []).filter((a) => a.sponsorship_amount > 0).map((a) => (
                  <option key={a.id} value={a.id}>{a.name} · {money(a.sponsorship_amount)} al mes</option>
                ))}
              </Select>
            )}
          </div>
        )}

        {roles.volunteer && (
          <div className={styles.section}>
            {(availability.data || []).length > 0 && (
              <Choices
                legend="¿Cuándo puedes ayudar?"
                name="availability"
                multiple
                options={availability.data.map((o) => [o.id, o.name])}
                value={availabilityIds}
                onChange={setAvailabilityIds}
              />
            )}
            <Note>¿Te gustaría ser casa de acogida? Las casas de acogida se eligen entre las personas del equipo: primero te sumas como voluntario y luego lo conversamos.</Note>
          </div>
        )}

        <div className={styles.section}>
          <h2>Tus datos</h2>
          <PersonFields value={person} onChange={setPerson} errors={fieldErrors} />
        </div>
        <Checkbox
          label={`Acepto que ${organization?.name || "la fundación"} guarde mis datos para gestionar mi solicitud.`}
          checked={person.consent}
          onChange={(consent) => setPerson({ ...person, consent })}
          error={fieldErrors.consent}
        />
        <FormError message={error} />
        <Button type="submit" block disabled={sending}>{sending ? "Enviando…" : "Enviar solicitud"}</Button>
      </form>
    </div>
  );
}
