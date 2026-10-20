# sso/  — IAM Identity Center (formerly AWS SSO)

The modern, more-secure alternative to long-lived IAM users. Identity Center
issues **temporary, auto-expiring credentials** via `aws sso login` — no access
key sitting in a file. A leaked SSO session expires on its own; a leaked IAM
access key lives until you revoke it.

## The three objects (this replaces "IAM user + attached policy")

```
identity-store/     USERS and GROUPS — who exists (native, or synced from an IdP)
permission-sets/    named bundles of policies — WHAT someone can do
                    (a permission set becomes an IAM ROLE in the account at login)
assignments/        the binding:  (user|group) × (permission set) × (account)
```

Mapping from the IAM-user world:
```
IAM user + policy      →   Identity Center user  +  permission set  +  assignment
long-lived access key  →   temporary creds from `aws sso login`
```

## Folder layout (same data/logic convention as the rest of the repo)
```
sso/
├── identity-store/        boto3 to create users/groups in the identity store
├── permission-sets/
│   ├── documents/         inline policy JSON per permission set (DATA)
│   └── apply/             boto3: create permission sets, attach managed/inline (LOGIC)
└── assignments/           boto3: assign a group → permission set → account
```

## IMPORTANT — one-time Console enable first
Identity Center can't be fully bootstrapped from zero over the CLI. You must,
once, in the Console:
1. IAM Identity Center → **Enable** (pick a region; in a standalone account it
   creates a default identity source).
2. Create a user (and group) in the identity store, OR plan to manage via boto3
   after.
3. Create a permission set (e.g. `AdministratorAccess`) and **assign** it to
   your account for that user/group.

Then the CLI uses SSO instead of a static key:
```
aws configure sso          # set up the SSO profile (start URL + region)
aws sso login --profile <name>
aws sts get-caller-identity --profile <name>   # ARN shows an assumed-role, not a user
```
boto3 then uses that profile — `boto3.Session(profile_name="<name>")` — with
temporary creds it refreshes automatically.

## Note
The IAM `users/` folder (long-lived IAM users) is now OPTIONAL for this
approach — kept only if we ever need a service/break-glass user. Identity-store
users/groups live here under `sso/`, not there.

## APIs you'll call (boto3 clients)
```
sso-admin        create_permission_set, put_inline_policy_to_permission_set,
                 attach_managed_policy_to_permission_set, create_account_assignment
identitystore    create_user, create_group, create_group_membership
```
