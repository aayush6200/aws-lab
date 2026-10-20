# 04 — Credentials: access keys vs console, and why keys are scarier

## Two ways to authenticate
- **Console password (+MFA)** — lives in your head; MFA adds a second factor.
- **Access key** (AKIA… ID + secret) — lives in a FILE; used by CLI/SDK; by
  default NO second factor. Whoever holds the two strings IS you, from anywhere.

## Why an access key is more dangerous than a password
A file can be copied, synced, logged, pasted, and — the big one — **committed
to git and pushed public**. Bots scrape GitHub for `AKIA…` within seconds and
start mining. A password has MFA; a raw key is a single secret.

## Where a key must NEVER go
- not hardcoded in source
- not in any file inside a git repo
→ defense: `.gitignore` blocks `.env`, `.aws/`, `credentials`, `*accessKeys*`.
The CLI reads creds from `~/.aws/credentials` — OUTSIDE the repo. Code never
contains the key; the SDK picks it up from there.

## The better answer: don't have long-lived keys at all
Use **temporary, auto-expiring credentials** via roles / SSO (`aws sso login`).
A cred that rotates itself every few hours is far less scary to leak. This is
why the lab uses IAM Identity Center instead of IAM-user access keys. (See 06.)

## CloudShell
Browser terminal in the Console. Derives TEMPORARY creds from your login
session — no access key to create or store. The one keyless way to run code
during bootstrap, before SSO exists.
