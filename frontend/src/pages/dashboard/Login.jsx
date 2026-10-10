import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router";

import { useAuth } from "../../auth/AuthProvider";
import { Logo } from "../../components/Brand";
import Button from "../../components/Button";
import { FormError, TextInput, formStyles } from "../../components/Form";
import { useOrganization } from "../../organization/OrganizationProvider";
import styles from "./Login.module.css";

export default function Login() {
  const { user, signIn } = useAuth();
  const { organization } = useOrganization();
  const { state } = useLocation();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);

  const destination = state?.from && state.from !== "/dashboard/login" ? state.from : "/dashboard";
  if (user) return <Navigate to={destination} replace />;

  const onSubmit = async (event) => {
    event.preventDefault();
    if (!form.email || !form.password) return setError("Escribe tu correo y tu contraseña.");
    setSending(true);
    setError(null);
    try {
      await signIn(form.email, form.password);
      navigate(destination, { replace: true });
    } catch (e) {
      setError(e.detail || e.message);
      setSending(false);
    }
  };

  return (
    <main className={styles.page}>
      <form className={`${formStyles.form} ${styles.card}`} onSubmit={onSubmit} noValidate>
        <div className={styles.brand}>
          <Logo organization={organization} />
          <span>{organization?.name}</span>
        </div>
        <h1>Ingresar al panel</h1>
        {state?.expired && <p className={styles.notice} role="status">Tu sesión terminó. Vuelve a ingresar para continuar.</p>}
        <TextInput label="Correo" type="email" autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <TextInput label="Contraseña" type="password" autoComplete="current-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <FormError message={error} />
        <Button type="submit" block disabled={sending}>{sending ? "Ingresando…" : "Ingresar"}</Button>
        <Link to="/" className={styles.back}>Volver a la web pública</Link>
      </form>
    </main>
  );
}
