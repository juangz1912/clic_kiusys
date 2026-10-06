data "oci_objectstorage_namespace" "ns" {
  compartment_id = local.compartment_id
}

resource "oci_objectstorage_bucket" "flow" {
  compartment_id = local.compartment_id
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  name           = "${local.name}-flow"
  access_type    = "NoPublicAccess"
  versioning     = "Enabled"
  storage_tier   = "Standard"
  freeform_tags  = local.tags
}

resource "oci_objectstorage_bucket" "tfstate" {
  compartment_id = local.compartment_id
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  name           = "${local.name}-tfstate"
  access_type    = "NoPublicAccess"
  versioning     = "Enabled"
  storage_tier   = "Standard"
  freeform_tags  = local.tags
}

resource "oci_identity_customer_secret_key" "api" {
  display_name = "${local.name}-s3-tf"
  user_id      = var.user_ocid
}
