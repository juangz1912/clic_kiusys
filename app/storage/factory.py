from functools import lru_cache

from app.config import settings
from app.storage.local_storage import LocalObjectStorage
from app.storage.oci_storage import OciObjectStorage


@lru_cache
def get_object_storage():
    backend = settings.object_storage_backend.lower()
    if backend == "oci":
        if not all(
            [
                settings.oci_os_namespace,
                settings.oci_os_bucket,
                settings.oci_os_region,
                settings.oci_s3_access_key_id,
                settings.oci_s3_secret_access_key,
            ]
        ):
            raise RuntimeError("Object storage OCI incompleto: revisa variables OCI_OS_* y OCI_S3_*")
        return OciObjectStorage(
            namespace=settings.oci_os_namespace,
            bucket=settings.oci_os_bucket,
            region=settings.oci_os_region,
            access_key=settings.oci_s3_access_key_id,
            secret_key=settings.oci_s3_secret_access_key,
        )
    return LocalObjectStorage(settings.object_storage_local_dir, bucket_label=settings.oci_os_bucket or "local")
