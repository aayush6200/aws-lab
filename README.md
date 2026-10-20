# aws-lab

Hands-on AWS, built the create → break → learn way. Separate from
`~/dev/network-mastery` (the containerlab/BGP work) on purpose.

Goal: build an **event-driven serverless app** that mirrors Southwest's stack,
so every line of their job description becomes "I built this." Interview 2026-10-20.

---

## Target architecture (the "Crew Event Processor")

```
          REST                     event bus                      store
Client → API Gateway → Lambda → EventBridge / Kinesis → Lambda consumer → DynamoDB
                         │                                                   │
                      (produce)                                          (query API)
                         └── S3 for artifacts/dead-letter ──┘
         CI/CD: GitHub Actions   ·   IaC: CloudFormation/CDK (= the real kill switch)
```

Maps to the JD keywords: S3, Lambda, DynamoDB, EventBridge, Kinesis, REST APIs,
microservices, Git, CI/CD, event streaming (their Kafka analog).

---

## COST SAFETY — read before creating anything

Three layers of shutdown:

1. **IaC stack delete** (normal) — everything lives in ONE stack → one
   `delete` command tears it all down atomically.
2. **Tag-sweep script** (failover) — every resource tagged `project=crew-lab`;
   a teardown script finds everything with that tag and force-deletes it, even
   if the stack delete half-fails. (TODO: `scripts/teardown.py`)
3. **Budget alarm** (backstop) — AWS Budgets alert set BEFORE building anything.
   (TODO: set up day 1, a few dollars threshold, email alert.)

### What costs money while IDLE (the kill-switch targets)
```
Kinesis            per-shard-hour — bills even with zero traffic
ECS / Fargate      per running task
NAT Gateway        per hour + per GB  (avoid entirely in a lab)
provisioned DynamoDB / RDS / EC2   per hour
Elastic IP (unattached)            per hour
```
### What is ~$0 when idle (safe to leave, pay-per-request)
```
Lambda             per invocation + duration
DynamoDB on-demand per request
API Gateway        per request
EventBridge        per event
S3                 per GB stored (tiny) + per request
```
Rule: prefer the pay-per-use variant. Treat anything in the first list as
"arm, use, tear down the SAME DAY."

### Safety checklist (day 1, before any service)
- [ ] Budget alarm created (email on threshold)
- [ ] NOT using the root user — a named IAM user / role with scoped perms
- [ ] root user has MFA and is locked away
- [ ] every resource gets the `project=crew-lab` tag
- [ ] `aws configure` points at the lab account, correct region

---

## Curriculum (identity first, then services)

```
1. Account + root user        container + god-key (lock it away)
2. IAM users                  named humans instead of root
3. IAM policies               how "who can do what" is written  ← heart of IAM
4. IAM roles                  assumed identity, no stored creds ← services↔services
5. Organizations              many accounts (light touch)
6. SSO / Identity Center      one human login across accounts (light touch)
   → then SERVICES, each connected back via roles
```

---

## Layout

```
scripts/   automation + the teardown/kill-switch scripts (I write these)
iac/       CloudFormation / CDK stack (the single-point shutdown)
services/  Lambda handlers, API code
notes/     what I learned, per concept
```

## Daily log
- 2026-10-14 — project created; cost-safety design locked; starting identity fundamentals.
- 2026-10-15 — identity fundamentals covered (root user, IAM users/groups, least
  privilege/blast radius, credentials, Organizations, Identity Center). Bootstrapped
  programmatically: Organizations enabled + `lab-sandbox` account created
  (`accounts/bootstrap_org.py`); IAM Identity Center enabled (Single-Region).
  Notes written per concept in `notes/01..06`. Handles in `sso/config.local.json`.

## BOOTSTRAP COMPLETE (2026-10-15)
Keyless SSO access to the sandbox is working. Verified:
`arn:aws:sts::685108782540:assumed-role/AWSReservedSSO_AdminAccess_…/aayush_admin`
— a temporary assumed role, no root, no IAM user, no long-lived key.

**To resume work (every session):**
```
aws sso login --profile aayush_admin          # refresh temp creds (re-run on ExpiredToken)
aws sts get-caller-identity --profile aayush_admin   # confirm sandbox 685108782540
```
All lab commands run with `--profile aayush_admin`. Provisioning that creates
IAM roles (Lambda exec roles etc.) needs this Admin profile; PowerUser/DevAccess
can't create IAM roles.

Profiles: `aayush_admin` (AdminAccess, build/provision) · a dev profile can be
added for DevAccess (run-only). SSO start URL: see `sso_start_url` in
`sso/config.local.json` (not committed).

## Next (planned 5–6 hr session, two terminals)
- **This terminal (AWS):** ~1 hr SSO fundamentals in depth, then WRITE programs
  (user writes the functions, Claude guides):
  - `sso/permission-sets/apply/` — create an `AdministratorAccess` permission set
  - `sso/identity-store/` — create your Identity Center user
  - `sso/assignments/` — assign you → permission set → sandbox (685108782540)
  - then `aws configure sso` + `aws sso login` → keyless temp creds on the Mac
  - verify: `aws sts get-caller-identity` shows an assumed-role, not root
- **Other terminal (BGP):** resume `network-mastery` — continue scaling the
  ibgp-01 lab (route reflectors / iBGP work).
