import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

// jsdom does not implement these browser features used by the pages.
window.scrollTo = () => {};
if (!globalThis.FontFace) {
  globalThis.FontFace = class {
    load() {
      return Promise.resolve(this);
    }
  };
}
