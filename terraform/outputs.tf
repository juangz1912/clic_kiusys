output "api_url" {
  description = "URL pública del API detrás del balanceador."
  value       = "http://${oci_load_balancer_load_balancer.api.ip_address_details[0].ip_address}/api/v2/health"
}

output "lb_ocid" {
  description = "OCID del balanceador, para cambiar el peso del canary."
  value       = oci_load_balancer_load_balancer.api.id
}

output "canary_percent" {
  description = "Porcentaje público que va al canary."
  value       = var.canary_percent
}

output "api_public_ip" {
  description = "IP pública de la VM del API."
  value       = data.oci_core_vnic.api.public_ip_address
}

output "autonomous_database" {
  description = "Base Always Free de OCI. El API usa PostgreSQL local, el mismo motor del seguimiento 2."
  value       = oci_database_autonomous_database.this.display_name
}

output "bucket_name" {
  description = "Bucket de Object Storage de los mensajes del flujo."
  value       = oci_objectstorage_bucket.flow.name
}

output "tfstate_bucket" {
  description = "Bucket privado donde el pipeline guarda el estado de Terraform."
  value       = oci_objectstorage_bucket.tfstate.name
}

output "namespace" {
  description = "Namespace de Object Storage."
  value       = data.oci_objectstorage_namespace.ns.namespace
}

output "ssh_private_key" {
  description = "Clave para entrar como opc a las dos VM. Solo vive en el estado."
  value       = tls_private_key.ssh.private_key_openssh
  sensitive   = true
}
