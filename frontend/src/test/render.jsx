import { render } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";

import { OrganizationProvider } from "../organization/OrganizationProvider";

export const organization = {
  name: "Fundación Patitas",
  street_address: "Av. Irarrázaval 2450",
  locality: "Ñuñoa",
  region: "Metropolitana de Santiago",
  phone: "+56 9 5555 1234",
  email: "hola@patitas.cl",
  logo_url: null,
  title_font_url: null,
  brand_color: "#2F7D5A",
  accent_color: "#F2C94C",
  adoption_fee: 30000,
  street_reports_enabled: true,
  social_links: [{ id: 1, network: "instagram", handle: "patitas", position: 0 }],
  membership_tiers: [{ id: 1, monthly_amount: 5000, position: 0 }, { id: 2, monthly_amount: 10000, position: 1 }],
  species: [
    { id: 1, name: "Perro", plural_name: "Perros", life_stages: [{ id: 1, name: "Cachorro", from_months: 0 }, { id: 2, name: "Adulto", from_months: 24 }] },
    { id: 2, name: "Gato", plural_name: "Gatos", life_stages: [] },
  ],
  featured_animal: null,
};

export function animalCard(overrides = {}) {
  return {
    id: 1, slug: "canela", name: "Canela", species: { id: 1, name: "Perro" }, sex: "Hembra", size: "Mediano",
    age_months: 36, life_stage: "Adulto", in_foster_home: false, in_treatment: false, sponsorship_amount: 8000, cover: null,
    ...overrides,
  };
}

/** Renders a page inside the router and the organization provider, at `route`, matching `path`. */
export function renderPage(element, { route = "/", path = "/" } = {}) {
  return render(
    <OrganizationProvider>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path={path} element={element} />
          <Route path="/gracias" element={<p>Página de gracias</p>} />
        </Routes>
      </MemoryRouter>
    </OrganizationProvider>,
  );
}
