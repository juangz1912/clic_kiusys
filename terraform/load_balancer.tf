resource "oci_load_balancer_load_balancer" "api" {
  compartment_id = local.compartment_id
  display_name   = "${local.name}-lb"
  shape          = "flexible"
  subnet_ids     = [oci_core_subnet.public.id]
  is_private     = false
  freeform_tags  = local.tags

  # El primer balanceador flexible de 10 Mbps entra en Always Free.
  shape_details {
    minimum_bandwidth_in_mbps = 10
    maximum_bandwidth_in_mbps = 10
  }
}

resource "oci_load_balancer_backend_set" "api" {
  load_balancer_id = oci_load_balancer_load_balancer.api.id
  name             = "api"
  policy           = "ROUND_ROBIN"

  health_checker {
    protocol          = "HTTP"
    port              = 8000
    url_path          = "/api/v2/health"
    return_code       = 200
    interval_ms       = 10000
    timeout_in_millis = 3000
    retries           = 3
  }
}

resource "oci_load_balancer_backend" "api" {
  load_balancer_id = oci_load_balancer_load_balancer.api.id
  backendset_name  = oci_load_balancer_backend_set.api.name
  ip_address       = data.oci_core_vnic.api.private_ip_address
  port             = 8000
}

resource "oci_load_balancer_listener" "http" {
  load_balancer_id         = oci_load_balancer_load_balancer.api.id
  name                     = "http"
  default_backend_set_name = oci_load_balancer_backend_set.api.name
  port                     = 80
  protocol                 = "HTTP"
}
