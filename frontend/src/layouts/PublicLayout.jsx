import { useEffect } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router";

import { BigTextButton, Logo } from "../components/Brand";
import Icon from "../components/Icon";
import { socialLink, whatsappLink } from "../lib/format";
import { useOrganization } from "../organization/OrganizationProvider";
import styles from "./PublicLayout.module.css";

export default function PublicLayout() {
  const { organization } = useOrganization();
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
        <span className={styles.bigText}><BigTextButton /></span>
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
