import json

from common.factory import get_client

with open("sso/config.local.json") as f:
    cfg = json.load(f)

client = get_client("identitystore", profile="aayush_admin")

resp = client.list_users(IdentityStoreId=cfg["identity_store_id"])

for user in resp["Users"]:
    print(user["UserName"], user["UserId"])