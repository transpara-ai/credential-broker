---
doc_id: CREDENTIAL-BROKER-DESIGN
title: Public GitHub Actions credential broker design
doc_type: design
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

# Public GitHub Actions credential broker design

## Factory Order and route

**Outcome:** Agent sessions request fixed, reviewed GitHub Actions operations
without receiving third-party credentials. A protected environment supplies
configuration and credentials outside the agent host. The initial adapter asks
Harbor for repository pull/push authorization and prints only success or failure.

**Critical route:** This introduces a credential and authorization boundary
(TLC triggers 1, 5, and 6). A credential stored on an agent host is not an
independent vault. This repository is public because the selected GitHub plan
supports Human-required environment reviewers only for public repositories.

**Scope:** Public source, fixed dispatch, tests, and a rollout contract. No
credential value, registry endpoint, or repository name belongs in source or
workflow input. This change does not create a GitHub environment, populate a
secret, revoke an identity, dispatch a live run, or deploy anything. New
operations require separate reviewed adapters; arbitrary commands and raw
secret retrieval are not operations.

## Trust boundary

| Risk | Control and residual limit |
| --- | --- |
| Agent changes code or protection | Enroll this repository in the no-bypass TLC `main` ruleset before merging source. Confirm every agent-accessible identity lacks repository/environment administration and cannot bypass the ruleset. Replace or revoke any agent-accessible administrative credential before adding a secret. |
| Public PR runs with credentials | Verification runs without the protected environment or secrets. The credentialed workflow has only `workflow_dispatch`; its job checks `main`, and the environment admits only protected `main` after Human approval. |
| Agent dispatches a different branch or repeats a run | A protected-branch environment policy rejects other refs. The required reviewer must be an off-agent Human, with no agent-accessible user or team member able to approve. Prevent self-review and read back both controls before adding secrets. GitHub records dispatch and deployment activity. The in-workflow branch guard is defense in depth. |
| Input becomes an exfiltration destination | Dispatch chooses only an allowlisted operation. Its endpoint and repository are protected environment secrets, not dispatch inputs. The script requires an HTTPS token endpoint, refuses redirects, and never emits a response body. |
| Public source reveals private infrastructure | The code and docs contain no real registry host or repository path. Environment secrets hold those values until a Human explicitly approves a different disclosure. Public visibility still exposes operation names and implementation; review them before merge. |
| Existing credentials bypass the broker | Do not call this an all-work boundary until direct credentials are inventoried and removed or explicitly excepted. |

The adapter examines claims in Harbor's TLS response but does not independently
verify the JWT signature or push an image. It makes one outbound request with
a 20-second timeout and a 64-KiB response cap. A run uses a GitHub-hosted runner
for at most five minutes; measure actual runner time and cost on the first
approved run before making a capacity claim.

## Activation sequence

1. Merge only after local tests, CI, exact-head TLC cross-family review (or a
   valid Human-signed exception), zero unresolved conversations, and Human
   acceptance. Confirm the no-bypass TLC ruleset covers this repository.
2. Replace and revoke any agent-accessible administrative GitHub credential.
   Inventory connected apps, user tokens, and team memberships. Verify every
   agent-accessible identity cannot administer the environment, bypass protected
   `main`, or approve a protected deployment. A dispatcher needs Actions write,
   not repository administration, secret management, or deployment approval.
3. Create the `credential-broker` environment, restrict deployment to protected
   `main`, require a named Human reviewer whose login and team memberships are
   inaccessible to agents, and enable `prevent_self_review`. Read back all
   three policies and verify the effective reviewer list against the identity
   inventory from step 2. A Human must approve each live dispatch on an
   independent device or session. The organization is on GitHub Team, where
   reviewer protection is available for public repositories, not private ones.
4. Add `HARBOR_TOKEN_URL`, `HARBOR_REPOSITORY`, `HARBOR_USERNAME`, and
   `HARBOR_PASSWORD` as **environment secrets only** from an approved source.
   Read back their names, never their values. Do not seed secrets if any prior
   protection check fails.
5. Dispatch the fixed Harbor operation on `main`. Inspect the result and logs
   without printing credentials. Confirm a non-main dispatch cannot receive
   environment secrets. Retire the host-local credential only after checking
   for other approved consumers.

Each live access, secret, protection, or runtime effect needs separate Human
authority immediately before execution. Source approval does not grant rollout.

## Verification and recovery

`make verify` uses fabricated credentials and no network; CI repeats it. It
checks fixed dispatch and credential handling but cannot prove live environment
policy. A failed rollout leaves the existing deployment consumer untouched.
Disable the broker environment or revoke its dispatch identity if a live run
fails. If a credential may have leaked, revoke and rotate it. Keep the current
host-local source until a verified replacement and consumer inventory exist.

## Revision History

| Version | Date | Change |
| --- | --- | --- |
| 0.1.1 | 2026-10-18 | Require off-agent reviewers, identity readback, and self-review prevention. |
| 0.1.0 | 2026-10-18 | Draft the public broker boundary, code, and guarded rollout. |
