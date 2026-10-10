import { useCallback, useEffect, useState } from "react";

/** Loads data from the API when the page opens (and again when `deps` change). */
export function useApi(load, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(load, deps);

  useEffect(() => {
    let active = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    run()
      .then((data) => active && setState({ data, error: null, loading: false }))
      .catch((error) => active && setState({ data: null, error, loading: false }));
    return () => {
      active = false;
    };
  }, [run]);

  return state;
}

/** Sends a form: keeps the sending state, the general error and the per-field errors from the backend. */
export function useSubmit(send) {
  const [state, setState] = useState({ sending: false, error: null, fieldErrors: {} });

  const submit = async (...args) => {
    setState({ sending: true, error: null, fieldErrors: {} });
    try {
      const result = await send(...args);
      setState({ sending: false, error: null, fieldErrors: {} });
      return result;
    } catch (error) {
      setState({ sending: false, error: error.detail || error.message, fieldErrors: error.fieldErrors || {} });
      return undefined;
    }
  };

  return [submit, state];
}
