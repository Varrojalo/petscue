import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router";

import { getCounters } from "../api/dashboard";
import { useAuth } from "../auth/AuthProvider";
import { BigTextButton, Logo } from "../components/Brand";
import Icon from "../components/Icon";
import { useOrganization } from "../organization/OrganizationProvider";
import styles from "./DashboardLayout.module.css";

// The panel is fairly quiet, so menu numbers refresh when it opens and then once an hour.
const COUNTERS_EVERY_MS = 60 * 60 * 1000;

const CountersContext = createContext({ counters: null, refresh: () => {} });
export const useCounters = () => useContext(CountersContext);

/** Sections of the panel. `adminOnly` hides them for team accounts without the administration role. */
export const SECTIONS = [
  { to: "/dashboard", label: "Resumen", icon: "chart", end: true, tab: true },
  { to: "/dashboard/animales", label: "Animales", icon: "paw", tab: true },
];

function initials(name) {
  return name.split(" ").filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
}

export default function DashboardLayout() {
  const { organization } = useOrganization();
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [counters, setCounters] = useState(null);

  const refresh = useCallback(() => getCounters().then(setCounters).catch(() => {}), []);
  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, COUNTERS_EVERY_MS);
    return () => clearInterval(timer);
  }, [refresh]);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  const sections = SECTIONS.filter((s) => !s.adminOnly || user.role === "admin");
  const badge = (section) => (section.counter && counters?.[section.counter] ? <span className={styles.count}>{counters[section.counter]}</span> : null);
  const exit = async () => {
    await signOut();
    navigate("/dashboard/login", { replace: true });
  };

  return (
    <CountersContext.Provider value={{ counters, refresh }}>
      <div className={styles.app}>
        <header className={styles.top}>
          <Link to="/dashboard" className={styles.brand}>
            <Logo organization={organization} />
            <span className={styles.org}>
              <b>{organization?.name}</b>
              <small>Panel interno</small>
            </span>
          </Link>
          <span className={styles.right}>
            <span className={styles.role}>{user.role === "admin" ? "Administración" : "Equipo"}</span>
            <BigTextButton />
            <span className={styles.avatar} title={user.name}>{initials(user.name)}</span>
          </span>
        </header>

        <div className={styles.body}>
          <nav className={styles.side} aria-label="Panel">
            {sections.map((s) => (
              <NavLink key={s.to} to={s.to} end={s.end} className={({ isActive }) => (isActive ? styles.active : undefined)}>
                <Icon name={s.icon} /> {s.label} {badge(s)}
              </NavLink>
            ))}
            <hr />
            <Link to="/"><Icon name="eye" /> Ver la web pública</Link>
            <button type="button" onClick={exit}><Icon name="logout" /> Cerrar sesión</button>
          </nav>
          <main className={styles.main}>
            <Outlet />
          </main>
        </div>

        <nav className={styles.tabs} style={{ "--n": sections.filter((s) => s.tab).length + 1 }} aria-label="Secciones">
          {sections.filter((s) => s.tab).map((s) => (
            <NavLink key={s.to} to={s.to} end={s.end} className={({ isActive }) => (isActive ? styles.active : undefined)}>
              <span className={styles.pill}><Icon name={s.icon} /></span>
              {s.label}
              {badge(s)}
            </NavLink>
          ))}
          <NavLink to="/dashboard/mas" className={({ isActive }) => (isActive ? styles.active : undefined)}>
            <span className={styles.pill}><Icon name="more" /></span>
            Más
          </NavLink>
        </nav>
      </div>
    </CountersContext.Provider>
  );
}

/** On phones, the sections that don't fit in the bottom bar, plus the public site and sign out. */
export function MoreMenu() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const extra = SECTIONS.filter((s) => !s.tab && (!s.adminOnly || user.role === "admin"));
  return (
    <div className={styles.more}>
      <h1>Más</h1>
      {extra.map((s) => (
        <Link key={s.to} to={s.to} className={styles.moreItem}><Icon name={s.icon} /> {s.label}</Link>
      ))}
      <Link to="/" className={styles.moreItem}><Icon name="eye" /> Ver la web pública</Link>
      <button type="button" className={styles.moreItem} onClick={async () => { await signOut(); navigate("/dashboard/login", { replace: true }); }}>
        <Icon name="logout" /> Cerrar sesión
      </button>
    </div>
  );
}
