import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { SESSION_EXPIRED } from "../api/client";
import * as api from "../api/dashboard";

const AuthContext = createContext(null);

/** Who is signed in to the panel. Loaded once; cleared when the backend says the session ended. */
export function AuthProvider({ children }) {
  const [state, setState] = useState({ user: null, loading: true, expired: false });

  useEffect(() => {
    api.prepareSession()
      .then(api.me)
      .then((user) => setState({ user, loading: false, expired: false }))
      .catch(() => setState({ user: null, loading: false, expired: false }));
  }, []);

  useEffect(() => {
    const onExpired = () => setState((s) => (s.user ? { user: null, loading: false, expired: true } : s));
    window.addEventListener(SESSION_EXPIRED, onExpired);
    return () => window.removeEventListener(SESSION_EXPIRED, onExpired);
  }, []);

  const signIn = useCallback(async (email, password) => {
    await api.prepareSession();
    const user = await api.login(email, password);
    await api.prepareSession(); // Django rotates the CSRF token when signing in
    setState({ user, loading: false, expired: false });
    return user;
  }, []);

  const signOut = useCallback(async () => {
    await api.logout().catch(() => {});
    setState({ user: null, loading: false, expired: false });
  }, []);

  return <AuthContext.Provider value={{ ...state, signIn, signOut }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
