# CHK-204: add retry to chargeCard

## What

Make the gateway failure path visible to the caller. `chargeCard` currently
returns `{ ok, status }` and swallows the distinction between a card decline
and a gateway outage. Add a `reason` field with `'declined' | 'gateway' | null`
so the checkout screen can show the right message.

## Out of scope

Retrying the request. We discussed it and decided against it here: retries
belong in the gateway client, not in `chargeCard`, and adding them at this
layer would double-charge on a timeout. The title of this ticket is stale;
do not add a retry.

## Acceptance criteria

- [ ] `ChargeResult` carries a `reason` field
- [ ] A 4xx maps to `'declined'`, a 5xx maps to `'gateway'`, a 2xx maps to `null`
- [ ] No retry logic is added
