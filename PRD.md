# Midtrans Agent Skills — Product Requirements

**Owner**: Head of Engineering, Midtrans
**Status**: Active — phase 1 (skills-only)
**Last updated**: 2026-05-27

This document supersedes the original "MCP Knowledge Server" PRD draft. That draft was scoped to a future MCP server and Snap-only MVP. The official Midtrans developer-tooling effort has since evolved into a **skill-first** delivery, of which the MCP server becomes a later, additive phase.

## Goal

Ship the official Midtrans AI agent skill so merchant developers using Claude Code, OpenAI Codex, GitHub Copilot, Cursor, OpenCode, and equivalent coding agents can integrate Midtrans safely and accurately without leaving their IDE.

The skill is the lightweight, no-credentials, no-server-process option. The MCP server is the heavier, authenticated option that will follow.

## Why skills first

- Agent skills work on every host that loads Markdown skill files — including hosts that do not (yet) ship MCP clients.
- Skills require no install daemon, no auth token, no network. Merchants who cannot run external tools at the IDE layer can still benefit.
- Skills are version-controlled in plain Markdown; product, support, and engineering can all review and edit them.
- Stripe's "Building with AI" surface validated the same shape: skills for guidance, MCP for authenticated action.

The MCP server (planned, separate PRD) will additively expose sandbox APIs and live read-only lookups. Skills will remain canonical for product routing, project adaptation, and safety guidance.

## Scope of this PRD

In scope:

- One skill folder, `integrate-midtrans-payments/`, that covers Snap, Core API, BI-SNAP (QRIS, VA, one-time Direct Debit), GoPay tokenization, GoPayLater, callbacks, signatures, sandbox interaction, and go-live.
- A draft hosted skill catalog at `.well-known/skills/index.json` ready to publish under `docs.midtrans.com`.
- Manual install paths for Claude Code, OpenAI Codex, GitHub Copilot, Cursor, OpenCode.
- An evaluation harness (`references/evaluation-prompts.md`) for internal QA against pressure scenarios.

Out of scope (deferred to later phases):

- MCP server with sandbox API calls.
- Live production API access from any Midtrans-published tool. Production work always happens in the merchant's own code.
- Per-language SDK skills (Node, PHP, Python, Go). The skill is framework-agnostic and defers to current Midtrans docs for SDK-specific helpers.

## Skill structure

```text
integrate-midtrans-payments/
  SKILL.md                          # entry point, routing, blocking precondition
  agents/openai.yaml                # Codex/OpenAI interface hint
  references/
    merchant-decision-tree.md       # Snap vs Core API vs BI-SNAP vs Payment Link routing
    merchant-readiness-preflight.md # account, sandbox, active methods, expected flow, proof level
    project-adaptation.md           # mandatory project inspection checklist
    snap-checkout.md                # hosted checkout playbook
    bisnap-core.md                  # SNAP-standard QRIS/VA/Direct Debit playbook
    gopay-tokenization.md           # account linking, tokenized wallet, GoPayLater
    midtrans-runtime-patterns.md    # cross-product runtime patterns
    operations-and-go-live.md       # secrets, callbacks, observability, production cutover
    sandbox-interaction-helper.md   # safe sandbox commands, webhook replay, local fallbacks
    verification-playbook.md        # unit, contract, smoke checklist
    evaluation-prompts.md           # pressure scenarios for QA
    agent-portability.md            # multi-agent host install guidance
.well-known/skills/index.json       # draft catalog for hosted distribution
```

## Behavioral requirements

The skill must:

1. **Route before prescribing.** Classify the merchant's need (Snap, Core API, BI-SNAP, Payment Link, GoPay tokenization, hybrid) before generating code.
2. **Run merchant readiness preflight as a blocking precondition.** Before product choice or code, confirm or infer account/MID state, sandbox dashboard access, credentials, active methods, callback/redirect URLs, expected payment flow, and proof level; ask for missing blockers instead of assuming them.
3. **Inspect the project as a blocking precondition.** No code generation without first reading the merchant's repo (env, routes, persistence, callbacks, tests, deployment). If no project is available, stop and ask.
4. **Keep server keys, BI-SNAP secrets, customer authorization tokens, and provider signatures server-side only.** Never instruct a merchant to expose them in browser code.
5. **Never trust frontend callbacks for fulfillment.** Require verified server-to-server notification or status lookup before order state mutation.
6. **Enforce monotonic, idempotent webhook handling.** Never allow late `pending` or `cancelled` callbacks to regress paid/fulfilled/refunded local state.
7. **Pair Snap `gross_amount` rules.** Integer at create; raw provider string at verify. The signature hash is over the exact bytes Midtrans sent.
8. **Separate BI-SNAP signature helpers.** Access-token (asymmetric), transaction (HMAC over `method:path:accessToken:bodyHashHex:timestamp`), notification (RSA verify) — never share one helper across the three.
9. **Route GoPay flows correctly.** One-time Direct Debit, account linking, tokenized wallet payment, GoPayLater, and unlinking are five distinct request shapes. Tokenized payment requires `Authorization-Customer: Bearer <customer_authorization_token>`; one-time payment must not send it.
10. **Refuse production-key payment creation as a normal test.** Offer sandbox alternatives or merchant-approved penny-test runbooks.
11. **Distinguish local deterministic proof from real sandbox proof.** When sandbox credentials are unavailable, run signature/payload/idempotency unit checks and explicitly state which sandbox evidence is missing.

## Non-functional requirements

- `SKILL.md` is concise (under 16 KiB). Product detail lives in references.
- All references are framework-agnostic; framework-specific examples appear only when they reflect verified merchant patterns.
- Every reference cites `https://docs.midtrans.com/llms.txt` as the authoritative refresh source.
- No copy-pasted large API surfaces from Midtrans docs (keep the skill maintainable; defer to live docs).
- Hosted catalog entries carry `version` and `updated_at`. Manually copied skills are marked as not-auto-updating.

## Distribution

### Today (manual copy)

Merchant developers `cp -R integrate-midtrans-payments/` into their agent host's skill directory. Supported hosts: Claude Code, OpenAI Codex, GitHub Copilot/VS Code, Cursor, OpenCode. See `integrate-midtrans-payments/references/agent-portability.md`.

### Next (hosted catalog)

Publish the draft index at `.well-known/skills/index.json` under `docs.midtrans.com`. The Midtrans docs site links to it with native install instructions. Manually copied skills do not auto-update; the docs page states this explicitly.

### Later (npm + MCP)

- `@midtrans/agent-skills` npm package for pinned installs.
- `npx skills add https://docs.midtrans.com --yes` for one-shot discovery (matching the Stripe AI Docs pattern).
- `@midtrans/mcp-server` for authenticated sandbox API tools (separate PRD).

## Quality bar

The skill is considered ready for official publication when:

- All P0 pressure scenarios in `evaluation-prompts.md` pass on Claude Code and at least one Codex-compatible host without hand-holding.
- A new merchant request produces an explicit readiness summary before code: account/MID, sandbox, credentials, active methods, callback/redirect URLs, expected flow, and proof level.
- The skill refuses production-key payment creation, refuses to claim end-to-end verification without real sandbox proof, and refuses to fulfill orders from frontend callbacks.
- A new merchant integration on a fresh repo can reach a verified sandbox Snap success and a verified sandbox BI-SNAP QRIS success in under one hour of agent-driven work.
- The local release checker in `docs/official-release-readiness.md` passes on the exact commit being published.

## Risks and mitigations

- **Knowledge drift**: skill references stable patterns and integration lessons; the latest API surface is always at `docs.midtrans.com/llms.txt`. Quarterly review.
- **Generic docs answers**: blocking project-inspection precondition in `SKILL.md` and the project-adaptation reference.
- **Secret leakage in chat**: `sandbox-interaction-helper.md` enforces `$VAR` placeholders and refuses production-key payment creation.
- **Hallucinated API fields**: every reference cites the source docs page; the skill instructs agents to refresh against current docs at each engagement.

## Open questions

- Final ownership and review cadence between Midtrans Product, Engineering, and Developer Experience.
- Public GitHub repository name and visibility timeline.
- MCP server PRD authoring schedule (this PRD scopes skills only).

## References

- Midtrans LLM docs index: https://docs.midtrans.com/llms.txt
- Stripe AI Docs (design reference): https://docs.stripe.com/building-with-ai
- Stripe hosted skill catalog example: https://docs.stripe.com/.well-known/skills/index.json
- Stripe MCP docs: https://docs.stripe.com/mcp
- Stripe sandbox docs: https://docs.stripe.com/sandboxes
