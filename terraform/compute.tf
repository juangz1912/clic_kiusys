data "oci_core_images" "ol" {
  compartment_id   = local.compartment_id
  operating_system = "Oracle Linux"
  shape            = "VM.Standard.A1.Flex"
  sort_by          = "TIMECREATED"
  sort_order       = "DESC"
}

resource "oci_core_instance" "api" {
  compartment_id      = local.compartment_id
  availability_domain = local.availability_domain
  display_name        = "${local.name}-api"
  # Always Free: Ampere A1, 1 OCPU y 6 GB (dentro de 4 OCPU / 24 GB).
  # Hay que destruirla al terminar la sustentación: bash destruir.sh
  shape         = "VM.Standard.A1.Flex"
  freeform_tags = local.tags

  shape_config {
    ocpus         = 1
    memory_in_gbs = 6
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.ol.images[0].id
    boot_volume_size_in_gbs = "50"
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.public.id
    assign_public_ip = true
    hostname_label   = "clicapi"
    display_name     = "${local.name}-api-vnic"
  }

  metadata = {
    ssh_authorized_keys = tls_private_key.ssh.public_key_openssh
    user_data           = base64encode(local.api_cloud_init)
  }

  timeouts {
    create = "20m"
  }
}

locals {
  api_cloud_init = sensitive(templatefile("${path.module}/cloud-init/api.yaml.tftpl", {
    db_password   = random_password.db.result
    namespace     = data.oci_objectstorage_namespace.ns.namespace
    bucket        = oci_objectstorage_bucket.flow.name
    region        = var.region
    s3_access_key = oci_identity_customer_secret_key.api.id
    s3_secret_key = oci_identity_customer_secret_key.api.key
  }))
}

data "oci_core_vnic_attachments" "api" {
  compartment_id = local.compartment_id
  instance_id    = oci_core_instance.api.id
}

data "oci_core_vnic" "api" {
  vnic_id = data.oci_core_vnic_attachments.api.vnic_attachments[0].vnic_id
}
