# Seguimiento 3 — Terraform en OCI

Infraestructura como código del mismo proyecto del seguimiento 2 (API A, Clic KiuSys). Un archivo `.tf` por servicio. No hay un único `main.tf`.

## Servicios

| Servicio | Archivo | Equivalente del seguimiento 2 | Costo |
| --- | --- | --- | --- |
| Red (VCN, subred, gateway, rutas, security list) | `network.tf` | VCN de OKE | Sin cobro |
| Object Storage | `object_storage.tf` | Bucket `clic-kiusys-flow` | Sin cobro dentro de los 10 GB Always Free |
| Balanceador flexible de 10 Mbps | `load_balancer.tf` | Load Balancer del API | El primero de 10 Mbps es Always Free |
| Autonomous Database | `database.tf` | Base de datos del proyecto | Always Free |
| Compute | `compute.tf` | OKE, donde corría el API y PostgreSQL | De pago. Destruir al terminar la sustentación |

PostgreSQL 16 corre en la VM, en `127.0.0.1:5432`, porque el API está escrito para ese motor (en el seguimiento 2 iba en un pod). Autonomous Database es la base administrada de Oracle, Always Free, creada con Terraform. El API no se conecta a ella: habla PostgreSQL, no Oracle.

La VM es `VM.Standard.E5.Flex` de 1 OCPU y 4 GB. Ampere Always Free y E4 no tenían capacidad en `sa-bogota-1` el día del despliegue. Esta VM es lo único que cobra: del orden de unos centavos de dólar por hora. El disco de 50 GB cabe en los 200 GB de Block Volume Always Free.

## Qué hace Terraform

1. `terraform init` descarga el provider de OCI.
2. `terraform plan` compara el código con el estado y muestra lo que crearía, sin tocarlo.
3. `terraform apply` llama a la API de OCI y guarda el resultado en `terraform.tfstate`.
4. `terraform destroy` borra solo lo que está en ese estado.

El estado también se sube al bucket privado `clic-kiusys-tfstate` para que el pipeline pueda seguir desde GitHub. No se commitea: tiene la clave SSH y las contraseñas.

## Desplegar en local

Hace falta Terraform 1.6+ y la config de OCI CLI (`~/.oci/apikey.config`).

```bash
cd terraform
source ./env.sh
terraform init
terraform plan
terraform apply
bash guardar_estado.sh
bash instalar_api.sh
```

`instalar_api.sh` espera a que cloud-init termine, copia `app/` a la VM, instala las dependencias en un virtualenv y arranca uvicorn. El pipeline hace los mismos pasos.

## Pipeline

En GitHub Actions, disparo manual:

- `Terraform OCI` (`.github/workflows/terraform-oci.yml`): `terraform apply`, guarda el estado e instala el API.
- `Terraform destruir` (`.github/workflows/terraform-destruir.yml`): `terraform destroy`.

Usa los secrets que ya estaban en el repo: `OCI_CLI_USER`, `OCI_CLI_TENANCY`, `OCI_CLI_FINGERPRINT`, `OCI_CLI_KEY`.

## Destruir al terminar la sustentación

```bash
cd terraform
bash destruir.sh
```

O el workflow `Terraform destruir`. Eso apaga la VM, la base, el balanceador, los buckets y la red. Hay que correrlo el mismo día de la sustentación para que la VM no siga cobrando.

## URL de esta ejecución

http://157.137.198.114/api/v2/health

La VM del API es `157.137.198.156`. Postgres no está publicado a internet.
