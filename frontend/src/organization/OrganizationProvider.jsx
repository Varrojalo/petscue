import { createContext, useContext, useEffect, useState } from "react";

import { getOrganization } from "../api/public";
import { readableTextOn } from "../lib/color";

const OrganizationContext = createContext(null);

/** Loads the organization's identity once and paints the whole site with its colors and typeface. */
export function OrganizationProvider({ children }) {
  const [organization, setOrganization] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getOrganization().then(setOrganization).catch(setError);
  }, []);

  useEffect(() => {
    if (!organization) return;
    const root = document.documentElement.style;
    root.setProperty("--brand", organization.brand_color);
    root.setProperty("--accent", organization.accent_color);
    root.setProperty("--on-brand", readableTextOn(organization.brand_color));
    root.setProperty("--on-accent", readableTextOn(organization.accent_color));
    document.title = organization.name;
    if (organization.title_font_url) {
      const font = new FontFace("OrganizationTitles", `url(${organization.title_font_url})`);
      font.load().then((loaded) => {
        document.fonts.add(loaded);
        root.setProperty("--display", `"OrganizationTitles", "Schibsted Grotesk", system-ui, sans-serif`);
      }).catch(() => {});
    }
  }, [organization]);

  return <OrganizationContext.Provider value={{ organization, error }}>{children}</OrganizationContext.Provider>;
}

export function useOrganization() {
  return useContext(OrganizationContext);
}
