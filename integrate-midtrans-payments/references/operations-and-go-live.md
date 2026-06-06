# Operations And Go-Live

Use this for sandbox testing, live cutover, callback setup, observability, secret management, and production readiness for any Midtrans product path.

Refresh current Midtrans product/API details from `https://docs.midtrans.com/llms.txt` before sandbox or live cutover work.

## Environment And Secrets

Keep sandbox and production isolated:

- server key/client key for Snap/Core,
- BI-SNAP client id, partner id, channel id, client secret, private/public keys,
- merchant ids/handles,
- callback/redirect base URLs,
- product feature flags and activation gates.

Every required runtime variable should be represented in:

- example env file,
- typed env validation or startup validation,
- deployment/secret manager wiring,
- CI drift checks when the project has them,
- operator handoff docs.

Fail fast on missing production secrets. Avoid silent fallback from production to sandbox values.

## Callback URLs

Dashboard/server-to-server notification URLs must be:

- public internet reachable,
- HTTPS in production,
- not localhost,
- not behind auth, VPN, IP blocks, or unusual ports unless Midtrans explicitly supports it,
- not redirecting through 301/302/303 before the handler,
- returning provider-expected 2xx only after verification/acceptance.

Keep these concepts separate:

- payment notification URL: server-to-server state updates,
- recurring/account-linking notification URLs: product-specific callbacks,
- finish/unfinish/error redirects: customer browser UX,
- GoPay/tokenization return URL: browser return and state validation.

## TLS And Webhook Endpoint Compatibility

Current notification docs state that Midtrans webhook delivery supports TLS up to version 1.2. A webhook endpoint hardened to TLS 1.3-only can pass ordinary browser or `curl` checks while Midtrans notifications fail to arrive.

Resolution: keep TLS 1.2 enabled on webhook endpoints. Disable TLS 1.0/1.1, but do not require TLS 1.3 only. Verify from the edge hostname with:

```bash
openssl s_client -connect merchant.example:443 -tls1_2 < /dev/null 2>&1 | head -3
```

A non-zero exit means the endpoint refuses TLS 1.2 and should not be used as the dashboard notification URL.

## Midtrans Source IP Allowlist

If the merchant runs a strict ingress firewall or WAF, allow Midtrans notification source IPs/CIDRs. Use `scripts/print_midtrans_webhook_ips.sh` to print the current docs-derived production/sandbox and legacy lists in labeled, nginx, or CSV format:

```bash
./scripts/print_midtrans_webhook_ips.sh production --as nginx
```

Verify the list against `https://docs.midtrans.com/docs/ip-address` before applying production rules. IP allowlists are not proof of authenticity; webhook handlers still must verify signatures. Do not allowlist resolved IPs for outbound calls to Midtrans API domains; docs require domain-based allowlisting for API endpoints.

## Structured Logging

Log enough to debug without leaking secrets:

- route/action,
- order id,
- merchant/provider order id,
- provider reference,
- payment method,
- provider,
- status/result,
- response code,
- request id/correlation id,
- latency,
- safe error code/message.

Redact:

- server key,
- client secret,
- private key,
- access token,
- customer authorization token,
- auth code,
- payment option token,
- signatures,
- cookies/session tokens,
- full unrestricted customer PII,
- full unrestricted provider payloads.

## Sandbox Smoke

Use [sandbox-interaction-helper.md](sandbox-interaction-helper.md) when the merchant wants concrete commands, webhook replay fixtures, BI-SNAP signing dry-runs, status polling, or a copy-safe sandbox evidence report.

For every enabled method:

1. Create a sandbox transaction.
2. Confirm customer-facing instruction/recovery page after refresh.
3. Complete or simulate payment in sandbox.
4. Verify notification updates local state exactly once.
5. Replay the notification and confirm idempotency.
6. Poll status and confirm mapping matches local state.
7. Test expiry/cancel/retry behavior.

For Snap:

- test popup/redirect/embed path chosen by merchant,
- test Get Status before method selection,
- test GoPay QR/deeplink paths if enabled,
- test duplicate/failure attempts within one Snap session.

For BI-SNAP:

- test access-token refresh,
- test signature failure handling,
- test each callback type,
- test stale callback after paid,
- test disabled/unactivated method gating.

For GoPay tokenization:

- test link, return, binding, inquiry, linked payment, unlink,
- test missing/changed payment option token,
- test PayLater unavailable path.

For Subscriptions:

- test create, disable, resume, cancel,
- test first-charge tokenization failure,
- test retry_schedule with sandbox-induced failure,
- test Recurring Notification URL routes to the recurring handler, not the one-time handler.

For Mobile (Snap WebView):

- test on a real device (not just simulator) for at least one wallet (GoPay/ShopeePay),
- test deeplink return when the app is foregrounded, backgrounded, and killed (cold-start),
- test WebView intercept of the finish redirect dismisses the WebView and triggers backend status verification.

For Payment Link:

- test single-use link payment,
- test reusable link with usage_limit > 1 (each buyer should land as a distinct transaction_id),
- test expired link rejection.

For Refunds:

- test full refund (transaction_status: refund),
- test partial refund and accumulating refunds against gross_amount,
- test idempotent retry with the same refund_key (must not double-refund),
- test refund on a non-refundable method (admin UI must reject before API call).

## Go-Live Checklist

- Production credentials installed and sandbox credentials removed from production.
- Production callback URLs configured in Midtrans dashboard (Payment Notification URL plus Recurring Notification URL when subscriptions or recurring is in scope).
- Payment methods activated in production account.
- Feature flags match activation state.
- Webhook endpoint accepts TLS 1.2; do not configure the notification URL as TLS-1.3-only.
- Midtrans notification source IPs/CIDRs allowlisted on strict production firewall/WAF rules when required (see `scripts/print_midtrans_webhook_ips.sh`).
- Logs visible in production runtime.
- Alerting or dashboard exists for provider 4xx/5xx and webhook failures.
- Refund/cancel/manual reconciliation runbook exists if those actions are supported.
- First live transaction is monitored end-to-end with order id and provider reference.
- Any final live transaction test is explicitly approved by the merchant and is not presented as a normal sandbox smoke.
