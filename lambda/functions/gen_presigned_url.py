import boto3
import json, os, uuid

s3_client = boto3.client("s3")
BUCKET = os.environ["BUCKET_NAME"]

def get_presigned_url_handler(event, context):
    body = json.loads(event.get("body") or "{}")
    filename = body.get("filename", "receipt")
    receipt_id = str(uuid.uuid4())
    key = f"incoming/{receipt_id}/{filename}"
    url = s3_client.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET, "Key": key},
        ExpiresIn=300,
    )
    return {
        "statusCode": 200,
        "body": json.dumps({"receipt_id": receipt_id, "upload_url": url}),
    }


