import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Outlet, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, SESSION_EXPIRED } from "../../api/client";
import * as api from "../../api/dashboard";
import * as publicApi from "../../api/public";
import { AuthProvider } from "../../auth/AuthProvider";
import { RequireAuth } from "../../auth/RequireAuth";
import VisitsChart from "../../components/VisitsChart";
import DashboardLayout from "../../layouts/DashboardLayout";
import { niceMax } from "../../lib/scale";
import { OrganizationProvider } from "../../organization/OrganizationProvider";
import { organization } from "../../test/render";
import AnimalPage from "./AnimalPage";
import AnimalsList from "./AnimalsList";
import Login from "./Login";
import Summary from "./Summary";

vi.mock("../../api/dashboard");
vi.mock("../../api/public");

const ADMIN = { id: 1, name: "Marta González", email: "marta@patitas.cl", role: "admin" };

function renderPanel(route, { signedIn = true } = {}) {
  vi.mocked(api.me).mockImplementation(() => (signedIn ? Promise.resolve(ADMIN) : Promise.reject(new ApiError(401, "Inicia sesión para continuar."))));
  return render(
    <OrganizationProvider>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="dashboard" element={<AuthProvider><Outlet /></AuthProvider>}>
            <Route path="login" element={<Login />} />
            <Route element={<RequireAuth><DashboardLayout /></RequireAuth>}>
              <Route index element={<Summary />} />
              <Route path="animales" element={<AnimalsList />} />
              <Route path="animales/:id" element={<AnimalPage />} />
            </Route>
          </Route>
        </Routes>
      </MemoryRouter>
    </OrganizationProvider>,
  );
}

const summary = {
  animals_in_care: 2, in_foster_homes: 1, new_adoption_requests: 3, adoptions_this_year: 23, active_members: 318,
  visits_chart: [
    { animal_id: 1, name: "Bruno", visits_last_30_days: 38, days_in_organization: 410 },
    { animal_id: 2, name: "Pipa", visits_last_30_days: 530, days_in_organization: 20 },
  ],
  recent_requests: [{ id: 9, animal: "Canela", person: "Elena Ruiz", status: "Nueva", created_at: "2026-10-09T10:00:00Z" }],
};

beforeEach(() => {
  vi.mocked(publicApi.getOrganization).mockResolvedValue(organization);
  vi.mocked(api.prepareSession).mockResolvedValue({ csrf_token: "x" });
  vi.mocked(api.getCounters).mockResolvedValue({ new_adoption_requests: 3, pending_applications: 0, new_street_reports: 0 });
  vi.mocked(api.getSummary).mockResolvedValue(summary);
});

describe("scale", () => {
  it("rounds the maximum up to a readable number", () => {
    expect(niceMax(37)).toBe(50);
    expect(niceMax(120)).toBe(200);
    expect(niceMax(4300)).toBe(5000);
    expect(niceMax(0)).toBe(1);
  });
});

describe("visits chart", () => {
  it("orders by visits or time and draws bars against a readable scale", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><VisitsChart rows={summary.visits_chart} /></MemoryRouter>);
    const names = () => screen.getAllByRole("listitem").map((li) => within(li).getByRole("link").textContent);
    expect(names()).toEqual(["Pipa", "Bruno"]);
    await user.click(screen.getByRole("button", { name: "Más tiempo" }));
    expect(names()).toEqual(["Bruno", "Pipa"]);
    expect(screen.getByText(/escala de 0 · 500 · 1\.000/)).toBeInTheDocument();
  });
});

describe("panel access", () => {
  it("sends people without a session to the login and back to where they were", async () => {
    vi.mocked(api.login).mockResolvedValue(ADMIN);
    vi.mocked(api.getAnimals).mockResolvedValue({ items: [], count: 0 });
    const user = userEvent.setup();
    renderPanel("/dashboard/animales", { signedIn: false });
    expect(await screen.findByRole("heading", { name: "Ingresar al panel" })).toBeInTheDocument();
    await user.type(screen.getByLabelText("Correo"), "marta@patitas.cl");
    await user.type(screen.getByLabelText("Contraseña"), "clave");
    await user.click(screen.getByRole("button", { name: "Ingresar" }));
    expect(await screen.findByRole("heading", { name: "Animales" })).toBeInTheDocument();
  });

  it("shows the backend's message when the password is wrong", async () => {
    vi.mocked(api.login).mockRejectedValue(new ApiError(400, "Correo o contraseña incorrectos."));
    const user = userEvent.setup();
    renderPanel("/dashboard/login", { signedIn: false });
    await user.type(await screen.findByLabelText("Correo"), "marta@patitas.cl");
    await user.type(screen.getByLabelText("Contraseña"), "mala");
    await user.click(screen.getByRole("button", { name: "Ingresar" }));
    expect(await screen.findByText("Correo o contraseña incorrectos.")).toBeInTheDocument();
  });

  it("returns to the login with a notice when the session ends", async () => {
    renderPanel("/dashboard");
    expect(await screen.findByText("Hola, Marta")).toBeInTheDocument();
    window.dispatchEvent(new CustomEvent(SESSION_EXPIRED));
    expect(await screen.findByText("Tu sesión terminó. Vuelve a ingresar para continuar.")).toBeInTheDocument();
  });
});

describe("summary", () => {
  it("shows the numbers, flags new requests and the menu counter", async () => {
    renderPanel("/dashboard");
    expect(await screen.findByText("Solicitudes nuevas")).toBeInTheDocument();
    expect(screen.getByText("Por revisar")).toBeInTheDocument();
    expect(screen.getByText("318")).toBeInTheDocument();
    expect(screen.getByText("Quiere adoptar a Canela · Nueva")).toBeInTheDocument();
  });
});

describe("animals", () => {
  it("filters by status, including exits", async () => {
    vi.mocked(api.getAnimals).mockResolvedValue({ items: [], count: 0 });
    const user = userEvent.setup();
    renderPanel("/dashboard/animales");
    await screen.findByRole("heading", { name: "Animales" });
    await user.click(screen.getByRole("button", { name: "Salidas" }));
    await waitFor(() => expect(api.getAnimals).toHaveBeenLastCalledWith(expect.objectContaining({ status: "exited", page: 1 })));
  });

  it("creates an animal and continues to its page to add photos", async () => {
    vi.mocked(api.getSpecies).mockResolvedValue([{ id: 2, name: "Gato", plural_name: "Gatos", is_active: true, position: 1, life_stages: [] }]);
    vi.mocked(api.getTraits).mockResolvedValue([{ id: 1, label: "Sociable" }]);
    vi.mocked(api.createAnimal).mockResolvedValue({ id: 7 });
    vi.mocked(api.getAnimal).mockReturnValue(new Promise(() => {}));
    const user = userEvent.setup();
    renderPanel("/dashboard/animales/nuevo");
    await user.type(await screen.findByLabelText("Nombre"), "Mishi");
    await user.selectOptions(screen.getByLabelText("Especie"), "Gato");
    await user.click(screen.getByLabelText("Sociable"));
    await user.click(screen.getByRole("button", { name: "Crear y seguir con las fotos" }));
    await waitFor(() => expect(api.getAnimal).toHaveBeenCalledWith("7"));
    expect(api.createAnimal).toHaveBeenCalledWith(expect.objectContaining({ name: "Mishi", species_id: 2, trait_ids: [1] }));
  });
});
