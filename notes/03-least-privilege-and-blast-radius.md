# 03 — Least privilege & blast radius

## Principle of least privilege
Grant the MINIMUM permission a task needs, nothing more. Start from deny-all,
add only what's required.

## Blast radius
When a credential leaks, the damage is bounded by what that credential could
touch. A key that can only read one S3 bucket, leaked, costs you one bucket —
not your wallet, not your account. You contain the damage BEFORE it happens by
never carrying more permission than needed.

## Two different controls (don't conflate)
- **IAM** bounds *capability* — what actions/resources an identity may touch.
- **Budgets** bounds *cost* — a hard dollar alarm. There is NO "wallet limit"
  field on an IAM user; cost caps come from AWS Budgets.

That's why the lab's safety design has BOTH: IAM for capability, Budgets for
spend.

## Account as the hardest boundary
The strongest isolation AWS has isn't IAM or tags — it's a separate **account**.
Lab work in a dedicated sandbox account = a fat-finger or leak is trapped there.
(See 05 — Organizations.)
