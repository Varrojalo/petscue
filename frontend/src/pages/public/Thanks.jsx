import { Navigate, useLocation } from "react-router";

import Button from "../../components/Button";
import Icon from "../../components/Icon";
import { socialLink } from "../../lib/format";
import { useOrganization } from "../../organization/OrganizationProvider";
import styles from "./Forms.module.css";

const TITLES = { adoption: "¡Solicitud enviada!", application: "¡Gracias por sumarte!", report: "Aviso recibido" };

/** Confirmation after any public form. The message comes from the backend. */
export default function Thanks() {
  const { state } = useLocation();
  const { organization } = useOrganization();
  if (!state?.kind) return <Navigate to="/" replace />;

  return (
    <div className={styles.narrow}>
      <div className={styles.done}>
        <span className={styles.doneIcon}><Icon name={state.kind === "report" ? "check" : "heart"} size="42" /></span>
        <h1>{TITLES[state.kind]}</h1>
        <p>{state.message}</p>
        <div className={styles.row}>
          <Button to="/">Volver al inicio</Button>
          <Button to="/animales" variant="ghost">Ver animales</Button>
        </div>
        {organization?.social_links.length > 0 && (
          <>
            <p>Mientras tanto, síguenos para ver cómo les va a los animales:</p>
            <div className={styles.row}>
              {organization.social_links.map((link) => {
                const { label, url } = socialLink(link);
                return <Button key={link.id} href={url} variant="ghost" size="small">{label}</Button>;
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
