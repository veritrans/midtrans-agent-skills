# Snap Checkout Playbook

Use this when the merchant asks for Snap-only checkout, hosted checkout, Snap popup/redirect/embed, Snap token creation, Snap status polling, Snap retry behavior, Snap expiry behavior, or Snap webhook debugging.

Always refresh current docs from `https://docs.midtrans.com/llms.txt`, especially Snap Integration Guide, Snap API overview, Snap JS, request body parameters, advanced features, notifications, transaction status cycle, sandbox testing, and switching to production. For concrete sandbox smoke commands and webhook replay, use [sandbox-interaction-helper.md](sandbox-interaction-helper.md).

Before building Snap code, complete [merchant-readiness-preflight.md](merchant-readiness-preflight.md). At minimum confirm account/MID state, sandbox keys, Snap method activation, display mode, dashboard notification URL, redirect URLs, expected customer flow, retry behavior, and the proof level required for this engagement.

## Product Fit

Use Snap when the merchant accepts Midtrans-hosted payment UI, wants the fastest integration, wants card data off merchant servers, or wants broad payment method coverage without owning method-specific payment UI.

Prefer Snap unless the merchant explicitly needs custom payment method UI, direct API ownership for QR/VA/e-wallet flows, or a tokenized wallet flow that belongs to another Midtrans product path.

Snap has two common checkout strategies:

- **Snap as the full payment page**: omit `enabled_payments`; Snap shows all active methods for the merchant account.
- **Merchant checkout plus Snap method screen**: merchant collects cart/address/method, backend creates a Snap token with one or a few `enabled_payments` values, and frontend opens Snap for that selection.

When a merchant has an existing payment abstraction, classify each method before writing code. It is valid for one app to use Snap for card/OTC while using another Midtrans product for app-owned QR/VA/e-wallet flows, as long as the provider owner per method is explicit.

## Snap Implementation Flow

1. Inspect existing order, payment, callback, logging, and env boundaries.
2. Confirm Snap account readiness: account/MID, sandbox keys, activated methods, notification URL, finish/unfinish/error redirects, and proof level.
3. Create or reuse the merchant's local order.
4. Move the local order/payment attempt into `creating_payment` or an equivalent state before calling Midtrans.
5. Build the Snap token payload server-side.
6. Call the Snap transaction endpoint with Basic Auth using the server key and a blank password.
7. Persist the returned token, provider order id, selected method, expiry, and safe request metadata.
8. Move the local order/payment attempt into `awaiting_payment`.
9. Open Snap through popup, redirect, or embedded mode.
10. Treat frontend callbacks as UX hints only.
11. Fulfill only from a verified webhook or trusted backend status reconciliation.
12. Keep retry, cancellation, and expiry paths explicit.

## Token Creation Contract

Server-side only:

- Sandbox transaction endpoint: `https://app.sandbox.midtrans.com/snap/v1/transactions`
- Production transaction endpoint: `https://app.midtrans.com/snap/v1/transactions`
- Auth: `Authorization: Basic base64(serverKey + ":")`
- Keep server key only on the backend. The client key is for Snap JS — it is not a secret and is safe to expose on the public frontend.

Token request checks:

- `transaction_details.order_id` must be unique per transaction attempt after a transaction exists.
- `transaction_details.gross_amount` is an integer IDR amount for Snap requests.
- If `item_details` is included, net item total must equal `gross_amount`; negative-price items can represent discounts if current docs allow the use case.
- Use `enabled_payments` only when the merchant intentionally restricts payment methods.
- Validate `enabled_payments` against the merchant's configured Snap-owned methods before calling the provider.
- Include customer details when available, but do not collect/store unnecessary PII.
- Set expiry intentionally for async methods. `expiry` controls payment-method expiry; `page_expiry` controls Snap page/token lifetime.
- Consider a per-transaction `notification_url` only when the project needs route-specific callback handling; otherwise use dashboard Payment Notification URL.

Common `enabled_payments` examples include `credit_card`, `gopay`, `shopeepay`, `bca_va`, `bni_va`, `bri_va`, `permata_va`, `other_va`, `alfamart`, and `indomaret`. Do not assume this list is complete or active for the merchant; confirm against current docs and dashboard activation.

Example token payload:

```json
{
  "transaction_details": {
    "order_id": "ORDER-12345-1700000000",
    "gross_amount": 150000
  },
  "customer_details": {
    "first_name": "Customer",
    "email": "customer@example.test",
    "phone": "081234567890"
  },
  "item_details": [
    {
      "id": "SKU-001",
      "price": 150000,
      "quantity": 1,
      "name": "Product Name"
    }
  ],
  "enabled_payments": ["credit_card", "alfamart"],
  "callbacks": {
    "finish": "https://merchant.example/orders/12345"
  },
  "expiry": {
    "start_time": "2026-06-03 14:00:00 +0700",
    "duration": 2,
    "unit": "hours"
  }
}
```

Generate `expiry.start_time` at request time in `yyyy-MM-dd HH:mm:ss +0700`; it is optional, so omit it to default to transaction creation time. The example value above is illustrative only — a past `start_time` shortens or immediately ends the payment window, and async methods (bank transfer, e-wallet) only begin counting from it.

Do not paste a real customer email, real phone number, server key, client key, or full provider response into examples, logs, tickets, or chat.

## Per-Transaction Notification Routing

Snap exposes two HTTP request headers for token creation that change webhook delivery for that single transaction:

| Header | Effect |
| --- | --- |
| `X-Override-Notification: <url>` | Replaces dashboard Payment Notification URL for this transaction only |
| `X-Append-Notification: <url1>,<url2>` | Adds extra notification URLs (up to 3) on top of the dashboard URL |

Use cases:

- Multi-tenant SaaS where each tenant has its own webhook handler.
- Migration window when a new handler is being validated alongside the legacy handler.
- Per-product routing when a single account serves multiple distinct workloads.

Constraints:

- Both headers accept comma-separated URLs and require HTTPS in production.
- Override silently replaces the dashboard URL for that one transaction; if the override is unreachable, the notification is lost (Midtrans does not fall back to the dashboard URL).
- Each appended URL receives the same payload independently; merchant handlers must remain idempotent across all of them.

Treat these headers as advanced features. Default to the dashboard URL unless one of the use cases above applies.

## Snap State Model

Every Snap implementation needs a local state model. At minimum, agents should look for or create equivalents of:

| Local state | Meaning | Provider action |
| --- | --- | --- |
| `selecting_method` | Customer has not requested payment yet | None |
| `creating_payment` | App has committed to creating a provider attempt | Snap token request in flight |
| `awaiting_payment` | Snap token exists and customer can pay | Webhook/status decides final state |
| `paid` | Verified settlement/capture accepted | Fulfill |
| `failed` / `cancelled` / `expired` | Provider or local timeout ended the attempt | Show retry path |
| `refunded` / `partially_refunded` | Provider refund event accepted | Reconcile fulfillment/accounting |

Field-tested rule: set `creating_payment` before the provider call. If the Snap API fails, the order still has an audit trail and the app can show a recoverable payment error.

Persist enough data to resume after refresh:

- internal order id,
- Midtrans `order_id`,
- Snap token and redirect URL when returned,
- selected local method and `enabled_payments`,
- local expiry and provider expiry,
- latest provider `transaction_status`,
- safe provider metadata for debugging.

Do not let a late `pending`, `deny`, `cancel`, or `expire` notification overwrite a paid, fulfilled, shipped, delivered, or refunded order unless the provider event is a valid refund transition.

## Frontend Display Modes

Display modes share the same backend token:

| Mode | How it opens | Use when |
| --- | --- | --- |
| Popup | Load `snap.js`, call `window.snap.pay(token, callbacks)` | The customer should stay on the merchant checkout page. |
| Redirect | Redirect customer to `redirect_url` | The merchant wants the simplest frontend integration or avoids loading Snap JS. |
| Embedded | Load `snap.js`, call `window.snap.embed(token, { embedId, ...callbacks })` | The merchant wants Snap inside a dedicated payment container. |

Use sandbox Snap JS in development and production Snap JS in production:

- Sandbox: `https://app.sandbox.midtrans.com/snap/snap.js`
- Production: `https://app.midtrans.com/snap/snap.js`

Frontend callbacks are UX hints only:

- `onSuccess`: move customer to an order/status page and let the backend verify.
- `onPending`: show awaiting-payment UI and recovery instructions.
- `onError`: show a retry path and keep the order recoverable.
- `onClose`: preserve token/order state if the customer can retry; do not assume provider cancellation.

`uiMode: "deeplink"` or `"qr"` can influence e-wallet display in popup/embed flows, but current docs and merchant activation should decide whether to rely on it. Redirect flows can also use finish-url query parameters for customer UX; always confirm current docs before coding this path.

`window.snap.hide()` can close a popup programmatically, but local cancellation still needs provider/state reconciliation.

If the page uses Content Security Policy, check current Snap JS and asset domains in the docs and add only the required script/connect/frame/image allowances.

For mobile apps (Android, iOS, Flutter, React Native), Snap is typically embedded via WebView with deeplink return for e-wallet app-switch flows. See [mobile-sdk.md](mobile-sdk.md).

## Webhook And Status Handling

Do not fulfill from Snap JS callbacks. Fulfillment requires a verified notification and/or trusted backend status lookup.

Classic notification signature:

```text
SHA512(order_id + status_code + gross_amount + serverKey)
```

Use the raw `gross_amount` string from the notification payload. Do not parse and reformat it before hashing.

Webhook endpoint requirements:

1. Read the raw provider fields needed for verification and status mapping.
2. Verify `signature_key` before mutating orders.
3. Map `transaction_status` and `fraud_status` through one shared payment-status rule.
4. Be idempotent; duplicate notifications must return success after safe processing.
5. Return 2xx quickly after accepting or safely recording the notification.
6. Log only allowlisted fields such as order id, payment type, transaction status, fraud status, and provider reference.

Status rules:

- `settlement`: paid.
- `capture`: paid only when fraud status is accepted; challenge usually remains pending.
- `pending`: awaiting payment.
- `deny`, `cancel`, `expire`, `failure`: failed/cancelled/expired according to project terminology.
- `refund`, `partial_refund`: refunded or partially refunded.

Core API status lookup is useful for recovery and polling. With Snap, a status lookup can return not found before the customer selects/confirms a method. Treat that as "not attempted yet", not as a fatal order failure.

Snap session cancel/expire and Core API transaction cancel/expire are different:

- Before method selection, use Snap session endpoints if the token/page itself must be invalidated.
- After a transaction exists, use transaction status/cancel/expire endpoints for the underlying payment.

## Server-Side Endpoints Used With Snap

Snap merchants often still need server-side recovery endpoints. They live on **two different host families — do not mix them**:

- Core API (status, cancel, expire, refund): `https://api.midtrans.com` (live) / `https://api.sandbox.midtrans.com` (sandbox).
- Snap API (token creation and Snap-session cancel/expire): `https://app.midtrans.com` (live) / `https://app.sandbox.midtrans.com` (sandbox).

Use the server key with Basic Auth and confirm current docs before shipping:

| Purpose | Host family | Endpoint shape | Use |
| --- | --- | --- | --- |
| Get status | Core API (`api.*`) | `GET /v2/{order_id}/status` | Reconcile order page, polling, webhook gaps, and support investigations. |
| Cancel transaction | Core API (`api.*`) | `POST /v2/{order_id}/cancel` | Cancel pending/capture transactions when allowed by provider state. |
| Expire transaction | Core API (`api.*`) | `POST /v2/{order_id}/expire` | End a pending payment when local order expiry requires it. |
| Refund transaction | Core API (`api.*`) | `POST /v2/{order_id}/refund` | Start full or partial refund when method and merchant policy allow it. |
| Cancel Snap session | Snap API (`app.*`) | `POST /snap/v1/transactions/{snapToken}/cancel` | Invalidate an unused Snap page before a payment transaction exists. |
| Expire Snap session | Snap API (`app.*`) | `POST /snap/v1/transactions/{snapToken}/expire` | Expire an unused Snap page/token before method selection. |

The Snap token host (`app.*`) is not the Core API host (`api.*`); reusing one base for the other returns 404. Match the sandbox/live host to the key environment.

Do not call production endpoints for ordinary tests. Use sandbox credentials, local deterministic signature checks, or an explicitly approved live smoke runbook.

## Retry, Expiry, And Recovery

Retry behavior depends on whether the customer has created a transaction inside the Snap session.

| Situation | Recommended behavior |
| --- | --- |
| Token exists and no method has been selected | Reopen the same token while the token/page is valid. |
| Token expired before any transaction exists | Create a new token with a new provider attempt id or clearly versioned provider order id. |
| Customer selected a method and payment failed | Do not blindly reuse the same provider order id; create a new attempt according to current docs and local order rules. |
| Customer closed popup | Keep local order recoverable; show continue payment or choose another method based on status lookup. |
| Local order expired | Mark local order expired and expire/cancel provider side only when the provider state supports it. |

Use both local expiry and provider expiry intentionally. The local expiry drives app UX and order cleanup. Snap `expiry` and `page_expiry` control provider payment availability and token/page availability.

Multiple payment attempts inside one Snap session can produce several notifications for the same provider order id. Accept duplicate and failed-attempt notifications safely, then fulfill only from a verified successful state.

Desktop QR flows and mobile deeplink flows can produce different `payment_type` values for a method family. Reconcile by order id and status, not by display label alone.

## Advanced Snap Feature Catalog

Load current docs before implementing any advanced feature. These are decision prompts for agents, not a substitute for the live API reference.

| Feature | When to consider it | Implementation note |
| --- | --- | --- |
| `expiry` | Async method availability must match order expiry | Include `start_time` explicitly when the merchant needs deterministic expiry. |
| `page_expiry` | Snap page/token should close before default lifetime | Use for short-lived checkout sessions. |
| `custom_field1`-`custom_field3` | Merchant needs dashboard/search metadata | Keep values non-sensitive and short. |
| Customer collection controls | Merchant wants Snap to collect name/email/phone/address | Decide which fields are required, optional, or not collected. |
| Dashboard theme/preferences | Merchant wants branded Snap UI | Prefer dashboard configuration over code. |
| Customer-imposed payment fee | Merchant wants to pass some payment fee to customer | Confirm merchant pricing/legal policy and active method support; add the fee as an item so net `item_details` total still equals `gross_amount`. |
| Credit card 3DS | Card payments are enabled | Keep 3DS enabled unless Midtrans and merchant risk owners explicitly approve otherwise. |
| Saved card / subsequent card payment | Returning customers need faster card checkout | Store returned card token fields server-side and respect expiry. |
| Recurring card payment | Subscription or scheduled billing | Separate first-payment tokenization from later recurring charges. |
| Pre-authorization / capture later | Merchant ships later or needs manual review | Track authorization, capture, and expiry states distinctly. |
| Online/offline installment | Merchant offers installment plans | Confirm bank/channel activation and valid term values. |
| BIN filter / bank routing | Merchant needs card routing or issuer filtering | Keep rules explicit and test sandbox declines. |
| GoPay callback URL | Merchant needs mobile return behavior after e-wallet flow | Confirm deeplink vs QR behavior on desktop, Android, and iOS. |
| Custom VA number/description | Merchant wants bank-transfer reconciliation UX | Validate bank support, length, and uniqueness rules. |
| Convenience-store receipt text | Merchant wants clearer OTC payment instructions | Keep text customer-safe and localized. |
| Item-level discount | Merchant needs line-item discount visibility | Use negative-price items only when net total equals `gross_amount`. |
| Promo management | Merchant wants dashboard-managed promotions | Do not implement duplicate promo logic in the app unless business rules require it. |

Do not enable an advanced feature just because it exists. Tie every feature to a merchant need, dashboard activation, local state impact, and test evidence.

## Snap Troubleshooting Matrix

| Symptom | Likely cause | Agent check |
| --- | --- | --- |
| 401 from token endpoint | Wrong key type or sandbox/live mismatch | Check server key is backend-only and endpoint environment matches key environment. |
| Method unavailable in Snap | Method inactive or invalid `enabled_payments` value | Check dashboard activation and local method-to-Snap-code mapping. |
| Duplicate order id error | Reused provider order id after a transaction exists | Create a new attempt id and keep local order linkage. |
| Webhook signature mismatch | Wrong server key or reformatted amount | Recompute using raw `gross_amount` string from payload. |
| Order remains pending after customer paid | Callback URL unreachable, invalid signature, stale status mapping, or missing idempotency | Inspect webhook logs, status lookup, and state transition guard. |
| Status lookup returns not found after token creation | Customer has not selected/confirmed a method yet | Treat as not attempted, keep order recoverable. |
| Popup closes without payment | Customer closed Snap or token/page expired | Preserve order state and show continue/retry options. |
| Snap JS blocked | Wrong JS URL or CSP blocks script/frame/connect domains | Use environment-specific Snap JS URL and current CSP domains. |

## Snap Production Checklist

- Sandbox and production server/client keys are separated.
- Backend token endpoint uses server key only; frontend uses client key only.
- Sandbox Snap JS URL is not used in production.
- Production dashboard methods are activated for every `enabled_payments` value.
- Production Payment Notification URL is public HTTPS and returns 2xx without redirects.
- Finish/unfinish/error redirects are UX redirects, not fulfillment signals.
- Signature verification uses the production server key in production.
- Webhook handler covers `settlement`, `capture`, `pending`, `deny`, `cancel`, `expire`, `failure`, `refund`, and `partial_refund`.
- Webhook handler is idempotent and monotonic.
- Core API status lookup handles not-found-before-method-selection.
- Order retry creates a new provider order id when required and keeps local order linkage clear.
- Local expiry, Snap `expiry`, and `page_expiry` are aligned with merchant UX.
- Advanced features are enabled only after dashboard activation and merchant need are confirmed.
- GoPay deeplink and QR behavior are tested on relevant desktop/mobile/iOS/Android paths when GoPay is enabled through Snap.
- Logs redact keys, signatures, full provider payloads, customer PII, and token-like values.
