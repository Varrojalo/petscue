import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router";

import Icon from "../components/Icon";
import { socialLink, whatsappLink } from "../lib/format";
import { useOrganization } from "../organization/OrganizationProvider";
import styles from "./PublicLayout.module.css";

const BIG_TEXT_KEY = "petscue-big-text";

function readBigText() {
  try {
    return localStorage.getItem(BIG_TEXT_KEY) === "1";
  } catch {
    return false;
  }
}

/** Larger letters for people who need them. The choice is remembered on this device. */
function useBigText() {
  const [big, setBig] = useState(readBigText);
  useEffect(() => {
    document.documentElement.classList.toggle("big-text", big);
    try {
      localStorage.setItem(BIG_TEXT_KEY, big ? "1" : "0");
    } catch {
      /* private mode: the choice just isn't remembered */
    }
  }, [big]);
  return [big, setBig];
}

function Logo({ organization }) {
  const initial = (organization?.name || "P").replace(/^(Fundación|Asociación|Agrupación|ONG)\s+/i, "")[0]?.toUpperCase();
  return (
    <span className={styles.logo}>
      {organization?.logo_url ? <img src={organization.logo_url} alt="" /> : initial}
    </span>
  );
}

export default function PublicLayout() {
  const { organization } = useOrganization();
  const [big, setBig] = useBigText();
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  const nav = [
    ["/", "Inicio", "home"],
    ["/animales", "Adoptar", "paw"],
    ["/ayudar", "Ayudar", "heart"],
    ...(organization?.street_reports_enabled ? [["/avisar", "Avisar", "pin"]] : []),
  ];
  const whatsapp = whatsappLink(organization?.phone);

  return (
    <div className={styles.app}>
      <header className={styles.top}>
        <Link to="/" className={styles.brand}>
          <Logo organization={organization} />
          <span className={styles.org}>
            <b>{organization?.name || " "}</b>
            {organization?.locality && <small>{organization.locality}</small>}
          </span>
        </Link>
        <nav className={styles.nav} aria-label="Principal">
          {nav.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => (isActive ? styles.active : undefined)}>
              {label}
            </NavLink>
          ))}
        </nav>
        <button type="button" className={styles.bigText} aria-pressed={big} onClick={() => setBig(!big)} title="Letra más grande">
          Aa<span className="sr-only"> · letra más grande</span>
        </button>
      </header>

      <main className={styles.main}>
        <Outlet />
      </main>

      {organization && (
        <footer className={styles.footer}>
          <b className={styles.footerName}>{organization.name}</b>
          <div className={styles.footerCols}>
            {organization.street_address && (
              <div>
                <span className={styles.eyebrow}>Dirección</span>
                <span>{organization.street_address}{organization.locality ? `, ${organization.locality}` : ""}</span>
              </div>
            )}
            {organization.phone && (
              <div>
                <span className={styles.eyebrow}>Teléfono</span>
                <span className={styles.selectable}>{organization.phone}</span>
              </div>
            )}
            {organization.email && (
              <div>
                <span className={styles.eyebrow}>Correo</span>
                <span className={styles.selectable}>{organization.email}</span>
              </div>
            )}
          </div>
          {(organization.social_links.length > 0 || whatsapp) && (
            <div className={styles.social}>
              {organization.social_links.map((link) => {
                const { label, url } = socialLink(link);
                return <a key={link.id} href={url} target="_blank" rel="noopener noreferrer">{label}</a>;
              })}
              {whatsapp && <a href={whatsapp} target="_blank" rel="noopener noreferrer">WhatsApp</a>}
            </div>
          )}
          <p className={styles.made}>Plataforma construida con Petscue</p>
        </footer>
      )}

      <nav className={styles.tabs} style={{ "--n": nav.length }} aria-label="Secciones">
        {nav.map(([to, label, icon]) => (
          <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => (isActive ? styles.active : undefined)}>
            <span className={styles.pill}><Icon name={icon} /></span>
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
