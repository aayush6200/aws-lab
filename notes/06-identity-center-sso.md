# 06 — IAM Identity Center (SSO)

The modern, more-secure alternative to long-lived IAM users. Issues
**temporary, auto-expiring credentials** via `aws sso login` — nothing stored,
nothing to rotate, nothing to leak-and-forget.

## The three objects (replaces "IAM user + attached policy")
```
identity store users/groups   WHO exists
permission set                WHAT they can do (a bundle of policies)
account assignment            the binding: WHO × WHAT × WHERE(account)
```
A **permission set** becomes a hidden IAM **role** in each assigned account
(`AWSReservedSSO_<permset>_<hash>`). At login you ASSUME that role with temp
creds — you never hold a permanent identity inside the account.

```
assignment = WHO (user/group) × WHAT (permission set) × WHERE (account)
remove any corner → access gone
```

## Why it beats IAM users (3 chores that vanish)
- no key to store/leak (temp creds)
- no key to rotate (they expire on their own)
- no identity to hunt down at offboarding (disable one identity-store user /
  pull one assignment → access everywhere dies at next expiry)

## What "Enable" provisioned in the background
1. a managed **user directory** (the `d-…` Identity Center directory)
2. an **identity provider / token issuer** (the Issuer URL) — what you auth
   against on `aws sso login`
3. **org-scoping** (tied to the org id) so it can reach every member account
4. the **role-minting + STS broker** — logs you in, then mints short-lived role
   creds in the right account

## The one Console click
Enabling the org instance is NOT scriptable — `sso-admin create_instance` is
rejected in the management account. Click Enable once (chose **Single-Region**
to avoid the ~$1/mo customer-managed KMS key that Multi-Region requires;
Identity Center itself is free). AFTER enabling, everything is boto3.

## The two handles every SSO call needs
```
InstanceArn        → sso-admin APIs (permission sets, assignments)
IdentityStoreId    → identitystore APIs (users, groups)
```
Get both: `aws sso-admin list-instances`. This lab's values live in
`sso/config.local.json` (gitignored).

## APIs to write (tomorrow)
```
sso-admin:    create_permission_set, attach_managed_policy_to_permission_set,
              create_account_assignment
identitystore: create_user, create_group, create_group_membership
```
Then: `aws configure sso` → `aws sso login` → keyless temp creds on the Mac.
