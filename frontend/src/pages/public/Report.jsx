import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

import { sendStreetReport } from "../../api/public";
import Button from "../../components/Button";
import { FormError, Note, TextInput, formStyles } from "../../components/Form";
import Icon from "../../components/Icon";
import { Empty } from "../../components/PageState";
import { EMERGENCY, PHONE_PLACEHOLDER } from "../../lib/format";
import { useSubmit } from "../../lib/useApi";
import { useOrganization } from "../../organization/OrganizationProvider";
import styles from "./Forms.module.css";

export default function Report() {
  const { organization } = useOrganization();
  const navigate = useNavigate();
  const [data, setData] = useState({ address: "", notes: "", contact_phone: "" });
  const [photo, setPhoto] = useState(null);
  const [preview, setPreview] = useState(null);
  const [submit, { sending, error, fieldErrors }] = useSubmit(sendStreetReport);

  useEffect(() => {
    if (!photo) return setPreview(null);
    const url = URL.createObjectURL(photo);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [photo]);

  if (organization && !organization.street_reports_enabled) {
    return (
      <Empty title="La fundación no recibe avisos por la web">
        <p>Si viste un animal que necesita ayuda, comunícate con la fundación por teléfono o redes sociales.</p>
      </Empty>
    );
  }

  const set = (key) => (event) => setData({ ...data, [key]: event.target.value });

  const onSubmit = async (event) => {
    event.preventDefault();
    const form = new FormData();
    Object.entries(data).forEach(([key, value]) => form.append(key, value));
    if (photo) form.append("photo", photo);
    const result = await submit(form);
    if (result) navigate("/gracias", { state: { kind: "report", message: result.detail } });
  };

  return (
    <div className={styles.narrow}>
      <div className={styles.head}>
        <h1>Avisar de un animal en la calle</h1>
        <p className={styles.muted}>Envíanos una foto y dónde está. El equipo recibirá tu aviso.</p>
      </div>
      <form className={formStyles.form} onSubmit={onSubmit} noValidate>
        {preview ? (
          <div className={styles.preview}>
            <img src={preview} alt="Foto elegida" />
            <Button variant="ghost" size="small" onClick={() => setPhoto(null)}>Quitar foto</Button>
          </div>
        ) : (
          <label className={styles.upload}>
            <span className={styles.optionIcon}><Icon name="camera" /></span>
            <span><b>Añadir foto del animal</b><small>Desde la cámara o la galería (opcional)</small></span>
            <input type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={(e) => setPhoto(e.target.files[0] || null)} />
          </label>
        )}
        <TextInput label="¿Dónde está?" multiline value={data.address} onChange={set("address")} error={fieldErrors.address} placeholder="Ej.: Av. Grecia 1500, Ñuñoa, frente a la plaza" />
        <TextInput label="¿Algo más que debamos saber?" optional multiline value={data.notes} onChange={set("notes")} error={fieldErrors.notes} placeholder="Ej.: está herido, tiene collar" />
        <TextInput label="Tu teléfono" optional type="tel" inputMode="tel" value={data.contact_phone} onChange={set("contact_phone")} error={fieldErrors.contact_phone} placeholder={PHONE_PLACEHOLDER} />
        <Note>Si el animal está en la calzada o hay peligro inmediato, llama a {EMERGENCY.name} al <b>{EMERGENCY.number}</b>.</Note>
        <FormError message={error} />
        <Button type="submit" block disabled={sending}>{sending ? "Enviando…" : "Enviar aviso"}</Button>
      </form>
    </div>
  );
}
