variable "tenancy_ocid" {
  description = "OCID del tenancy. También es el compartimento raíz."
  type        = string
  sensitive   = true
}

variable "user_ocid" {
  description = "OCID del usuario con el que Terraform llama a OCI."
  type        = string
  sensitive   = true
}

variable "fingerprint" {
  description = "Fingerprint de la clave API."
  type        = string
  sensitive   = true
}

variable "private_key_path" {
  description = "Ruta local de la clave privada API. No se sube al repositorio."
  type        = string
  sensitive   = true
}

variable "region" {
  description = "Región del seguimiento 2."
  type        = string
  default     = "sa-bogota-1"
}
