---
name: integrate-midtrans-payments
description: "Use for Midtrans: Snap/mobile, Core, BI-SNAP, QRIS, VA, GoPay, Payment Link, subscriptions, refunds, webhooks, sandbox."
license: BSD-3-Clause
---

# Integrate Midtrans Payments

## Operating Rule

Treat this as payment-system integration, not generic API wiring. Before changing code, learn the merchant's checkout architecture, payment products, persistence model, callback paths, auth/session boundary, environment management, deployment target, and test harness.

Before recommending a Midtrans product or writing code, complete the merchant readiness preflight: account state, sandbox credentials, active payment methods, expected customer flows, dashboard callback URLs, and the proof level the merchant expects. If those facts are missing and cannot be inferred from the project, pause and ask for them instead of silently assuming them.

Use current Midtrans docs each time. Search `https://docs.midtrans.com/llms.txt` first, then open product pages for the methods being implemented.

## Workflow

1. **Run merchant readiness preflight**
   - Complete [merchant-readiness-preflight.md](references/merchant-readiness-preflight.md) before product choice or code.
   - Infer from env, deploy config, runbooks, tests, provider code, and specs; ask only for missing blockers.
   - Gate unavailable methods with configuration and state what dashboard/merchant action is still required.

2. **Classify the integration**
   - Identify whether the merchant wants hosted checkout, custom UI, recurring/tokenized payments, marketplace/partner behavior, or a hybrid.
   - Map each requested payment method to the intended Midtrans product before writing code.
   - Do not mix Snap, Core API, and BI-SNAP request shapes, auth headers, callback semantics, or status objects.
   - If the merchant need is unclear, read [merchant-decision-tree.md](references/merchant-decision-tree.md) and ask the smallest set of clarifying questions.

3. **Inspect the project (blocking precondition)**
   - Before recommending a product, writing code, or editing config, complete [project-adaptation.md](references/project-adaptation.md).
   - Read repository instructions, env examples, payment docs, checkout/order/payment code, database schema, tests, and deployment config.
   - Find existing HTTP, domain, provider-client, persistence, UI, ops, and logging boundaries; preserve them unless asked to change architecture.
   - If the project cannot be inspected (no access, no repo, greenfield), state that explicitly and stop until the merchant confirms a target stack. Do not synthesize a generic answer.

4. **Design the payment state model**
   - Represent checkout as explicit state: selecting method, creating payment, awaiting payment, paid, failed/cancelled, expired, refunded.
   - Transition the order to a `creating_payment` (or equivalent) state **before** calling the provider so a provider failure never leaves the order in an unidentified state.
   - Persist provider data needed after refresh: merchant order id, provider reference, method, instructions, redirect/QR/VA data, expiry, latest provider status, and safe raw metadata.
   - Make callbacks idempotent and monotonic: never let late `pending` or `cancelled` callbacks overwrite paid/fulfilled/refunded states.

5. **Build provider clients server-side**
   - Prefer official Midtrans libraries when one fits the merchant stack; a thin wrapper still owns env wiring, retry, logging, and payment state.
   - Keep Midtrans keys, signatures, access tokens, customer authorization tokens, and provider payload signing on the backend.
   - For Snap/Core API, use Basic Auth with server key and blank password.
   - For BI-SNAP, keep access-token, transactional, and notification signatures separate.
   - Sign the exact request body bytes/string that will be sent.
   - See [midtrans-runtime-patterns.md](references/midtrans-runtime-patterns.md) for product-specific patterns and gotchas.

6. **Wire callbacks and status recovery**
   - Use publicly reachable HTTPS callback URLs in the merchant dashboard.
   - Verify notification authenticity before mutating orders.
   - Verify browser callbacks or user-facing payment results by backend status lookup, not by trusting frontend callback data.
   - Return 2xx only after safely accepting the callback or deliberately storing it for later reconciliation.

7. **Instrument and verify**
   - Add structured logs for payment creation, provider responses, callbacks, status polling, account linking, cancellation, refund, and reconciliation.
   - Redact secrets, signatures, authorization headers, tokens, customer PII, and full provider payloads unless explicitly allowlisted.
   - Cover status mapping, signature generation/verification, idempotent callback handling, expired payments, disabled methods, refund flows, and env/deployment drift.
   - See [verification-playbook.md](references/verification-playbook.md).
   - When the user asks to prove the integration in sandbox, replay a webhook, poll status, run a smoke test, or diagnose sandbox behavior, read [sandbox-interaction-helper.md](references/sandbox-interaction-helper.md).

8. **Prepare agent-portable output**
   - If asked to package lessons as a skill, keep `SKILL.md` concise and move product details to references.
   - Use only standard frontmatter fields unless a target agent requires more.
   - See [agent-portability.md](references/agent-portability.md) for Claude, Codex, Copilot, Cursor, OpenCode, and tools without native skill support.

## Pathway References

Load only the references relevant to the merchant's request:

| Merchant request or symptom | Read |
| --- | --- |
| Any new Midtrans implementation, migration, or verification request | [merchant-readiness-preflight.md](references/merchant-readiness-preflight.md) and [project-adaptation.md](references/project-adaptation.md) |
| Unsure whether to use Snap, Core API, BI-SNAP, Payment Link, or a hybrid | [merchant-decision-tree.md](references/merchant-decision-tree.md) |
| Snap-only hosted checkout, Snap popup/redirect/embed, Snap webhook or status bugs | [snap-checkout.md](references/snap-checkout.md) |
| Mobile apps/WebView/deeplinks | [mobile-sdk.md](references/mobile-sdk.md) |
| BI-SNAP QRIS, VA, one-time Direct Debit, signatures, access tokens, notification dispatcher | [bisnap-core.md](references/bisnap-core.md) |
| GoPay linking, tokenized wallet, GoPayLater, Binding Inquiry, account unlinking | [gopay-tokenization.md](references/gopay-tokenization.md) |
| Payment Link via API or dashboard, invoice/chat collection, social commerce, no-code link sharing | [payment-links.md](references/payment-links.md) |
| Subscription API, recurring card billing, saved-token recurring charges, recurring notification routing | [subscriptions.md](references/subscriptions.md) |
| Classic Core API card/3DS/one-click/installment, OTC (Alfamart/Indomaret), legacy VA | [core-api-classic.md](references/core-api-classic.md) |
| Cross-product runtime patterns and gotchas not covered above | [midtrans-runtime-patterns.md](references/midtrans-runtime-patterns.md) and current docs |
| Issuing refunds (full or partial), `refund_key`/`partnerRefundNo` idempotency, BI-SNAP refund, refund webhook handling | [refund-operations.md](references/refund-operations.md) |
| Sandbox/live cutover, callbacks, logging, secrets, smoke tests, production readiness | [operations-and-go-live.md](references/operations-and-go-live.md) |
| Sandbox interaction, smoke tests, webhook replay, status polling, BI-SNAP signing dry-runs, credential-safe test commands | [sandbox-interaction-helper.md](references/sandbox-interaction-helper.md) and [scripts/README.md](scripts/README.md) |
| Improving this skill or checking whether an agent follows it correctly | [evaluation-prompts.md](references/evaluation-prompts.md) and [evaluations.json](evaluations.json) |

## Critical Pairing Rules

- **Snap `gross_amount`**: integer when **creating** a Snap token; raw provider string when **verifying** the notification signature. Hashing a reformatted amount is the most common Snap signature bug.
- **BI-SNAP signatures**: three independent helpers — access-token (asymmetric RSA-SHA256), transaction (HMAC-SHA512 over `method:path:accessToken:bodyHashHex:timestamp`), notification (verify with Midtrans public key over `POST:path:bodyHashHex:timestamp`). Never share one helper across the three.
- **GoPay flows**: one-time GoPay Direct Debit, tokenized GoPay wallet payment, GoPayLater, account linking, and unlinking are **five different request shapes**. Tokenized payment additionally requires the `Authorization-Customer: Bearer <customer_authorization_token>` header that one-time payment must not send.
- **Seamless data signing (GoPay linking)**: when current docs require a seamless signature, the data must be `encodeURIComponent(...)`-wrapped **before** RSA-SHA256 signing. Signing the raw string fails silently in sandbox.
- **Refund idempotency**: pass `refund_key` (Snap/Core/Payment Link) or `partnerRefundNo` (BI-SNAP) on every refund call. A retried refund without an idempotency key creates a double refund.
- **Subscription owner**: choose either Midtrans-managed Subscription API or merchant-driven recurring for a customer subscription. Running both creates duplicate scheduled charges.
- **Recurring notifications**: recurring charges may use the dashboard Recurring Notification URL instead of the ordinary Payment Notification URL. Route and reconcile recurring charge attempts separately from one-time payments.

## Output Expectations

When responding to the user, state:

- the detected Midtrans product split and why,
- merchant readiness facts confirmed, inferred, and still missing,
- project-specific files and boundaries found,
- assumptions that need merchant/dashboard confirmation,
- implementation or fix plan with tests,
- exact verification completed and remaining sandbox/live smoke steps.

When implementing, keep changes small, testable, and compatible with the target project's existing payment architecture.
