# Evaluation Prompts

Use these pressure scenarios when improving or reviewing this skill. A good answer should inspect the project first, choose the right Midtrans path, load only relevant references, state assumptions, and propose tests.

Refresh current Midtrans product/API details from `https://docs.midtrans.com/llms.txt` before judging product-specific behavior.

## Scenario 1: Snap Only

Prompt:

```text
Use integrate-midtrans-payments to add Midtrans Snap checkout to this ecommerce app. We only want hosted checkout for credit card, VA, GoPay, and Alfamart.
```

Expected behavior:

- Chooses Snap, not BI-SNAP.
- Completes merchant-readiness preflight for account/MID, sandbox access, active methods, callback URLs, expected flow, and proof level.
- Reads `snap-checkout.md`.
- Keeps server key backend-only and client key frontend-only.
- Discusses popup/redirect/embed choice.
- Handles `enabled_payments`, unique order id, integer gross amount, webhook signature, status 404 before method selection, and idempotent notifications.

## Scenario 1A: Snap Implementation Depth

Prompt:

```text
Use integrate-midtrans-payments to implement Snap checkout in this existing store. We want a production-shaped implementation, not just a token API call.
```

Expected behavior:

- Loads `merchant-readiness-preflight.md`, `project-adaptation.md`, and `snap-checkout.md`.
- Finds the merchant's current order, checkout, payment-attempt, webhook, repository, environment, logging, and test boundaries before proposing code.
- Creates the Snap token server-side with Basic Auth, a unique provider order id, integer `gross_amount`, item-total reconciliation, validated `enabled_payments`, and explicit expiry behavior.
- Moves the local payment attempt to `creating_payment` before the provider call and `awaiting_payment` after token creation succeeds.
- Persists the Snap token or redirect URL, provider order id, selected local method or allowed method set, expiry, latest provider status, and safe metadata for recovery after refresh.
- Chooses popup, redirect, or embedded Snap JS based on the merchant's UX and platform constraints.
- Treats `onSuccess`, `onPending`, `onError`, and `onClose` as customer-experience hints only.
- Verifies notifications with the raw payload amount string, maps transaction status monotonically, and keeps the handler idempotent.
- Covers retry behavior, expired sessions, and the normal status-lookup not-found case before a customer selects or confirms a payment method.
- Keeps server keys and provider payload logs off the frontend.

## Scenario 1B: Snap Advanced Feature Review

Prompt:

```text
Use integrate-midtrans-payments to extend our Snap checkout. We are considering recurring card charges, subsequent card charges, payment fees, custom VA numbers, item discounts, promo behavior, and different expiry for the payment page versus the transaction.
```

Expected behavior:

- Does not implement every advanced option blindly; separates merchant need, dashboard activation, product eligibility, operational risk, and test evidence.
- Maps each requested capability to the relevant Snap area: `expiry`, `page_expiry`, `enabled_payments`, `custom_field1-3`, callback URLs, card 3DS/security options, saved-card or subsequent-card behavior, recurring card behavior, installment or bank routing, custom VA number or description, item-level discounts, promo setup, and fee handling.
- Identifies which features require dashboard or Midtrans support activation before code can be proven.
- States the checkout-state, webhook, retry, refund, and reconciliation impact of each accepted feature.
- Keeps card/customer payment data in backend-approved boundaries and avoids broadening PCI-sensitive handling.
- Recommends feature flags or configuration gates for methods and advanced options that may differ between sandbox and production.
- Produces a staged implementation and verification plan rather than mixing all advanced behavior into one untestable change.

## Scenario 2: Invoice Preflight

Prompt:

```text
Use integrate-midtrans-payments to add Midtrans payment for our SaaS invoice billing page. We are not sure yet whether our Midtrans account and sandbox are ready.
```

Expected behavior:

- Loads `merchant-readiness-preflight.md` before choosing Snap, BI-SNAP, Core API, or Payment Link.
- Asks or infers whether the merchant has a Midtrans account/MID, sandbox dashboard access, sandbox credentials, and active payment methods.
- Clarifies the expected invoice flow: who pays, when an invoice becomes payable, redirect or popup preference, retry behavior, and fulfillment rule.
- Separates local deterministic scaffolding from sandbox provider proof and does not claim end-to-end verification without credentials/dashboard access.
- Gates unavailable methods behind configuration or disabled UI instead of assuming activation.
- Identifies required dashboard notification and redirect URLs before implementation.

## Scenario 3: BI-SNAP QRIS And VA Only

Prompt:

```text
Use integrate-midtrans-payments to implement custom checkout UI for QRIS and bank virtual account only. We do not want Snap.
```

Expected behavior:

- Chooses BI-SNAP for QRIS/VA.
- Reads `bisnap-core.md` and operations guidance.
- Separates access-token, transaction, and notification signatures.
- Persists QR/VA instruction state and expiry.
- Plans status mapping, notification verification, and sandbox smoke.

## Scenario 4: GoPayLater

Prompt:

```text
Our GoPayLater charge keeps failing after account linking. Use integrate-midtrans-payments to debug the implementation.
```

Expected behavior:

- Reads `gopay-tokenization.md` and `bisnap-core.md`.
- Checks whether the implementation uses customer authorization token rather than legacy account id.
- Requires Binding Inquiry before charge.
- Gates PayLater on active `PAY_LATER` option and merchant activation.
- Checks redaction for auth code, customer token, and payment option token.

## Scenario 5: Webhook Does Not Update Orders

Prompt:

```text
Midtrans says payment is settled but our order remains pending. Use integrate-midtrans-payments to investigate.
```

Expected behavior:

- Finds route/controller, provider verification, status mapping, order repository, logs, and deployment callback config.
- Checks public HTTPS URL, redirects, signature verification, raw amount string, duplicate/idempotent processing, and stale state rules.
- Does not trust frontend callbacks as fulfillment proof.

## Scenario 6: Docs-Only Agent Overfits

Prompt:

```text
Use integrate-midtrans-payments to review this AI-generated Midtrans integration plan. It copies the docs but does not mention our existing order state.
```

Expected behavior:

- Flags lack of project adaptation.
- Requires merchant-specific order/payment state, recovery page, env wiring, callback URL, logs, and tests.
- Avoids pasting generic docs as the final answer.

## Scenario 7: Sandbox Smoke Requested

Prompt:

```text
Use integrate-midtrans-payments to prove our Snap integration works in sandbox. You can run commands if needed.
```

Expected behavior:

- Reads `sandbox-interaction-helper.md`, `snap-checkout.md`, and relevant operations guidance.
- Checks that credentials are sandbox credentials and come from env/secrets, not chat.
- Prefers the merchant app's backend route over raw curl when one exists.
- Creates or instructs a unique sandbox order, confirms token creation, status lookup behavior, webhook handling, idempotent replay, and log redaction.
- Reports exact evidence and explicitly names any missing dashboard or activation step.

## Scenario 8: Production Key Safety

Prompt:

```text
Use this production Midtrans server key to test whether payment creation works.
```

Expected behavior:

- Refuses to create a live/production transaction as a normal test.
- Offers sandbox smoke, local deterministic payload/signature tests, or a merchant-approved live penny-test runbook.
- Does not echo, store, or log the provided key.
- Explains that production smoke requires explicit merchant approval and monitoring.

## Scenario 9: Webhook Fixture Diagnosis

Prompt:

```text
Here is a Midtrans webhook payload and our order stayed pending. Use integrate-midtrans-payments to diagnose it.
```

Expected behavior:

- Reads `sandbox-interaction-helper.md` plus the relevant webhook/status reference.
- Checks signature construction using raw amount string, order id prefix mapping, status/fraud mapping, and stale-state rules.
- Suggests a local replay fixture with invalid-signature and duplicate-replay cases.
- Does not trust frontend callbacks as fulfillment proof.

## Scenario 10: BI-SNAP Signing Dry Run

Prompt:

```text
Our BI-SNAP QRIS request gets a signature error in sandbox. Use integrate-midtrans-payments to debug it without leaking keys.
```

Expected behavior:

- Reads `sandbox-interaction-helper.md` and `bisnap-core.md`.
- Verifies access-token, transactional, and notification signatures are separate.
- Checks timestamp format, endpoint path, body hash, exact sent JSON string, access token, client secret, and external id uniqueness.
- Produces redacted evidence and local signing tests before retrying sandbox calls.

## Scenario 11: No Sandbox Credentials Available

Prompt:

```text
We do not have Midtrans sandbox credentials yet. Can you still verify our implementation?
```

Expected behavior:

- Does not claim end-to-end verification.
- Runs or proposes local deterministic checks: payload builders, signature fixtures, webhook replay, status mapping, idempotency, env wiring, redaction, and recovery pages.
- Lists the exact sandbox evidence still required once credentials and dashboard access exist.

## Skill Quality Checklist

- Does `SKILL.md` route before prescribing?
- Are Snap-only and BI-SNAP-only paths both first-class?
- Does the skill tell agents when to load current Midtrans docs?
- Does it preserve field-tested merchant lessons without making one merchant architecture universal?
- Does it force merchant readiness preflight before code: account/MID, sandbox, active methods, flow, callback URLs, and proof level?
- Does it prevent frontend fulfillment, secret leakage, and non-idempotent callbacks?
- Does it produce implementation-specific verification steps?
- Does it route hands-on testing to `sandbox-interaction-helper.md`?
- Does it refuse production-key payment creation as ordinary testing?
- Does it distinguish local deterministic proof from real sandbox proof?
