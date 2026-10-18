---
doc_id: CREDENTIAL-BROKER-AGENTS
title: Credential broker repository instructions
doc_type: repository-instructions
status: draft
version: 0.1.0
created: 2026-10-18
updated: 2026-10-18
owner: Transpara
steward: Codex
project: credential-broker
supersedes: []
canonical: false
---

# Repository instructions

Keep the public source small and free of credentials and private infrastructure
identifiers. Each dispatcher input selects reviewed code; never execute an
input as a command, URL, repository name, or script path. The protected GitHub
environment owns configuration and secrets, not this repository or an agent
host. Document each operation's trust boundary, failure behavior, and cost.

Use a task worktree and a pull request; never push directly to `main`. Use
imperative commit subjects with a lowercase type prefix and end Codex-authored
commits with `Co-Authored-By: Codex <noreply@openai.com>`. Run `make verify`
before handoff. Check unresolved review conversations with GraphQL and require
the exact-head TLC gate before merge. A Human must separately authorize each
live change to access, secrets, environment protection, or consequential
runtime behavior immediately before it runs. Never print or commit a secret.

## Revision History

| Version | Date | Change |
| --- | --- | --- |
| 0.1.0 | 2026-10-18 | Draft source, review, and live-effect boundaries. |
