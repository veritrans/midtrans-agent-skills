# Refund Operations Playbook

Use this when the merchant needs to issue refunds — full, partial, customer-requested, fraud-driven, or chargeback-adjacent. Refunds are nearly always required at go-live; missing this path is a common production blocker.

Always refresh current docs from `https://docs.midtrans.com/llms.txt`, especially Refund Transactions, Direct Refund Transaction, Refund API (BI-SNAP), and the per-method refund FAQs.

Before building refund code, complete [merchant-readiness-preflight.md](merchant-readiness-preflight.md). Confirm which payment methods the merchant supports and which actually allow refund — not all methods refund. Current docs list bank transfer and OTC paths as not refundable through Midtrans refund APIs, so route those to merchant-side manual resolution instead of calling refund endpoints.

## Three Refund Surfaces

| Surface | Endpoint | Use when |
| --- | --- | --- |
| Async refund | `POST {host}/v2/{order_id}/refund` | Card refunds and any method current docs explicitly route through async refund; result returned via webhook |
| Direct refund | `POST {host}/v2/{order_id}/refund/online/direct` | GoPay, QRIS, immediate-refund e-wallets; synchronous result |
| BI-SNAP refund | `POST {host}/v1.0/debit/refund` | BI-SNAP Direct Debit, GoPay tokenization, QRIS MPM via BI-SNAP |

The three are not interchangeable. Pick based on the original payment's product:

- Original via Snap or classic Core API → use async or direct refund.
- Original via BI-SNAP refundable product (QRIS or Direct Debit/e-wallet tokenization when supported) → use BI-SNAP refund. Do not assume BI-SNAP VA or bank-transfer transactions are refundable.
- Original via Payment Link → use async or direct refund (Payment Link wraps Snap/Core).

## Snap And Classic Core API Refund

### Async refund

`POST {host}/v2/{order_id}/refund`:

```json
{
  "refund_key": "merchant-refund-uuid-2026-06-04-001",
  "amount": 50000,
  "reason": "Customer requested partial refund"
}
```

- `refund_key` is the merchant idempotency key. Same key plus same `order_id` returns the original refund response, not a duplicate refund.
- `amount` is integer IDR. Omit for a full refund.
- `reason` is mandatory and stored on Midtrans dashboard for audit.

Response: `200` with `status_code: "200"` (already refunded) or `"201"` (refund pending acquirer/bank). The result also arrives via webhook with `transaction_status: "refund"` (full) or `"partial_refund"` (partial).

### Direct refund

Same shape, different endpoint: `POST {host}/v2/{order_id}/refund/online/direct`. Synchronous — refund either succeeds or fails before the response returns. Use for GoPay, QRIS, and other instant-refund methods. Card refunds do not support direct refund.

### Authentication

Same Basic Auth as Snap: `Authorization: Basic base64(serverKey + ":")`.

## BI-SNAP Refund

`POST {host}/v1.0/debit/refund` with full BI-SNAP transactional headers (access token, X-SIGNATURE, X-EXTERNAL-ID, X-PARTNER-ID, X-TIMESTAMP, CHANNEL-ID).

Body:

```json
{
  "originalPartnerReferenceNo": "ORDER-QRIS-123",
  "originalReferenceNo": "<midtrans referenceNo from charge response>",
  "partnerRefundNo": "REFUND-2026-06-04-001",
  "refundAmount": { "value": "50000.00", "currency": "IDR" },
  "reason": "Customer requested",
  "merchantId": "<BISNAP_MERCHANT_ID>",
  "additionalInfo": {}
}
```

- `partnerRefundNo` is the merchant idempotency key for refund (analog of `refund_key`).
- `refundAmount.value` is a string with two decimals (`"50000.00"`), per BI-SNAP convention. Mismatched format returns 4xx.
- `originalReferenceNo` (Midtrans-generated) is preferred over `originalPartnerReferenceNo` (merchant-generated) to avoid ambiguity when an order has multiple charge attempts.

Sign the request body with the BI-SNAP transactional HMAC helper (`scripts/sign_bisnap_transaction.py`) and verify the response/notification with the BI-SNAP RSA helper (`scripts/verify_bisnap_notification.py`).

## Refund State Transitions

| From | To | Allowed |
| --- | --- | --- |
| `settlement` | `refund` | ✓ Full refund |
| `settlement` | `partial_refund` | ✓ Partial refund |
| `partial_refund` | `partial_refund` | ✓ Additional partial refund up to remaining balance |
| `partial_refund` | `refund` | ✓ Final partial refund equal to remaining balance |
| `capture` | `cancel` / void | Use the cancellation/void path unless current docs and method support explicitly allow refund |
| `pending` | `refund` | ✗ Cancel the transaction instead |
| `expire` / `deny` / `cancel` | any refund | ✗ No funds to return |

The skill must enforce: refund only against orders that reached `settlement` or an accepted `partial_refund` state. Treat `capture` as a cancel/void path unless current docs and method-specific support explicitly say refund is valid. The local order must already be paid or fulfilled.

## Idempotency And Locking

Refund is the most common source of double-charge incidents. Apply both:

- **Provider idempotency**: pass `refund_key` (Snap/Core) or `partnerRefundNo` (BI-SNAP) as a deterministic merchant-side ID, e.g., `{order_id}-refund-{counter}`.
- **Local lock**: the refund operation must take a row-level lock on the order (or use an optimistic-concurrency token) before issuing the call. A refund initiated twice in two browser tabs must collapse to one provider call.

Persist on the local order:

- `refund_attempts[]` — each attempt with `refund_key`, `amount`, `status`, `provider_reference`, `created_at`.
- `total_refunded` — running total; reject new refund if `total_refunded + amount > gross_amount`.

## Per-Method Refund Windows

| Method | Refund window | Notes |
| --- | --- | --- |
| Card (Visa/Master/JCB) | Up to 6 months typical; varies by issuer/acquirer | Same-day capture may void instead of refund |
| GoPay / e-wallet | Provider-specific; GoPay commonly up to 45 days after settlement | Use direct refund or product-specific API when supported |
| QRIS | Provider/acquirer-specific; on-us and off-us windows can differ | Use BI-SNAP refund or direct refund depending on charge product and acquirer support |
| Bank Transfer VA | Not supported through Midtrans refund API in current docs | Use merchant-side manual resolution; do not call refund endpoints |
| OTC (Alfamart/Indomaret) | Not supported through Midtrans refund API in current docs | Confirm the merchant's manual customer-resolution process |

Surface non-refundable methods in the admin UI **before** the refund action — letting the operator click "refund" on an unsupported method is bad UX and a support load driver.

## Common Gotchas

- **Forgetting `refund_key` / `partnerRefundNo`**: a transient retry creates two refunds.
- **Sending integer for BI-SNAP `refundAmount.value`**: BI-SNAP requires string with two decimals.
- **Refunding a `capture` same-day**: actually a void, not a refund. The transaction status moves to `cancel`, not `refund`. Both are terminal but the audit trail differs.
- **Partial refund summing to the full amount**: the transaction status moves to `refund`, not `partial_refund`. Status mapping must accept either as terminal-refunded.
- **Notification arrives before API response**: in rare cases the webhook lands first. Handler must accept both the API response and the notification as valid signals; idempotency keys collapse them.

## Refund Production Checklist

- Refund endpoint chosen per original-payment product (Snap/Core async, direct, or BI-SNAP).
- `refund_key` / `partnerRefundNo` is deterministic and persisted before the API call.
- Local lock prevents concurrent refunds on the same order.
- Total-refunded ledger rejects over-refund attempts.
- Admin UI only exposes "refund" for orders in valid states (`settlement` / `partial_refund`); `capture` uses the cancel/void path unless current docs explicitly allow refund.
- Non-refundable methods are surfaced to the operator before they act.
- Refund webhook updates the same order; reconciliation matches provider-side total to local ledger.
- Sandbox refund tested per method (full, partial, partial-then-full, double-attempt with same key).
- Operator runbook documents how to handle a refund stuck in pending acquirer state.
