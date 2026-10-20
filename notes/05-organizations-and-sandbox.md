# 05 — Organizations & the sandbox account

## AWS Organizations
Free service that groups many AWS accounts under one **management account**
(consolidated billing + central control). `create_organization(FeatureSet="ALL")`
converts your existing account INTO the management account — a sticky commit
(leaving an org has a process).

## Why a separate sandbox account (not just a folder)
A whole ACCOUNT is the hardest isolation boundary AWS has — harder than IAM or
tags:
1. **Blast radius** — fat-finger / leak / runaway bill is trapped in the sandbox.
2. **Cost isolation** — you see exactly what the lab costs; cap it per-account.
3. **Clean teardown** — worst case, close the account; everything in it is gone.

Cost: **$0** — Organizations is free, creating member accounts is free. You pay
only for what you RUN inside them. Billing consolidates to the management
account (no new credit card for the sandbox).

## The clean pattern
```
management account  = control plane (Organizations + Identity Center), NO workloads
sandbox member acct = where the lab actually runs
```

## Creating accounts programmatically (fully scriptable)
```
organizations.create_account(Email=<unique>, AccountName=…)   # async
organizations.describe_create_account_status(...)             # poll to SUCCEEDED
```
- Every account needs a **unique email** → Gmail `+` trick
  (`name+sandbox@gmail.com` lands in the same inbox, AWS sees it as unique).
- A new member account auto-gets an **`OrganizationAccountAccessRole`** that the
  management account can ASSUME (STS) — the keyless path to script INTO the
  sandbox without ever root-logging into it.

## This lab's accounts
- management: 249093698600
- sandbox `lab-sandbox`: 685108782540
- org id: o-rynk9am0dw
