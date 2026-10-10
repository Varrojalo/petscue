/**
 * Rounds a maximum up to a readable number (1, 2 or 5 times a power of ten) so the chart's scale reads well
 * whatever the organization's numbers are: 37 → 50, 120 → 200, 4_300 → 5_000.
 */
export function niceMax(value) {
  if (!value || value <= 0) return 1;
  const power = 10 ** Math.floor(Math.log10(value));
  const fraction = value / power;
  const nice = fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 5 ? 5 : 10;
  return nice * power;
}

export function ticks(max) {
  return [0, max / 2, max];
}
