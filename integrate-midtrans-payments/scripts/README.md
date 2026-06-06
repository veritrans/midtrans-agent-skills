# Skill scripts

Deterministic helpers for the highest-leverage Midtrans operations: signature
generation, signature verification, webhook replay, BI-SNAP formatting. Each
script is a thin, auditable reference implementation that matches what
production merchant code does.

These scripts exist because the doc patches in `references/` describe the
rules, and the scripts let an agent (or developer) run them. Both surfaces
should stay in sync — when a script changes, the matching reference should
update too.

## Safety model

1. **No network calls except `replay_snap_webhook.sh`**, which only POSTs to
   a target the operator names. No script reaches out to Midtrans.
2. **No production-key payment creation, ever.** Scripts that need
   `MIDTRANS_SERVER_KEY` refuse keys that do not start with `SB-` unless the
   operator passes `--allow-production`. Even with that flag, no script
   creates a real charge; the most they do is POST to the operator's own
   webhook URL.
3. **No secrets printed to stdout.** Stdout is reserved for machine-parseable
   output (signatures, paths). Debug output goes to stderr, with secrets
   redacted using a leading prefix + asterisks pattern.
4. **No persistence.** Scripts do not write files outside their own argv
   targets. No log files, no `~/.cache` writes, no temp files left behind.
5. **No silent reformatting.** When the body is signed, the byte string used
   for the hash is the byte string the operator passed in.
6. **No tracebacks.** Bad input (missing files, malformed JSON, missing env
   vars, unknown flags) always produces a one-line error message on stderr
   and a non-zero exit code. Scripts never punt a Python stack trace to the
   user.

Use these scripts only with sandbox credentials in development environments.
Audit before running with production credentials, and only with explicit
merchant approval.

## Exit code contract

All scripts follow the same convention:

| Exit | Meaning |
| --- | --- |
| `0` | Success. For verifiers: signature valid. For signers: signature emitted on stdout. For replay: HTTP 2xx received (or dry-run completed). |
| `1` | Behavioral failure. Signature mismatch (verify_snap_signature.sh), invalid signature (verify_bisnap_notification.py), or non-2xx HTTP (replay_snap_webhook.sh). |
| `2` | Bad input. Missing required arg/env, file not found, malformed JSON, sandbox-key safety refusal, unknown flag, or any other operator-correctable mistake. |

Use this contract when wiring scripts into CI checks or pre-commit hooks.

## Dependencies

- `bash` 4+ (any modern macOS or Linux)
- `openssl`
- `python3.10+` standard library
- `python3-cryptography` for the BI-SNAP RSA scripts only
  (`sign_bisnap_access_token.py`, `verify_bisnap_notification.py`)

Install `cryptography` into the merchant's project venv if needed:

```bash
pip install cryptography
```

We do not recommend installing it system-wide.

## Inventory

| Script | Purpose | Algorithm anchor |
| --- | --- | --- |
| `verify_snap_signature.sh` | Verify Snap / Core API notification signature | `SHA-512(order_id + status_code + gross_amount + serverKey)` |
| `replay_snap_webhook.sh` | Build, sign, and POST a Snap notification to a local handler | Same SHA-512 rule above |
| `sign_bisnap_transaction.py` | Compute BI-SNAP transactional `X-SIGNATURE` | HMAC-SHA512 base64 over `method:path:accessToken:bodyHashHex:timestamp` |
| `sign_bisnap_access_token.py` | Compute BI-SNAP access-token `X-SIGNATURE` | RSA-SHA256 base64 over `clientId|timestamp` |
| `verify_bisnap_notification.py` | Verify a BI-SNAP notification signature | RSA-SHA256 verify over `POST:path:bodyHashHex:timestamp` |
| `dry_run_bisnap_sign.py` | Print every artifact (body hash, string-to-sign, headers) that a BI-SNAP request would carry, with secrets redacted | All of the above |
| `format_partner_service_id.sh` | Format `partnerServiceId` to the 8-char left-space-padded shape | Padding rule from current Midtrans VA docs |
| `bisnap_timestamp.py` | Emit an Asia/Jakarta `YYYY-MM-DDTHH:MM:SS+07:00` timestamp | Required by every BI-SNAP request |
| `print_midtrans_webhook_ips.sh` | Print Midtrans notification source IPs/CIDRs for inbound firewall/WAF allowlists (production / sandbox plus legacy; labeled / nginx / csv) | Sourced from current Midtrans IP address docs; verify before applying |

## Typical use cases

**"My Snap webhook handler rejects everything as bad signature."**

```bash
export MIDTRANS_SERVER_KEY=SB-Mid-server-test
./scripts/verify_snap_signature.sh --payload assets/fixtures/snap-notification-settlement.json
```

The bundled Snap fixtures are signed with `SB-Mid-server-test` for deterministic
local checks. If you use a different sandbox key, regenerate the fixture with
`replay_snap_webhook.sh --dry-run` or verify a real payload from your sandbox
environment instead.

If the script reports `OK` but your handler reports invalid, the bug is in
the handler's signature construction (most often: it reformatted
`gross_amount` before hashing).

**"I want to test my handler is idempotent."**

```bash
export MIDTRANS_SERVER_KEY=SB-Mid-server-...
./scripts/replay_snap_webhook.sh \
  --target-url http://localhost:3000/api/payment/webhook \
  --fixture assets/fixtures/snap-notification-settlement.json
# run it again to test idempotency
./scripts/replay_snap_webhook.sh \
  --target-url http://localhost:3000/api/payment/webhook \
  --fixture assets/fixtures/snap-notification-settlement.json
```

The second call must not double-fulfill the order.

**"My BI-SNAP QRIS request fails with signature error."**

```bash
# Save the failing JSON body to /tmp/body.json then:
./scripts/dry_run_bisnap_sign.py \
  --method POST \
  --path /v1.0/qr/qr-mpm-generate \
  --body-file /tmp/body.json
```

The redacted output shows what your code would send. Compare against the
actual sent request (with secrets redacted) to find the divergence.

**"What timestamp value should my client send?"**

```bash
./scripts/bisnap_timestamp.py
# 2026-05-27T14:30:00+07:00
```

**"I need to test my code with an 8-char partnerServiceId."**

```bash
./scripts/format_partner_service_id.sh 12345
#    12345
```

## Cross-references

- Snap signature rules → [references/snap-checkout.md](../references/snap-checkout.md)
- BI-SNAP signature rules → [references/bisnap-core.md](../references/bisnap-core.md)
- Sandbox interaction → [references/sandbox-interaction-helper.md](../references/sandbox-interaction-helper.md)
- Webhook replay safety → [references/sandbox-interaction-helper.md](../references/sandbox-interaction-helper.md)
