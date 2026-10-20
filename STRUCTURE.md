# Repo structure — organized by SERVICE

Each AWS service/feature is a self-contained top-level folder with whatever
subfolders it needs, **including its own `policies/`**. You work one service at
a time; everything that service touches lives together.

```
aws-lab/
├── accounts/          AWS Organizations / member-account creation
│   └── policies/      (SCP / account-level policies, later)
├── users/             IAM users + groups (identity)
│   └── policies/      human/daily-driver permission policies
├── lambda/
│   ├── functions/     handler code
│   └── policies/      execution-role policies (service-local)
├── eventbridge/
│   ├── rules/         event rules / patterns
│   └── policies/
├── apigateway/
│   └── policies/
├── dynamodb/
│   └── policies/
├── s3/
│   └── policies/
│
├── scripts/           CROSS-CUTTING — kill-switch/teardown, tagging helpers.
│                      NOT per-service: the teardown must sweep EVERY service,
│                      so it can't live inside one service folder.
├── iac/               CloudFormation/CDK (the single-command shutdown, later)
└── notes/             what I learned, per concept
```

## Conventions
- **Policies live with their service.** A policy is DATA (JSON); the boto3 that
  attaches it is LOGIC. Keep the JSON in `<service>/policies/<named>.json`,
  named clearly (e.g. `lambda/policies/crew-exec-role.json`).
- **Identity policies** (what a human user may do) live in `users/policies/`.
- **Attach to GROUPS, not users.** Least privilege — grant only what's needed.
- **Tag everything** `project=crew-lab` so the kill-switch can find + delete it.
- **Never** commit access keys — `.gitignore` blocks them; CLI reads creds from
  `~/.aws/credentials`, outside the repo.
- **Cross-cutting stays global.** Teardown/tagging/shared helpers → `scripts/`,
  never inside a service folder.

## Tooling
Python + boto3 (learn the API by hand) → graduates to CloudFormation/CDK, which
becomes the real single-point shutdown.
