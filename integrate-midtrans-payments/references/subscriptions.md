# Subscriptions And Recurring Billing Playbook

Use this when the merchant needs to charge a customer on a schedule — SaaS subscriptions, monthly memberships, weekly deliveries, or any merchant-driven recurring billing.

Always refresh current docs from `https://docs.midtrans.com/llms.txt`, especially Subscription API, Core API saved-card/recurring transactions, GoPay recurring, and Recurring Notification URL behavior.

Before building subscription code, complete [merchant-readiness-preflight.md](merchant-readiness-preflight.md). Confirm dashboard activation for subscriptions (a separate enablement from regular Snap/Core), the Recurring Notification URL is configured, and the merchant agreement permits no-customer-present charges for the chosen method.

## Two Recurring Models

Midtrans supports two ways to charge on a schedule. They are not interchangeable; agents must pick one and stick with it.

| Model | Owner | Methods | Use when |
| --- | --- | --- | --- |
| **Midtrans-managed Subscription API** | Midtrans schedules and charges | Card, and GoPay only when current docs and merchant activation support it | Merchant wants Midtrans to own the schedule — fewest moving parts |
| **Merchant-driven recurring** | Merchant cron triggers each charge | Card saved-token recurring, GoPay tokenization, BI-SNAP Direct Debit | Merchant has its own billing engine, dunning, retry policy, or needs non-card recurring |

Mixing them — e.g., creating a subscription via Subscription API then also charging the saved card from merchant cron — leads to double charges. Pick one owner.

## Midtrans-Managed Subscription API

The merchant tokenizes the card once (via classic Core API first charge with `save_token_id: true`), then creates a subscription that references the resulting `saved_token_id`.

### Create subscription

`POST {host}/v1/subscriptions`:

```json
{
  "name": "MONTHLY-PRO-2026",
  "amount": "150000",
  "currency": "IDR",
  "payment_type": "credit_card",
  "token": "<saved_token_id>",
  "schedule": {
    "interval": 1,
    "interval_unit": "month",
    "max_interval": 12,
    "start_time": "2026-07-01 09:00:00 +0700"
  },
  "metadata": {
    "merchant_subscription_id": "SUB-MERCH-0001"
  },
  "customer_details": { "email": "customer@example.test" }
}
```

- `name` is the merchant-facing identifier and **must be unique within the merchant account**. Reusing a name returns 4xx, which is the most common Subscription API integration bug.
- `amount` is a **string** for Subscription API (different from the integer Snap uses). Mismatched format returns 4xx.
- `schedule.interval_unit` accepts `day`, `week`, `month`. `max_interval` caps total charges; omit for indefinite.
- `start_time` controls the **first charge moment**. A past `start_time` triggers the first charge immediately upon subscription creation.

Response returns the subscription `id`. Persist it against the merchant subscription record.

### Manage

- `GET /v1/subscriptions/{id}` — read state.
- `POST /v1/subscriptions/{id}/disable` — pause; resume with `/enable`.
- `POST /v1/subscriptions/{id}/cancel` — terminal stop.
- `PATCH /v1/subscriptions/{id}` — update amount, schedule, or token.

Disabling vs cancelling: disable preserves the subscription for resumption; cancel is one-way. Surface both to the operator.

### Retry

Configure `retry_schedule` on subscription create:

```json
"retry_schedule": {
  "interval": 1,
  "interval_unit": "day",
  "max_interval": 3
}
```

Failed charges retry per this policy. Each retry generates a notification; webhook handler must reconcile per attempt, not assume one-charge-per-period.

## Merchant-Driven Recurring

The merchant cron triggers each charge using a previously saved token. Three flavors:

### Card recurring

Same as classic Core API one-click/recurring charge: use the saved card token as `credit_card.token_id` after the first successful save-card transaction and merchant recurring activation:

```json
{
  "payment_type": "credit_card",
  "transaction_details": {
    "order_id": "ORDER-RECUR-2026-07-{YYYYMMDD}-{customer}",
    "gross_amount": 150000
  },
  "credit_card": {
    "token_id": "<saved_token_id>"
  }
}
```

Notes:

- `order_id` must be unique per charge — include the period in the suffix.
- Saved-token recurring indicates customer-not-present (CNP). Merchant agreement and recurring MID activation must permit CNP charges.
- 3DS is typically not invoked for recurring; first-charge 3DS is the friction-anchor.

### GoPay tokenization recurring

For tokenized GoPay wallets (after account linking), the merchant charges with the stored `customer_authorization_token` and `payment_option_token`. See [gopay-tokenization.md](gopay-tokenization.md). The recurring trigger is the merchant's cron; Midtrans does not schedule GoPay charges.

### BI-SNAP Direct Debit recurring

For ATM-linked Direct Debit, the merchant uses BI-SNAP `/v1.0/debit/payment-host-to-host` with the stored bind token, triggered from the merchant cron. See [bisnap-core.md](bisnap-core.md).

## Notification Routing

Recurring payments use a separate notification URL when the merchant configures one. Dashboard exposes:

- **Payment Notification URL** — for one-time transactions.
- **Recurring Notification URL** — for subscription or recurring charges when the merchant configures a separate recurring endpoint.

If the Recurring Notification URL is not set, recurring notifications fall back to the Payment Notification URL. Both URLs use the same SHA-512 signature over `order_id + status_code + gross_amount + serverKey`. `scripts/verify_snap_signature.sh` works unchanged.

The skill should:

1. Detect whether the merchant intends to separate recurring from one-time webhook handlers.
2. If yes, configure the Recurring Notification URL on the dashboard and mount a distinct route in the merchant app.
3. Persist a `is_recurring` flag on the local order so the right ledger gets the credit.

## State Model

Subscriptions need a richer state model than one-time payments:

| State | Meaning |
| --- | --- |
| `active` | Schedule is running |
| `pending_first_charge` | Created but `start_time` in future |
| `inactive` | Disabled by merchant; resumable |
| `expired` | `max_interval` reached |
| `cancelled` | Terminal stop |
| `failed_payment_retry` | Last charge failed; retry pending per `retry_schedule` |
| `failed_payment_terminal` | Retries exhausted; subscription paused or cancelled per merchant policy |

Maintain a `charge_attempts[]` ledger keyed on charge `order_id` to reconcile against notifications.

## Common Gotchas

- **Reused subscription `name`**: 4xx on create. Use a deterministic merchant-side suffix (`{plan}-{customer}-{epoch}`).
- **Past `start_time`**: charges immediately, surprising the merchant who expected delayed start.
- **Mixing Subscription API and merchant cron**: double-charges customers. Pick one model.
- **Forgetting Recurring Notification URL**: webhooks can land on the one-time handler, which may treat them as duplicates of older one-time orders.
- **`amount` as integer**: Subscription API requires string. Snap requires integer. Easy mistake when reusing a charge builder.
- **3DS challenge on first save**: if first-charge 3DS is denied, the `saved_token_id` is never created, and the subscription create call fails with no token. Surface the first-charge failure clearly.

## Subscription Production Checklist

- Subscription product is activated on the merchant account; sandbox parity is verified.
- Recurring Notification URL is configured if the merchant separates handlers.
- Subscription `name` generation is deterministic and uniqueness-tested.
- `retry_schedule` matches merchant dunning policy.
- Operator runbook covers disable/resume/cancel and updating the saved token after card replacement.
- Webhook handler reconciles by charge `order_id` and increments `charge_attempts[]`, not by subscription id alone.
- Customer-facing UI shows next charge date and lets the customer cancel from the merchant app (the cancel call goes to Midtrans).
- For merchant-driven recurring, the cron is idempotent — replaying the same period must not double-charge.
