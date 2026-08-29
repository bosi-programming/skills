export function parseId(raw: string): number {
  return Number.parseInt(raw.replace(/\D/g, ''), 10);
}
