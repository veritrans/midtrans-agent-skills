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

## Scenario 12: BI-SNAP Implementation Depth

Prompt:

```text
Use integrate-midtrans-payments to implement BI-SNAP QRIS and virtual account in this app with our own payment UI. We want a production-shaped implementation, not just a single charge call.
```

Expected behavior:

- Loads `merchant-readiness-preflight.md`, `project-adaptation.md`, and `bisnap-core.md`.
- Finds the merchant's order, payment, repository, environment, logging, and test boundaries before proposing code.
- Obtains a cached B2B access token using the `clientId|timestamp` RSA-SHA256 access-token signature, refreshes with an expiry buffer, and guards refresh races.
- Builds product payloads server-side, signs the transactional request as `method:path:accessToken:bodyHashHex:timestamp` (HMAC-SHA512), and signs the exact serialized body without reformatting.
- Moves the local payment attempt to `creating_payment` before the provider call and `awaiting_payment` after the charge is accepted.
- Persists provider reference, QR/VA instructions, expiry, and latest provider status for recovery after refresh.
- Maps BI-SNAP status codes through one shared, idempotent, monotonic rule, and reconciles on the merchant order id / `trxId`.
- Keeps private keys, client secret, access tokens, and signatures off the frontend.

## Scenario 13: BI-SNAP Notification Routing And Signature

Prompt:

```text
Use integrate-midtrans-payments to wire BI-SNAP notifications for QRIS, VA, and Direct Debit. Our dashboard lets us register callback URLs.
```

Expected behavior:

- Uses product-specific standardized callback paths (for example `/v1.0/debit/notify`, `/v1.0/qr/notify`, `/v1.0/va/notify`) rather than one merged route, and confirms exact paths against current docs.
- Verifies the notification signature over the exact request path (`POST:requestPath:bodyHashHex:timestamp`) using the Midtrans public key, and warns that a path-rewriting dispatcher breaks verification.
- Returns the BI-SNAP-standard response envelope per product (for example VA `2002500` echoing `virtualAccountData`; QR `2005200`; debit `2005600`), not a generic `200 OK`.
- Reads the raw body for verification, verifies before mutating, and gates any verification bypass to non-production only.
- Reads the per-product status field (`additionalInfo.paymentFlagStatus` for VA; `latestTransactionStatus` for QR/debit) and reconciles on the right key.
- Keeps notification handling idempotent and monotonic and redacts secrets, signatures, and full payloads from logs.

## Scenario 14: Refund Idempotency

Prompt:

```text
Use integrate-midtrans-payments to add a partial refund flow for our settled GoPay orders. The customer support tool may double-click the refund button.
```

Expected behavior:

- Loads `refund-operations.md`.
- Routes GoPay to the direct refund endpoint when current docs and merchant activation support it.
- Generates and persists a deterministic `refund_key` before the provider call.
- Takes a row-level lock or optimistic-concurrency token before issuing the refund.
- Maintains a `total_refunded` ledger and rejects over-refund attempts.
- Allows refund only from settled or accepted partial-refund states; treats `capture` as cancel/void unless current docs explicitly allow refund.
- Handles `partial_refund` and `refund` notifications idempotently.
- Does not assume bank transfer or OTC methods support Midtrans refund APIs.

## Scenario 15: Reusable Payment Link

Prompt:

```text
Use integrate-midtrans-payments to create a reusable Payment Link for our event registration. We expect 50 attendees to pay through the same link, and each registration should appear as a distinct order in our admin.
```

Expected behavior:

- Loads `payment-links.md`.
- Sets `usage_limit` to 50 explicitly instead of relying on the API default.
- Persists the `payment_url`, Payment Link `order_id`, expiry, and local invoice/order linkage before sending the URL.
- Reconciles reusable-link payments by transaction-level identifiers such as `transaction_id` or transaction-specific provider order id, not only by the Payment Link id.
- Verifies notifications with the same Snap/Core signature formula and raw amount string.
- Confirms dashboard Payment Notification URL and activated methods.
- Plans an operator/admin cancellation path because customers cannot self-cancel the link page.

## Scenario 16: Core API Custom Card UI

Prompt:

```text
Use integrate-midtrans-payments to build a custom card checkout using Midtrans Core API. We also need Alfamart fallback for customers who do not use cards.
```

Expected behavior:

- Loads `core-api-classic.md`, plus merchant readiness and project adaptation references.
- Chooses classic Core API only because the merchant explicitly wants custom card UI and OTC fallback.
- Tokenizes cards in the browser with `MidtransNew3ds.getCardToken`; raw PAN/CVV never reaches the merchant backend.
- Charges from the backend with `POST /v2/charge`, `payment_type: "credit_card"`, 3DS enabled, and backend status verification after 3DS.
- Keeps saved-card, two-click, one-click, and recurring flows separate and gated by merchant activation.
- Implements `cstore` Alfamart/Indomaret charge handling with persisted `payment_code`, expiry, and customer instructions.
- Reuses Snap/Core notification signature verification and idempotent status mapping.
- Avoids BI-SNAP QRIS/VA request shapes for this classic Core API path.

## Scenario 17: Managed Card Subscription

Prompt:

```text
Use integrate-midtrans-payments to implement monthly card subscriptions. We want Midtrans to own the billing schedule and notify our app for every recurring charge.
```

Expected behavior:

- Loads `subscriptions.md`, plus merchant readiness and project adaptation references.
- Chooses one recurring owner: Midtrans-managed Subscription API, not a merchant cron running parallel charges.
- Confirms recurring/subscription merchant activation and Recurring Notification URL setup.
- Requires an initial successful save-card flow and persists `saved_token_id` plus expiry before creating the subscription.
- Creates subscriptions with unique `name`, string `amount`, schedule, metadata, and retry policy aligned with merchant dunning.
- Stores the returned subscription id and keeps a `charge_attempts[]` ledger keyed by recurring charge order id.
- Verifies recurring charge notifications with the Snap/Core signature formula and maps each attempt idempotently.
- Separates disable/resume/cancel semantics for operator workflows.

## Scenario 18: Mobile Snap WebView And GoPay Return

Prompt:

```text
Use integrate-midtrans-payments to add Midtrans payment to our React Native app. We want Snap hosted checkout in a WebView and need GoPay app-switch return to work.
```

Expected behavior:

- Loads `merchant-readiness-preflight.md`, `project-adaptation.md`, `snap-checkout.md`, and `mobile-sdk.md`.
- Chooses Snap WebView as the default mobile path, not a deprecated native SDK or an unofficial React Native plugin.
- Confirms the backend creates Snap tokens server-side and never exposes the server key to the app.
- Persists local payment state before opening the WebView for background and cold-start recovery.
- Opens the exact Snap `redirect_url` without rewriting, shortening, or encoding it.
- Configures WebView or in-app browser behavior for JavaScript, cookies, Midtrans hosts, and wallet deeplinks.
- Sets GoPay `callback_url` only after the merchant app deeplink is registered and tested; handles QR scan return separately.
- Treats finish/unfinish/error/wallet return as UX hints, then verifies payment status through the backend or webhook.
- Tests on real Android and iOS devices for wallet app-switch, unknown URL schemes, and cold-start recovery.

## Scenario 19: Production Webhooks Never Arrive

Prompt:

```text
Use integrate-midtrans-payments to debug why Midtrans production webhooks never arrive. Sandbox webhooks worked. curl to our endpoint succeeds.
```

Expected behavior:

- Loads `operations-and-go-live.md` before changing webhook code.
- Checks whether the production edge endpoint accepts TLS 1.2 instead of requiring TLS 1.3 only.
- Suggests `openssl s_client -connect <host>:443 -tls1_2` against the exact dashboard notification hostname.
- Checks strict firewall/WAF allowlists against current Midtrans notification source IPs/CIDRs using `print_midtrans_webhook_ips.sh`.
- Warns that IP allowlists are not authenticity proof; signature verification is still required.
- Confirms the Payment Notification URL is public HTTPS, has no auth/VPN/unusual port, and does not redirect before the handler.
- Uses edge logs to distinguish TLS/WAF drops from application signature or status-mapping bugs.

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
