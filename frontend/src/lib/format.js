/**
 * Central place for country-specific formats (Chile for now). Screens call these functions instead of
 * formatting by hand, so supporting another country later means changing this file.
 */

export function money(amount) {
  return `$${Number(amount || 0).toLocaleString("es-CL")}`;
}

export function age(months) {
  if (months < 1) return "Menos de 1 mes";
  if (months < 12) return `${months} ${months === 1 ? "mes" : "meses"}`;
  const years = Math.floor(months / 12);
  return `${years} ${years === 1 ? "año" : "años"}`;
}

export const ID_LABEL = "RUT";
export const ID_PLACEHOLDER = "12.345.678-5";
export const PHONE_PLACEHOLDER = "+56 9 1234 5678";
export const LOCALITY_LABEL = "Comuna";
export const EMERGENCY = { name: "Carabineros", number: "133" };

const SOCIAL = {
  instagram: ["Instagram", "https://instagram.com/"],
  facebook: ["Facebook", "https://facebook.com/"],
  tiktok: ["TikTok", "https://tiktok.com/@"],
  youtube: ["YouTube", "https://youtube.com/@"],
  x: ["X", "https://x.com/"],
};

export function socialLink({ network, handle }) {
  if (handle.startsWith("http")) return { label: SOCIAL[network]?.[0] || "Sitio web", url: handle };
  const [label, base] = SOCIAL[network] || ["Sitio web", ""];
  return { label, url: base + encodeURIComponent(handle.replace(/^@/, "")) };
}

export function whatsappLink(phone) {
  const digits = (phone || "").replace(/\D/g, "");
  return digits ? `https://wa.me/${digits}` : null;
}
