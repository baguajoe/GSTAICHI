"""Cloudflare R2 (S3-compatible) helpers. Both buckets are private; nothing here makes anything public.

taichi-masters: original uploads from the Studio (the browser uploads straight to R2 with presigned URLs).
taichi-streams: encoded HLS files, thumbnails and article pictures (served only through the media Worker).
"""
import mimetypes
import os
import boto3
from botocore.config import Config

MAX_UPLOAD_BYTES = 10 * 1024 ** 3  # 10 GB
PART_SIZE = 16 * 1024 ** 2  # 16 MB parts: a 10 GB file is 640 parts (S3 allows 10,000)
PRESIGN_SECONDS = 6 * 60 * 60

CONTENT_TYPES = {".m3u8": "application/vnd.apple.mpegurl", ".ts": "video/mp2t", ".vtt": "text/vtt",
                 ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


class R2NotConfigured(Exception):
    pass


def masters_bucket():
    return os.getenv("R2_MASTERS_BUCKET", "taichi-masters")


def streams_bucket():
    return os.getenv("R2_STREAMS_BUCKET", "taichi-streams")


def client():
    account = os.getenv("R2_ACCOUNT_ID")
    endpoint = os.getenv("R2_ENDPOINT_URL") or (f"https://{account}.r2.cloudflarestorage.com" if account else None)
    key_id, secret = os.getenv("R2_ACCESS_KEY_ID"), os.getenv("R2_SECRET_ACCESS_KEY")
    if not endpoint or not key_id or not secret:
        raise R2NotConfigured("Video storage is not set up yet (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY).")
    return boto3.client("s3", endpoint_url=endpoint, aws_access_key_id=key_id, aws_secret_access_key=secret,
                        region_name="auto", config=Config(signature_version="s3v4", retries={"max_attempts": 5}))


# ----- browser multipart uploads -----

def start_multipart(bucket, key, content_type):
    return client().create_multipart_upload(Bucket=bucket, Key=key, ContentType=content_type or "application/octet-stream")["UploadId"]


def presign_part(bucket, key, upload_id, part_number):
    return client().generate_presigned_url("upload_part", ExpiresIn=PRESIGN_SECONDS, Params={
        "Bucket": bucket, "Key": key, "UploadId": upload_id, "PartNumber": int(part_number)})


def list_parts(bucket, key, upload_id):
    s3, parts, marker = client(), [], 0
    while True:
        resp = s3.list_parts(Bucket=bucket, Key=key, UploadId=upload_id, PartNumberMarker=marker)
        parts += [{"part_number": p["PartNumber"], "etag": p["ETag"], "size": p["Size"]} for p in resp.get("Parts", [])]
        if not resp.get("IsTruncated"):
            return parts
        marker = resp["NextPartNumberMarker"]


def complete_multipart(bucket, key, upload_id, parts):
    client().complete_multipart_upload(Bucket=bucket, Key=key, UploadId=upload_id, MultipartUpload={
        "Parts": [{"PartNumber": int(p["part_number"]), "ETag": p["etag"]} for p in sorted(parts, key=lambda p: int(p["part_number"]))]})


def abort_multipart(bucket, key, upload_id):
    client().abort_multipart_upload(Bucket=bucket, Key=key, UploadId=upload_id)


def presign_put(bucket, key, content_type, seconds=3600):
    return client().generate_presigned_url("put_object", ExpiresIn=seconds, Params={
        "Bucket": bucket, "Key": key, "ContentType": content_type})


def object_size(bucket, key):
    return client().head_object(Bucket=bucket, Key=key)["ContentLength"]


# ----- used by the background worker -----

def download(bucket, key, path):
    client().download_file(bucket, key, path)


def upload_folder(local_dir, bucket, prefix):
    s3 = client()
    for root, _dirs, files in os.walk(local_dir):
        for name in files:
            path = os.path.join(root, name)
            rel = os.path.relpath(path, local_dir).replace(os.sep, "/")
            ext = os.path.splitext(name)[1].lower()
            content_type = CONTENT_TYPES.get(ext) or mimetypes.guess_type(name)[0] or "application/octet-stream"
            s3.upload_file(path, bucket, f"{prefix}/{rel}", ExtraArgs={"ContentType": content_type})


def put_text(bucket, key, text, content_type):
    client().put_object(Bucket=bucket, Key=key, Body=text.encode("utf-8"), ContentType=content_type)


def put_bytes(bucket, key, body, content_type):
    client().put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)


def delete_prefix(bucket, prefix):
    """Deletes every object under prefix/ (a video's folder)."""
    s3 = client()
    prefix = prefix.rstrip("/") + "/"
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        keys = [{"Key": o["Key"]} for o in page.get("Contents", [])]
        if keys:
            s3.delete_objects(Bucket=bucket, Delete={"Objects": keys, "Quiet": True})


def delete_object(bucket, key):
    client().delete_object(Bucket=bucket, Key=key)
