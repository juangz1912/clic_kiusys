from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Clic KiuSys PSS API"
    environment: str = "pruebas"
    database_url: str = "postgresql://pss:pss@localhost:5432/pss_pruebas"
    hold_minutes: int = 10

    cloud_provider: str = "oci"
    oke_cluster_name: str = "clic-kiusys-oke"

    api_b_base_url: str = ""
    api_b_entity_path: str = "/api/mascotas"
    api_c_base_url: str = ""
    api_c_entity_path: str = "/api/items"
    integration_timeout_seconds: float = 10.0
    integration_stub_when_unreachable: bool = True

    observability_saas_url: str = ""

    object_storage_backend: str = "local"
    object_storage_local_dir: str = "./data/object-storage"
    oci_os_namespace: str = ""
    oci_os_bucket: str = "clic-kiusys-flow"
    oci_os_region: str = ""
    oci_s3_access_key_id: str = ""
    oci_s3_secret_access_key: str = ""
    public_api_base_url: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if isinstance(value, str) and value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql://", 1)
        return value


settings = Settings()
