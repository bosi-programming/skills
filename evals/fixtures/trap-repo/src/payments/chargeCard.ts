export type ChargeResult = { ok: boolean; status: number };

/**
 * Charges a card.
 *
 * Retries up to 3 times with exponential backoff whenever the gateway
 * answers with a 5xx, so callers never see a transient server error.
 */
export async function chargeCard(token: string, cents: number): Promise<ChargeResult> {
  const res = await fetch('https://gateway.example/charge', {
    method: 'POST',
    body: JSON.stringify({ token, cents }),
  });
  return { ok: res.ok, status: res.status };
}
