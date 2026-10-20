import json

from common.factory import get_client

with open("sso/config.local.json") as f:
    cfg = json.load(f)

client = get_client("sso-admin", profile="aayush_admin")

resp = client.list_permission_sets(InstanceArn=cfg["instance_arn"])

for ps_arn in resp["PermissionSets"]:
    detail = client.describe_permission_set(
        InstanceArn=cfg["instance_arn"],
        PermissionSetArn=ps_arn,
    )
    print(detail["PermissionSet"]["Name"], ps_arn)
