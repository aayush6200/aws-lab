#!/usr/bin/env python3
"""
Bootstrap step 1 — Organizations + sandbox account.

Turns THIS account into an Organizations management account and creates the
crew-lab sandbox member account under it.

WHERE TO RUN: AWS CloudShell (keyless), logged into the Console as the
management account. boto3 is pre-installed there; CloudShell injects temporary
credentials from your console session, so no access key is needed.

Idempotent: safe to re-run. It won't create a second organization or a
duplicate sandbox.
"""
import json
import os
import sys
import time
from pathlib import Path

import boto3

SANDBOX_NAME = "lab-sandbox"

# Root email is NOT committed to the repo (phishing surface). Provide it via
# the SANDBOX_EMAIL env var (CloudShell) or sso/config.local.json (local).
_cfg = Path(__file__).resolve().parent.parent / "sso" / "config.local.json"
SANDBOX_EMAIL = os.environ.get("SANDBOX_EMAIL") or (
    json.loads(_cfg.read_text()).get("sandbox_root_email") if _cfg.exists() else None
)
if not SANDBOX_EMAIL:
    sys.exit("set SANDBOX_EMAIL env var or sandbox_root_email in sso/config.local.json")

org = boto3.client("organizations")

# 1. Ensure this account is an Organizations management account (FeatureSet ALL
#    = SCPs + full member-account management, not just consolidated billing).
try:
    org.create_organization(FeatureSet="ALL")
    print("created organization — this account is now the MANAGEMENT account")
except org.exceptions.AlreadyInOrganizationException:
    print("already in an organization — continuing")

# 2. Guard against duplicates: if the sandbox already exists, stop here.
existing = None
for page in org.get_paginator("list_accounts").paginate():
    for acct in page["Accounts"]:
        if acct["Email"] == SANDBOX_EMAIL or acct["Name"] == SANDBOX_NAME:
            existing = acct
            break
    if existing:
        break

if existing:
    print(f"sandbox already exists: {existing['Name']} "
          f"({existing['Id']}) [{existing['Status']}]")
    print("SANDBOX_ACCOUNT_ID =", existing["Id"])
    sys.exit(0)

# 3. Create the sandbox member account (asynchronous — returns a request id).
resp = org.create_account(Email=SANDBOX_EMAIL, AccountName=SANDBOX_NAME)
req_id = resp["CreateAccountStatus"]["Id"]
print("create_account requested:", req_id)

# 4. Poll until the async creation finishes.
while True:
    s = org.describe_create_account_status(
        CreateAccountRequestId=req_id)["CreateAccountStatus"]
    print("  state:", s["State"])
    if s["State"] in ("SUCCEEDED", "FAILED"):
        break
    time.sleep(5)

if s["State"] == "SUCCEEDED":
    print("sandbox created")
    print("SANDBOX_ACCOUNT_ID =", s["AccountId"])
    print("note: the sandbox has an 'OrganizationAccountAccessRole' this "
          "management account can assume — that's how you script INTO it "
          "without ever root-logging into the sandbox.")
else:
    print("FAILED:", s.get("FailureReason"))
    sys.exit(1)
