resource "oci_database_autonomous_database" "this" {
  compartment_id              = local.compartment_id
  db_name                     = "clicdb"
  display_name                = "${local.name}-adb"
  db_workload                 = "OLTP"
  is_free_tier                = true
  admin_password              = random_password.db.result
  is_auto_scaling_enabled     = false
  is_mtls_connection_required = true
  freeform_tags               = local.tags
}
