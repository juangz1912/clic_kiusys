# Evidencia de ejecución — 13 de octubre de 2026

`terraform apply` dejó estos recursos en `sa-bogota-1`:

- `oci_core_vcn.this`
- `oci_core_subnet.public`
- `oci_core_internet_gateway.this`
- `oci_objectstorage_bucket.flow` (`clic-kiusys-flow`)
- `oci_objectstorage_bucket.tfstate`
- `oci_database_autonomous_database.this` (`clic-kiusys-adb`, Always Free)
- `oci_core_instance.api` (`VM.Standard.E5.Flex`, 1 OCPU, 4 GB)
- `oci_load_balancer_load_balancer.api` (flexible, 10 Mbps)

Ampere Always Free y `VM.Standard.E4.Flex` respondieron `Out of host capacity`. Por eso el API quedó en E5.

Health a través del balanceador:

```bash
curl -fsS http://157.137.198.114/api/v2/health
```

```json
{"status":"ok","service":"clic-kiusys-pss","api_version":"v2","environment":"produccion","cloud_provider":"oci","oke_cluster_name":"vm-e5-flex","trace_id":"b3effd56-5045-4bc0-9818-5f8d5710d74b"}
```

`GET /api/v2/entidades/vuelos` respondió `[]`. El health consulta PostgreSQL, así que la base de la VM está atendiendo.

El estado quedó en el bucket `clic-kiusys-tfstate`, objeto `terraform.tfstate`. No está en git.
