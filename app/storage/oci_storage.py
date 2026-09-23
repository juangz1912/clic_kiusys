import json
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.storage.base import ObjectStorage


class OciObjectStorage:
    backend = "oci"

    def __init__(
        self,
        namespace: str,
        bucket: str,
        region: str,
        access_key: str,
        secret_key: str,
    ):
        self.bucket = bucket
        self.namespace = namespace
        endpoint = f"https://{namespace}.compat.objectstorage.{region}.oraclecloud.com"
        self.client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint,
            config=Config(signature_version="s3v4"),
        )

    def _get_object(self, object_key: str) -> dict:
        try:
            return self.client.get_object(Bucket=self.bucket, Key=object_key)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"NoSuchKey", "404", "NotFound"}:
                raise FileNotFoundError(object_key) from exc
            raise

    def put_json(self, object_key: str, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=body,
            ContentType="application/json",
        )

    def get_json(self, object_key: str) -> dict[str, Any]:
        response = self._get_object(object_key)
        raw = response["Body"].read().decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("object is not a JSON object")
        return data

    def put_bytes(self, object_key: str, data: bytes, content_type: str) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=data,
            ContentType=content_type,
        )

    def get_bytes(self, object_key: str) -> tuple[bytes, str]:
        response = self._get_object(object_key)
        content_type = response.get("ContentType") or "application/octet-stream"
        return response["Body"].read(), content_type

    def list_keys(self, prefix: str) -> list[str]:
        keys: list[str] = []
        token = None
        while True:
            kwargs: dict[str, Any] = {"Bucket": self.bucket, "Prefix": prefix}
            if token:
                kwargs["ContinuationToken"] = token
            page = self.client.list_objects_v2(**kwargs)
            keys.extend(item["Key"] for item in page.get("Contents") or [])
            if not page.get("IsTruncated"):
                break
            token = page.get("NextContinuationToken")
        return keys
