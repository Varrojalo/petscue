import { request } from "./client";

// Session
export const prepareSession = () => request("/auth/csrf");
export const login = (email, password) => request("/auth/login", { method: "POST", body: { email, password } });
export const logout = () => request("/auth/logout", { method: "POST" });
export const me = () => request("/auth/me");

// Summary and menu counters
export const getSummary = () => request("/dashboard/summary");
export const getCounters = () => request("/dashboard/counters");

// Animals
export const getAnimals = (filters = {}) => request("/dashboard/animals", { params: filters });
export const getAnimal = (id) => request(`/dashboard/animals/${id}`);
export const createAnimal = (data) => request("/dashboard/animals", { method: "POST", body: data });
export const updateAnimal = (id, data) => request(`/dashboard/animals/${id}`, { method: "PATCH", body: data });
export const setFosterHome = (id, teamMemberId) => request(`/dashboard/animals/${id}/foster-home`, { method: "PUT", body: { team_member_id: teamMemberId } });
export const featureAnimal = (id) => request(`/dashboard/animals/${id}/feature`, { method: "POST" });
export const unfeatureAnimal = (id) => request(`/dashboard/animals/${id}/feature`, { method: "DELETE" });
export const registerExit = (id, data) => request(`/dashboard/animals/${id}/exit`, { method: "POST", body: data });

export function uploadPhoto(id, file) {
  const form = new FormData();
  form.append("image", file);
  return request(`/dashboard/animals/${id}/photos`, { method: "POST", form });
}
export const reorderPhotos = (id, photoIds) => request(`/dashboard/animals/${id}/photos/order`, { method: "PUT", body: { photo_ids: photoIds } });
export const deletePhoto = (id, photoId) => request(`/dashboard/animals/${id}/photos/${photoId}`, { method: "DELETE" });

// Catalogs
export const getSpecies = () => request("/dashboard/species");
export const getTraits = () => request("/dashboard/traits");
export const createTrait = (label) => request("/dashboard/traits", { method: "POST", body: { label } });
export const getFosterHomes = () => request("/dashboard/team-members/foster-homes");

// Adoptions (used from the animal page to record a return)
export const registerReturn = (adoptionId, data) => request(`/dashboard/adoptions/${adoptionId}/return`, { method: "POST", body: data });
