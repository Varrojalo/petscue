import { useEffect, useState } from "react";

const KEY = "petscue-big-text";

function read() {
  try {
    return localStorage.getItem(KEY) === "1";
  } catch {
    return false;
  }
}

/** Larger letters for people who need them. The choice is remembered on this device. */
export function useBigText() {
  const [big, setBig] = useState(read);
  useEffect(() => {
    document.documentElement.classList.toggle("big-text", big);
    try {
      localStorage.setItem(KEY, big ? "1" : "0");
    } catch {
      /* private mode: the choice just isn't remembered */
    }
  }, [big]);
  return [big, setBig];
}
