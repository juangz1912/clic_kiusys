data "oci_identity_availability_domains" "ads" {
  compartment_id = local.compartment_id
}

locals {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
}

resource "oci_core_vcn" "this" {
  compartment_id = local.compartment_id
  display_name   = "${local.name}-vcn"
  cidr_blocks    = [local.vcn_cidr]
  dns_label      = "clickiuss3"
  freeform_tags  = local.tags
}

resource "oci_core_internet_gateway" "this" {
  compartment_id = local.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "${local.name}-igw"
  enabled        = true
  freeform_tags  = local.tags
}

resource "oci_core_route_table" "public" {
  compartment_id = local.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "${local.name}-public-rt"
  freeform_tags  = local.tags

  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.this.id
    description       = "Salida a internet"
  }
}

resource "oci_core_security_list" "public" {
  compartment_id = local.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "${local.name}-public-sl"
  freeform_tags  = local.tags

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
    description = "Salida"
  }

  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    description = "SSH para instalar el API"
    tcp_options {
      min = 22
      max = 22
    }
  }

  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    description = "HTTP del balanceador"
    tcp_options {
      min = 80
      max = 80
    }
  }

  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    description = "API stable y health check del balanceador"
    tcp_options {
      min = 8000
      max = 8000
    }
  }

  ingress_security_rules {
    protocol    = "6"
    source      = "10.0.0.0/16"
    description = "API canary, solo desde la VCN"
    tcp_options {
      min = 8001
      max = 8001
    }
  }

}

resource "oci_core_subnet" "public" {
  compartment_id             = local.compartment_id
  vcn_id                     = oci_core_vcn.this.id
  display_name               = "${local.name}-public"
  cidr_block                 = local.subnet_cidr
  dns_label                  = "public"
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.public.id]
  prohibit_public_ip_on_vnic = false
  freeform_tags              = local.tags
}
