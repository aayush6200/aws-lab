# Provisioned accounts

| Role | Name | Account ID | Root email |
|---|---|---|---|
| Management | (your existing account) | — | see `sso/config.local.json` |
| Sandbox | `lab-sandbox` | `685108782540` | see `sso/config.local.json` |

Created 2026-10-15 via `accounts/bootstrap_org.py` (Organizations `create_account`).

The sandbox has an auto-created role `OrganizationAccountAccessRole` that the
management account can assume (STS) — the keyless path to script into it.
