---
doc_id: CREDENTIAL-BROKER-README
title: Transpara credential broker
doc_type: repository-guide
status: draft
version: 0.1.1
created: 2026-10-18
updated: 2026-10-18
owner: Transpara
steward: Codex
project: credential-broker
supersedes: []
canonical: false
---

# Transpara credential broker

This public repository holds reviewed GitHub Actions operations that use
credentials without returning them to agent sessions. It is not a general
secret vault or remote shell. The initial operation checks whether a Harbor
robot can request repository pull and push authorization; it does not push an
image or deploy anything.

The source is **not operational yet**. Do not populate its environment secrets
until `main` has TLC protection, the `credential-broker` environment restricts
deployments to protected `main`, requires an off-agent Human reviewer, and
prevents self-review. Agent-accessible GitHub identities must be unable to
administer those controls, bypass `main`, or approve deployments. The
[design and activation checklist](docs/design.md) record the required readbacks.

Run `make verify` for the local tests. CI runs the same target for pull requests
and changes to `main`; CI does not exercise a real credential. Each new operation
requires fixed, reviewed code and a separate secret-access decision. Never put
secret values, registry tokens, or signed approval material in this repository,
an issue, a pull request, or chat.

## Revision History

| Version | Date | Change |
| --- | --- | --- |
| 0.1.1 | 2026-10-18 | Require off-agent approval and prevent self-review before activation. |
| 0.1.0 | 2026-10-18 | Draft the public broker scaffold and its activation contract. |
