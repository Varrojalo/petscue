import { useMemo, useState } from "react";

import { getLocalities } from "../api/public";
import { ID_LABEL, ID_PLACEHOLDER, LOCALITY_LABEL, PHONE_PLACEHOLDER } from "../lib/format";
import { useApi } from "../lib/useApi";
import { Select, TextInput, formStyles } from "./Form";

export const emptyPerson = {
  rut: "", first_names: "", paternal_surname: "", maternal_surname: "", phone: "", email: "", locality_id: "", consent: false,
};

export function personPayload(person) {
  return { ...person, email: person.email || null, locality_id: Number(person.locality_id) || null };
}

/** Contact data shared by every public form: RUT, names, phone, email and commune (chosen by region first). */
export default function PersonFields({ value, onChange, errors = {} }) {
  const localities = useApi(getLocalities);
  const [region, setRegion] = useState("");
  const set = (key) => (event) => onChange({ ...value, [key]: event.target.value });

  const regions = useMemo(() => [...new Set((localities.data || []).map((l) => l.region))], [localities.data]);
  const selectedRegion = region || (localities.data || []).find((l) => String(l.id) === String(value.locality_id))?.region || "";
  const communes = (localities.data || []).filter((l) => l.region === selectedRegion);

  return (
    <>
      <div className={formStyles.row}>
        <TextInput label="Nombres" value={value.first_names} onChange={set("first_names")} error={errors.first_names} autoComplete="given-name" />
        <TextInput label={ID_LABEL} value={value.rut} onChange={set("rut")} error={errors.rut} placeholder={ID_PLACEHOLDER} autoComplete="off" />
      </div>
      <div className={formStyles.row}>
        <TextInput label="Primer apellido" value={value.paternal_surname} onChange={set("paternal_surname")} error={errors.paternal_surname} autoComplete="family-name" />
        <TextInput label="Segundo apellido" optional value={value.maternal_surname} onChange={set("maternal_surname")} error={errors.maternal_surname} />
      </div>
      <div className={formStyles.row}>
        <TextInput label="Teléfono" type="tel" inputMode="tel" value={value.phone} onChange={set("phone")} error={errors.phone} placeholder={PHONE_PLACEHOLDER} autoComplete="tel" />
        <TextInput label="Correo" optional type="email" value={value.email} onChange={set("email")} error={errors.email} autoComplete="email" />
      </div>
      <div className={formStyles.row}>
        <Select label="Región" value={selectedRegion} onChange={(e) => { setRegion(e.target.value); onChange({ ...value, locality_id: "" }); }}>
          <option value="">Elige tu región</option>
          {regions.map((r) => <option key={r} value={r}>{r}</option>)}
        </Select>
        <Select label={LOCALITY_LABEL} value={value.locality_id} onChange={set("locality_id")} error={errors.locality_id} disabled={!selectedRegion}>
          <option value="">{selectedRegion ? `Elige tu ${LOCALITY_LABEL.toLowerCase()}` : "Primero elige la región"}</option>
          {communes.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
        </Select>
      </div>
    </>
  );
}
