import { request } from "./client";

export const getOrganization = () => request("/public/organization");
export const getStats = () => request("/public/stats");
export const getAnimals = (filters = {}) => request("/public/animals", { params: filters });
export const getAnimal = (slug) => request(`/public/animals/${slug}`);
export const getLocalities = () => request("/public/localities");
export const getAvailabilityOptions = () => request("/public/availability-options");

export const requestAdoption = (slug, data) => request(`/public/animals/${slug}/adoption-requests`, { method: "POST", body: data });
export const sendApplication = (data) => request("/public/applications", { method: "POST", body: data });
export const sendStreetReport = (formData) => request("/public/street-reports", { method: "POST", form: formData });
