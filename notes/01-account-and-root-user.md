# 01 — AWS account vs root user

## The precise terms (AWS docs avoid "root account")
- **AWS account** = the CONTAINER — a 12-digit ID, a billing relationship,
  holds all resources. The "building."
- **AWS account root user** (or **root user**) = the single all-powerful
  IDENTITY created with the account, signs in with the account EMAIL. The
  "person holding the master key."
- "Root account" is loose/colloquial — not an official object. The clean pair
  is *account* (container) vs *root user* (identity inside it).

One account has exactly ONE root user. Can't delete it, can't make more.

## Why you lock root away and never use it
If the root user leaks, two disasters:
- **Money:** attacker spins up expensive resources (GPU fleets, mining) → AWS
  bills YOU. Five/six-figure bills from one leaked key have happened.
- **Control:** root can change the account email + password and remove MFA →
  you're locked out of your own account, recovery email goes to the attacker.
  Root is the one identity that can lock out everyone, including you.

## The rule
Use root EXACTLY ONCE — to create a limited daily-driver identity — then:
- strong password + **MFA** on root
- NO root access keys (ever)
- never log in with it again for daily work

Everything else is built as the weaker identity, so a leaked *daily* credential
is contained, not account-ending.
