---
title: Build on Midtrans with AI
excerpt: Use AI coding agents to integrate Midtrans — official agent skill, plain-text docs, and llms.txt.
---

> Ready-to-publish source for the docs.midtrans.com "Build on Midtrans with
> AI" page. Create it in the Documentation section under "Technical Reference
> & Developer Tools", as a sibling of "Library & Plugins" and "Postman
> Collection", with slug `building-with-ai` (ReadMe keeps the URL stable if
> the page is later promoted in the nav). Set the page title and excerpt from
> the frontmatter above, then paste only the body below this note. ReadMe
> adds the published page to https://docs.midtrans.com/llms.txt
> automatically, so coding agents reading Midtrans docs discover it on their
> own. After publishing, run ./tools/docs_drift_watch.py --update and commit
> the refreshed snapshot, since llms.txt gains a new entry. Remove this note
> before publishing.

Use AI coding agents and LLMs to integrate Midtrans payments. Midtrans ships two AI surfaces today: an official **agent skill** that teaches coding agents how to integrate safely, and **plain-text documentation** built for LLM consumption. Both need no credentials and call no Midtrans APIs by themselves.

## Install the agent skill

The skill covers product selection (Snap, Core API, BI-SNAP, Payment Link), merchant readiness preflight, payment state modeling, webhook signature verification, idempotent fulfillment, and sandbox-first verification.

With the [skills CLI](https://github.com/vercel-labs/skills) (works with Claude Code, Codex, Cursor, and other supported agents):

```bash
npx skills add https://github.com/veritrans/midtrans-agent-skills --yes
```

Or copy the folder manually from the [veritrans/midtrans-agent-skills](https://github.com/veritrans/midtrans-agent-skills) repository:

| Agent | Project location |
| --- | --- |
| Claude Code | `.claude/skills/integrate-midtrans-payments/` |
| OpenAI Codex and compatible agents | `.codex/skills/` or `.agents/skills/` |
| GitHub Copilot / VS Code | `.github/skills/` |
| OpenCode | `.opencode/skills/` |
| Cursor and tools without native skills | copy the folder, then point a rule in `.cursor/rules/` or `AGENTS.md` at `integrate-midtrans-payments/SKILL.md` |

Then ask your agent, for example:

```text
Use integrate-midtrans-payments to add Midtrans Snap checkout to this app.
```

What the skill enforces:

- Inspects your project and confirms merchant readiness (account, sandbox keys, active payment methods, callback URLs) before writing code.
- Routes each payment method to the right Midtrans product instead of mixing Snap, Core API, and BI-SNAP request shapes.
- Keeps server keys and signing on the backend, verifies webhook signatures, and fulfills orders only from trusted signals.
- Verifies in sandbox with deterministic signature checks and webhook replay before any go-live step.

Manually copied skills do not auto-update — refresh the folder before major payment work.

## Plain text docs

Every page on this documentation site has a Markdown variant: append `.md` to the URL, for example [https://docs.midtrans.com/docs/snap-snap-integration-guide.md](https://docs.midtrans.com/docs/snap-snap-integration-guide.md). Markdown pages cost fewer tokens than HTML and keep the document structure intact.

The complete page index lives at [https://docs.midtrans.com/llms.txt](https://docs.midtrans.com/llms.txt), following the [llmstxt.org](https://llmstxt.org) convention. Point your agent there first; the agent skill treats it as the source of truth and re-reads it on every engagement.

## What's next

A Midtrans MCP server for authenticated sandbox interaction is a separate, later phase; the agent skill stays the lightweight no-credentials option.

Found a misroute or a gap in the skill? File an issue at [github.com/veritrans/midtrans-agent-skills](https://github.com/veritrans/midtrans-agent-skills/issues).
