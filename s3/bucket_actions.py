from common.factory import get_client

client = get_client("s3")


def create_bucket(bucket_name: str) -> dict:
    return client.create_bucket(Bucket=bucket_name)


def list_buckets() -> list[dict]:
    return client.list_buckets()["Buckets"]


def delete_bucket(bucket_name: str) -> dict:
    return client.delete_bucket(Bucket=bucket_name)


def put_object(bucket_name: str, key: str, body: bytes) -> dict:
    return client.put_object(Bucket=bucket_name, Key=key, Body=body)


def get_object(bucket_name: str, key: str) -> bytes:
    response = client.get_object(Bucket=bucket_name, Key=key)
    return response["Body"].read()


def upload_file_to_s3(bucket_name: str, key: str, file_name: str) -> None:
    client.upload_file(file_name, bucket_name, key)


def list_objects(bucket_name: str) -> dict:
    return client.list_objects(Bucket=bucket_name)


def delete_object(bucket_name: str, key: str) -> dict:
    return client.delete_object(Bucket=bucket_name, Key=key)


def gen_pre_signed_url(bucket_name: str, key: str, client_method: str = "get_object", expires_in: int = 3600):
    return client.generate_presigned_url(ClientMethod=client_method, Bucket=bucket_name, Key=key, ExpiresIn=expires_in)