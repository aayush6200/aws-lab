import boto3
import os
def get_client(service, profile=None):
    profile = profile or os.environ.get("AWS_PROFILE", "aayush_dev")
    session = boto3.Session(profile_name=profile)
    return session.client(service)