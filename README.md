# Midtrans Agent Skills

Official Midtrans Agent Skills for AI-assisted merchant payment integrations. Designed for Claude Code, OpenAI Codex, GitHub Copilot, Cursor, OpenCode, and any coding agent that loads Markdown skill files.

This is the **skill-first phase**. It does not ship an MCP server yet. Agents use these skills to inspect merchant codebases, choose the correct Midtrans product path, implement safely, and guide sandbox verification. Authenticated live API tools will follow in a separate MCP phase.

## Skills

- `integrate-midtrans-payments` — integrate, debug, review, or productionize Midtrans Snap, Core API, BI-SNAP, QRIS, virtual account, GoPay, GoPay tokenization, and GoPayLater flows.

The skill is an adaptive router plus product playbooks. Agents first classify the merchant's need, then load only the relevant reference: Snap Checkout, BI-SNAP Core, GoPay tokenization, operations/go-live, sandbox interaction, or evaluation prompts.

## Install today

### Skills CLI (recommended)

The skills CLI installs straight from this repository for Claude Code, Codex, Cursor, and other supported agents:

```bash
npx skills add https://github.com/veritrans/midtrans-agent-skills --yes
```

Manual copy works everywhere else:

### Claude Code

```bash
# Project-scoped
mkdir -p .claude/skills
cp -R integrate-midtrans-payments .claude/skills/

# Or user-scoped (available across all projects)
mkdir -p ~/.claude/skills
cp -R integrate-midtrans-payments ~/.claude/skills/
```

Claude Code auto-discovers any folder under `.claude/skills/` that contains a `SKILL.md` with valid frontmatter. The skill activates whenever the user's request matches the description (Midtrans, Snap, BI-SNAP, QRIS, VA, GoPay, GoPayLater, webhook, signature, payment, etc.).

Invoke explicitly with:

```
Use integrate-midtrans-payments to add Midtrans Snap to this app.
```

### OpenAI Codex / Codex-compatible agents

```bash
mkdir -p .codex/skills
cp -R integrate-midtrans-payments .codex/skills/
# or, for vendor-neutral sharing
mkdir -p .agents/skills
cp -R integrate-midtrans-payments .agents/skills/
```

### GitHub Copilot / VS Code

```bash
mkdir -p .github/skills
cp -R integrate-midtrans-payments .github/skills/
# or fall back to the Claude/agents convention
mkdir -p .claude/skills
cp -R integrate-midtrans-payments .claude/skills/
```

### Cursor and tools without native skill loading

Copy the folder, then add a short pointer to the tool's always-loaded instructions (for Cursor: `.cursor/rules/midtrans.md`, for an AGENTS.md repo: append a line):

```markdown
When asked to implement, debug, or review Midtrans payment integration,
read and follow `integrate-midtrans-payments/SKILL.md`.
```

### OpenCode

```bash
mkdir -p .opencode/skills
cp -R integrate-midtrans-payments .opencode/skills/
```

## Usage

The skill always begins with merchant readiness and project inspection. It will not generate Midtrans code without first establishing account/sandbox/method/flow assumptions and reading the merchant repo (env files, payment routes, order persistence, callbacks, tests, deployment). If no project is available, the skill stops and asks for the target stack rather than emitting generic docs.

Authoritative source of truth: [https://docs.midtrans.com/llms.txt](https://docs.midtrans.com/llms.txt). The skill refreshes against current Midtrans docs at every engagement; the local files capture stable patterns and integration lessons, not API surface details.

## Hosted distribution

`docs.midtrans.com` runs on ReadMe, which auto-generates `llms.txt` from published pages but cannot serve repository files such as `/.well-known/skills/index.json`. Distribution therefore splits:

- **Canonical skill source**: this GitHub repository (installable today via `npx skills add`).
- **Machine-readable catalog**: `https://raw.githubusercontent.com/veritrans/midtrans-agent-skills/main/.well-known/skills/index.json`.
- **Docs discovery**: publish the "Build on Midtrans with AI" page from [docs/readme-io/agent-skills-page.md](docs/readme-io/agent-skills-page.md) on docs.midtrans.com. Once published, ReadMe lists it in `llms.txt` automatically, so agents reading Midtrans docs find the skill organically.

Still planned but **not yet shipped**:

- Versioned `@midtrans/agent-skills` npm package for pinned installs.
- Midtrans MCP server for authenticated sandbox interaction. The MCP phase will be additive — skills stay as the lightweight, no-credentials option.

Manually copied skills do not auto-update. Refresh the folder before major payment work.

## Official release gate

Before publishing as an official Midtrans artifact, run the local checker and
complete the host pressure tests in [Official Release Readiness](docs/official-release-readiness.md).
Use `tools/build_pressure_pack.py` to generate exact Claude/Codex scenario
prompts and evidence templates from `integrate-midtrans-payments/evaluations.json`.
Use `tools/validate_pressure_evidence.py` to check completed host evidence
before claiming the pressure gate has passed.
A GitHub Actions workflow template is included under `docs/github-actions/`;
a repository maintainer with `workflow` scope should install it under
`.github/workflows/` before public release.
Use `tools/build_publication_bundle.py` to produce the exact hosted index and
skill files for the official docs/repository release.

Docs freshness is watched, not assumed: `docs/doc-sync/doc-dependencies.json`
maps each reference to the docs.midtrans.com pages it was written against, and
`tools/docs_drift_watch.py` compares those pages (plus the full `llms.txt`
page list) with the committed snapshot. Install
`docs/github-actions/docs-drift-watch.yml` as a scheduled workflow so doc
changes open an issue naming the references to review; after updating them,
run `./tools/docs_drift_watch.py --update` and commit the snapshot.

## Repository layout

```text
integrate-midtrans-payments/
  SKILL.md                          # entry point with routing and blocking precondition
  evaluations.json                  # structured QA scenarios (Anthropic schema)
  agents/
    openai.yaml                     # Codex/OpenAI interface hint
  references/
    merchant-decision-tree.md       # product routing
    merchant-readiness-preflight.md # merchant account, sandbox, flow, and proof preflight
    project-adaptation.md           # mandatory project inspection
    snap-checkout.md                # Snap playbook
    mobile-sdk.md                   # mobile WebView and deeplink playbook
    bisnap-core.md                  # BI-SNAP playbook
    gopay-tokenization.md           # GoPay tokenization + GoPayLater
    core-api-classic.md             # classic Core API playbook
    payment-links.md                # Payment Link playbook
    subscriptions.md                # Subscription API and recurring billing
    refund-operations.md            # refund playbook
    midtrans-runtime-patterns.md    # cross-product runtime patterns
    operations-and-go-live.md       # callbacks, secrets, logs, smoke
    sandbox-interaction-helper.md   # safe sandbox commands and fallbacks
    verification-playbook.md        # unit, contract, smoke checklist
    evaluation-prompts.md           # pressure scenarios for QA (prose form)
    agent-portability.md            # multi-agent host guidance
  scripts/
    README.md                       # safety model and inventory
    verify_snap_signature.sh        # Snap notification signature verifier
    replay_snap_webhook.sh          # signed Snap webhook replay
    sign_bisnap_transaction.py      # BI-SNAP HMAC transactional signature
    sign_bisnap_access_token.py     # BI-SNAP RSA access-token signature
    verify_bisnap_notification.py   # BI-SNAP RSA notification verify
    dry_run_bisnap_sign.py          # full BI-SNAP signing dry-run
    format_partner_service_id.sh    # 8-char left-padded VA partner id
    bisnap_timestamp.py             # Asia/Jakarta ISO-8601 timestamp
    print_midtrans_webhook_ips.sh   # webhook source IP allowlist helper
  assets/
    fixtures/                       # redacted webhook payload shapes
    templates/env.example           # Midtrans env starter template
.well-known/skills/index.json       # draft hosted catalog manifest
docs/official-release-readiness.md  # publication and evidence gate
docs/readme-io/agent-skills-page.md # ready-to-publish docs.midtrans.com page
docs/doc-sync/doc-dependencies.json # reference-to-docs-page dependency map
docs/doc-sync/doc-snapshot.json     # hashed docs snapshot for drift detection
docs/github-actions/official-readiness.yml # CI readiness workflow template
docs/github-actions/docs-drift-watch.yml   # scheduled docs drift workflow template
tools/check_official_readiness.py   # local release checker
tools/docs_drift_watch.py           # docs.midtrans.com drift watchdog
tools/build_pressure_pack.py        # Claude/Codex pressure-pack generator
tools/validate_pressure_evidence.py # completed evidence validator
tools/build_publication_bundle.py   # hosted publication bundle builder
```

## Contributing

File issues at the public Midtrans GitHub repository when the skill misroutes a merchant scenario or omits a real integration gotcha. Pull requests must keep `SKILL.md` concise and push product detail into `references/`.

## License

Licensed under the [BSD 3-Clause License](LICENSE).
