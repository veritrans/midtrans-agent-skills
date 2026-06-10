# Agent Portability

The portable artifact is the skill folder:

```text
integrate-midtrans-payments/
  SKILL.md
  evaluations.json
  agents/
    openai.yaml
  references/
    merchant-decision-tree.md
    merchant-readiness-preflight.md
    project-adaptation.md
    snap-checkout.md
    mobile-sdk.md
    bisnap-core.md
    gopay-tokenization.md
    core-api-classic.md
    payment-links.md
    subscriptions.md
    refund-operations.md
    midtrans-runtime-patterns.md
    operations-and-go-live.md
    sandbox-interaction-helper.md
    verification-playbook.md
    evaluation-prompts.md
    agent-portability.md
  scripts/
    README.md
    verify_snap_signature.sh
    replay_snap_webhook.sh
    sign_bisnap_transaction.py
    sign_bisnap_access_token.py
    verify_bisnap_notification.py
    dry_run_bisnap_sign.py
    format_partner_service_id.sh
    bisnap_timestamp.py
    print_midtrans_webhook_ips.sh
  assets/
    fixtures/
      snap-notification-settlement.json
      snap-notification-pending.json
      snap-notification-expire.json
      snap-notification-refund.json
      snap-notification-partial-refund.json
      bisnap-qris-notification.json
      bisnap-va-notification.json
      bisnap-debit-notification.json
      gopay-account-linking-notification.json
      payment-link-notification.json
      recurring-notification-card.json
    templates/
      env.example
```

Keep the skill standard-first: `name`, `description`, Markdown body, and relative references. Avoid host-specific frontmatter unless publishing to a host that requires it. `agents/openai.yaml` is an optional Codex/OpenAI interface hint — regenerate it with the skill-creator `generate_openai_yaml.py` script when fields change.

## Contents

- Native Skill Hosts
- Cursor And Tools Without Native SKILL.md Loading
- Packaging Guidance For Merchants
- Official Hosted Distribution
- Prompt Examples

## Native Skill Hosts

| Host | Project location | User/global location | Notes |
| --- | --- | --- | --- |
| Claude Code | `.claude/skills/<name>/SKILL.md` | `~/.claude/skills/<name>/SKILL.md` | Claude also supports direct slash invocation. |
| OpenAI Codex / compatible agents | `.codex/skills/<name>/SKILL.md`, `.agents/skills/<name>/SKILL.md`, or host-specific configured skills path | `~/.codex/skills/<name>/SKILL.md` or `~/.agents/skills/<name>/SKILL.md` | Prefer `.agents/skills` for vendor-neutral sharing when the host supports it. |
| GitHub Copilot / VS Code | `.github/skills/<name>/SKILL.md`, `.claude/skills/<name>/SKILL.md`, or `.agents/skills/<name>/SKILL.md` | `~/.copilot/skills/<name>/SKILL.md` or `~/.agents/skills/<name>/SKILL.md` | Skills are task-specific and loaded on demand. |
| OpenCode | `.opencode/skills/<name>/SKILL.md`, `.claude/skills/<name>/SKILL.md`, or `.agents/skills/<name>/SKILL.md` | `~/.config/opencode/skills/<name>/SKILL.md`, `~/.claude/skills/<name>/SKILL.md`, or `~/.agents/skills/<name>/SKILL.md` | Name must match directory and use lowercase hyphen form. |

## Cursor And Tools Without Native SKILL.md Loading

If the tool cannot load Agent Skills natively, keep the skill folder in the repo and add a small pointer in the tool's always-loaded instructions:

```markdown
When asked to implement, debug, or review Midtrans payment integration, read and follow `integrate-midtrans-payments/SKILL.md`.
```

For Cursor, prefer a project rule in `.cursor/rules/` or `AGENTS.md` that points to the skill. Keep the rule short so the detailed guidance stays in the skill.

Some hosts run skills without network access (skills uploaded to the Claude API code-execution environment; claude.ai depending on settings). On those hosts the per-engagement `https://docs.midtrans.com/llms.txt` refresh is impossible: rely on the bundled references, and state explicitly that live-docs freshness was not verified for this session.

## Packaging Guidance For Merchants

- Publish one generic Midtrans skill folder, not a separate skill per framework.
- Put framework-specific examples in references only when they are proven by real projects.
- Encourage agents to inspect each merchant codebase before choosing file locations or patterns.
- Keep public docs links live instead of copying large API docs into the skill.
- Version the skill with release notes outside the skill folder if needed; do not clutter the skill with changelog content.
- For high-risk scripts, avoid auto-run permissions. Payment integrations usually need judgment and merchant credentials, so references are safer than executable scripts.

## Official Hosted Distribution

The canonical skill source is the public GitHub repository, installable today:

```bash
npx skills add https://github.com/veritrans/midtrans-agent-skills --yes
```

`docs.midtrans.com` runs on ReadMe, which auto-generates `https://docs.midtrans.com/llms.txt` from published pages but cannot serve repository files such as `/.well-known/skills/index.json`. Distribution therefore splits:

- The machine-readable catalog is served from the repository: `https://raw.githubusercontent.com/veritrans/midtrans-agent-skills/main/.well-known/skills/index.json`.
- The docs site publishes a "Build on Midtrans with AI" page (source: `docs/readme-io/agent-skills-page.md` in the repository). Once published, ReadMe lists it in `llms.txt` automatically, so agents reading Midtrans docs discover the skill organically.

Publishing requirements:

- The docs page explains native install options for Claude Code, Codex-compatible agents, Cursor, Copilot, OpenCode, and manual users.
- The docs page states that manually copied skills do not auto-update.
- The hosted skill links to `https://docs.midtrans.com/llms.txt` and product docs instead of copying entire API references.
- Release notes and changelog live outside `SKILL.md`.

Keep MCP separate. Agent skills teach the coding agent how to behave. The later MCP server can expose authenticated or sandbox API tools with stronger permissioning.

## Prompt Examples

- "Use `integrate-midtrans-payments` to add Snap card checkout to this app."
- "Use `integrate-midtrans-payments` to debug why Midtrans webhooks do not update orders."
- "Use `integrate-midtrans-payments` to review our BI-SNAP GoPay tokenization implementation before launch."
- "Use `integrate-midtrans-payments` to create a merchant-specific Midtrans rollout checklist for our stack."
