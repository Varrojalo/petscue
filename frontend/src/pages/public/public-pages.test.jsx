import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "../../api/public";
import { ApiError } from "../../api/client";
import { animalCard, organization, renderPage } from "../../test/render";
import AdoptionRequest from "./AdoptionRequest";
import AnimalDetail from "./AnimalDetail";
import Animals from "./Animals";
import Help from "./Help";
import Home from "./Home";

vi.mock("../../api/public");

const LOCALITIES = [
  { id: 1, name: "Ñuñoa", region: "Metropolitana de Santiago" },
  { id: 2, name: "Providencia", region: "Metropolitana de Santiago" },
  { id: 3, name: "Viña del Mar", region: "Valparaíso" },
];

function detail(overrides = {}) {
  return { ...animalCard(), quote: "La primera en saludar.", story: "La encontraron en una obra.", traits: ["Sociable"],
    vaccinated: true, sterilized: true, has_microchip: false, photos: [], ...overrides };
}

beforeEach(() => {
  vi.mocked(api.getOrganization).mockResolvedValue(organization);
  vi.mocked(api.getStats).mockResolvedValue({ adoptions_this_year: 23, active_members: 318, rescued_this_year: 5, animals_in_care: 2 });
  vi.mocked(api.getLocalities).mockResolvedValue(LOCALITIES);
  vi.mocked(api.getAvailabilityOptions).mockResolvedValue([{ id: 1, name: "Fines de semana" }]);
});

describe("Home", () => {
  it("features an animal and shows the organization's numbers and adoption fee", async () => {
    vi.mocked(api.getAnimals).mockResolvedValue({ items: [animalCard(), animalCard({ id: 2, slug: "bruno", name: "Bruno" })], count: 2 });
    renderPage(<Home />);
    expect(await screen.findByText("Conocer a Canela", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("Tenemos 2 animales listos", { exact: false })).toBeInTheDocument();
    expect(await screen.findByText("23")).toBeInTheDocument();
    expect(screen.getAllByText("$30.000").length).toBeGreaterThan(0);
  });

  it("says when there are no animals yet", async () => {
    vi.mocked(api.getAnimals).mockResolvedValue({ items: [], count: 0 });
    renderPage(<Home />);
    expect(await screen.findByText(/Pronto publicaremos/)).toBeInTheDocument();
  });
});

describe("Animals", () => {
  it("filters by species and only then offers that species' age stages", async () => {
    vi.mocked(api.getAnimals).mockResolvedValue({ items: [animalCard()], count: 1 });
    renderPage(<Animals />, { route: "/animales", path: "/animales" });
    expect(await screen.findByText("Canela")).toBeInTheDocument();
    expect(screen.getByLabelText("Edad")).toBeDisabled();

    await userEvent.click(screen.getByRole("button", { name: "Perros" }));
    await waitFor(() => expect(api.getAnimals).toHaveBeenLastCalledWith(expect.objectContaining({ species: "1", page: 1 })));
    const age = screen.getByLabelText("Edad");
    expect(age).toBeEnabled();
    expect(within(age).getByRole("option", { name: "Cachorro" })).toBeInTheDocument();
  });

  it("offers to clear filters when nothing matches", async () => {
    vi.mocked(api.getAnimals).mockResolvedValue({ items: [], count: 0 });
    renderPage(<Animals />, { route: "/animales?tamano=large", path: "/animales" });
    expect(await screen.findByText("No hay animales con esos filtros")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Quitar filtros" })).toBeInTheDocument();
  });
});

describe("Animal page", () => {
  it("shows the animal, its fee and the sponsorship button", async () => {
    vi.mocked(api.getAnimal).mockResolvedValue(detail({ in_foster_home: true }));
    renderPage(<AnimalDetail />, { route: "/animales/canela", path: "/animales/:slug" });
    expect(await screen.findByRole("heading", { name: "Canela" })).toBeInTheDocument();
    expect(screen.getByText("En casa de acogida · disponible")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Quiero adoptarla/ })).toHaveAttribute("href", "/animales/canela/adoptar");
    expect(screen.getByRole("link", { name: /Apadrinar · \$8\.000 al mes/ })).toHaveAttribute("href", "/ayudar?como=padrino&animal=1");
  });

  it("explains when an animal's page is no longer available", async () => {
    vi.mocked(api.getAnimal).mockRejectedValue(new ApiError(410, "Esta ficha ya no está disponible."));
    renderPage(<AnimalDetail />, { route: "/animales/bruno", path: "/animales/:slug" });
    expect(await screen.findByText("Esta ficha ya no está disponible")).toBeInTheDocument();
  });
});

async function fillPerson(user) {
  await user.type(screen.getByLabelText("Nombres"), "Elena");
  await user.type(screen.getByLabelText("RUT"), "18.765.432-7");
  await user.type(screen.getByLabelText("Primer apellido"), "Ruiz");
  await user.type(screen.getByLabelText("Teléfono"), "+56 9 6231 9087");
  await user.selectOptions(screen.getByLabelText("Región"), "Metropolitana de Santiago");
  await user.selectOptions(screen.getByLabelText("Comuna"), "Ñuñoa");
}

describe("Adoption request", () => {
  it("chooses the commune after the region and sends the request", async () => {
    vi.mocked(api.getAnimal).mockResolvedValue(detail());
    vi.mocked(api.requestAdoption).mockResolvedValue({ detail: "Recibimos tu solicitud para adoptar a Canela." });
    const user = userEvent.setup();
    renderPage(<AdoptionRequest />, { route: "/animales/canela/adoptar", path: "/animales/:slug/adoptar" });
    await screen.findByText("Quiero adoptar a Canela");
    expect(screen.getByLabelText("Comuna")).toBeDisabled();
    await fillPerson(user);
    await user.click(screen.getByLabelText(/Acepto que Fundación Patitas/));
    await user.click(screen.getByRole("button", { name: "Enviar solicitud" }));

    expect(await screen.findByText("Página de gracias")).toBeInTheDocument();
    expect(api.requestAdoption).toHaveBeenCalledWith("canela", expect.objectContaining({
      rut: "18.765.432-7", locality_id: 1, housing: "apartment", has_other_pets: false, consent: true, email: null,
    }));
  });

  it("shows the backend's message next to each field", async () => {
    vi.mocked(api.getAnimal).mockResolvedValue(detail());
    vi.mocked(api.requestAdoption).mockRejectedValue(
      new ApiError(422, "Revisa los datos enviados.", [{ field: "rut", message: "RUT no válido. El dígito verificador no coincide." }]),
    );
    const user = userEvent.setup();
    renderPage(<AdoptionRequest />, { route: "/animales/canela/adoptar", path: "/animales/:slug/adoptar" });
    await screen.findByText("Quiero adoptar a Canela");
    await user.click(screen.getByRole("button", { name: "Enviar solicitud" }));
    expect(await screen.findByText("RUT no válido. El dígito verificador no coincide.")).toBeInTheDocument();
    expect(screen.getByText("Revisa los datos enviados.")).toBeInTheDocument();
    expect(screen.getByLabelText("RUT")).toHaveAttribute("aria-invalid", "true");
  });
});

describe("Help (Súmate)", () => {
  it("sends a sponsorship with the animal's own amount", async () => {
    vi.mocked(api.getAnimals).mockResolvedValue({ items: [animalCard()], count: 1 });
    vi.mocked(api.sendApplication).mockResolvedValue({ detail: "Recibimos tu solicitud." });
    const user = userEvent.setup();
    renderPage(<Help />, { route: "/ayudar?como=padrino&animal=1", path: "/ayudar" });
    expect(await screen.findByText(/El padrinazgo de Canela es de \$8\.000/)).toBeInTheDocument();
    await fillPerson(user);
    await user.click(screen.getByLabelText(/Acepto que Fundación Patitas/));
    await user.click(screen.getByRole("button", { name: "Enviar solicitud" }));
    await screen.findByText("Página de gracias");
    expect(api.sendApplication).toHaveBeenCalledWith(expect.objectContaining({
      membership: { kind: "sponsorship", monthly_amount: 8000, animal_id: 1 },
      volunteer: null,
    }));
  });

  it("sends a volunteer application with the chosen availability", async () => {
    vi.mocked(api.getAnimals).mockResolvedValue({ items: [], count: 0 });
    vi.mocked(api.sendApplication).mockResolvedValue({ detail: "Recibimos tu solicitud." });
    const user = userEvent.setup();
    renderPage(<Help />, { route: "/ayudar?como=voluntario", path: "/ayudar" });
    await user.click(await screen.findByLabelText("Fines de semana"));
    await fillPerson(user);
    await user.click(screen.getByLabelText(/Acepto que Fundación Patitas/));
    await user.click(screen.getByRole("button", { name: "Enviar solicitud" }));
    await screen.findByText("Página de gracias");
    expect(api.sendApplication).toHaveBeenCalledWith(expect.objectContaining({ membership: null, volunteer: { availability_ids: [1] } }));
  });
});
