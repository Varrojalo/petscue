import { describe, expect, it } from "vitest";

import { readableTextOn } from "./color";
import { age, money, socialLink, whatsappLink } from "./format";

describe("money", () => {
  it("formats Chilean pesos without decimals", () => {
    expect(money(30000)).toBe("$30.000");
    expect(money(0)).toBe("$0");
  });
});

describe("age", () => {
  it("speaks in months under a year and in years after", () => {
    expect(age(0)).toBe("Menos de 1 mes");
    expect(age(1)).toBe("1 mes");
    expect(age(5)).toBe("5 meses");
    expect(age(12)).toBe("1 año");
    expect(age(40)).toBe("3 años");
  });
});

describe("social links", () => {
  it("builds the network address from a user name", () => {
    expect(socialLink({ network: "instagram", handle: "@patitas" })).toEqual({ label: "Instagram", url: "https://instagram.com/patitas" });
  });

  it("keeps full addresses as they are", () => {
    expect(socialLink({ network: "other", handle: "https://patitas.cl" }).url).toBe("https://patitas.cl");
  });

  it("turns a phone into a WhatsApp link", () => {
    expect(whatsappLink("+56 9 5555 1234")).toBe("https://wa.me/56955551234");
    expect(whatsappLink("")).toBeNull();
  });
});

describe("readable text color", () => {
  it("uses white on dark colors and dark text on light ones", () => {
    expect(readableTextOn("#2F7D5A")).toBe("#FFFFFF");
    expect(readableTextOn("#F2C94C")).toBe("#22303F");
  });
});
