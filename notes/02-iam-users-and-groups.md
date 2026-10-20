# 02 — IAM users and groups

## IAM user
A named identity INSIDE the account, created by root, with least-privilege
permissions. The "keycard" vs root's "master key." Two credential types:
- **password (+MFA)** → Console (human, web UI)
- **access key** (ID + secret) → CLI / SDK / API (programmatic)

## Groups
Permissions attach two ways: directly to a user, or to a **group** the user
joins and inherits from.
- A group is a **labeled bucket of permissions** — NOT an identity. You cannot
  log in as a group; it has no credentials.
- Attach the policy to the group ONCE; drop N users in; change the group →
  all N update. Remove someone → pull from group.

Best practice even for one user: **attach to groups, not users** — "one user"
becomes "a team" later, and access stays auditable.

```
root ──creates──▶ IAM user (has credentials)
                     └─ member of ─▶ IAM group (holds policy, no credentials)
```

## Interview line
"I attach policies to groups, not users, so access scales and stays auditable,
and I follow least privilege."
