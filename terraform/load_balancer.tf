variable "canary_percent" {
  description = "Porcentaje de tráfico público hacia el canary: 0, 10, 50 o 100."
  type        = number
  default     = 0

  validation {
    condition     = contains([0, 10, 50, 100], var.canary_percent)
    error_message = "canary_percent debe ser 0, 10, 50 o 100."
  }
}

locals {
  stable_weight = 100 - var.canary_percent
}

resource "oci_load_balancer_load_balancer" "api" {
  compartment_id = local.compartment_id
  display_name   = "${local.name}-lb"
  shape          = "flexible"
  subnet_ids     = [oci_core_subnet.public.id]
  is_private     = false
  freeform_tags  = local.tags

  shape_details {
    minimum_bandwidth_in_mbps = 10
    maximum_bandwidth_in_mbps = 10
  }
}

resource "oci_load_balancer_backend_set" "stable" {
  load_balancer_id = oci_load_balancer_load_balancer.api.id
  name             = "stable"
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

resource "oci_load_balancer_backend" "stable" {
  load_balancer_id = oci_load_balancer_load_balancer.api.id
  backendset_name  = oci_load_balancer_backend_set.stable.name
  ip_address       = data.oci_core_vnic.api.private_ip_address
  port             = 8000
}

resource "oci_load_balancer_backend_set" "canary" {
  load_balancer_id = oci_load_balancer_load_balancer.api.id
  name             = "canary"
  policy           = "ROUND_ROBIN"

  health_checker {
    protocol          = "HTTP"
    port              = 8001
    url_path          = "/api/v2/health"
    return_code       = 200
    interval_ms       = 10000
    timeout_in_millis = 3000
    retries           = 3
  }
}

resource "oci_load_balancer_backend" "canary" {
  load_balancer_id = oci_load_balancer_load_balancer.api.id
  backendset_name  = oci_load_balancer_backend_set.canary.name
  ip_address       = data.oci_core_vnic.api.private_ip_address
  port             = 8001
}

resource "oci_load_balancer_backend_set" "split" {
  load_balancer_id = oci_load_balancer_load_balancer.api.id
  name             = "split"
  policy           = "WEIGHTED_ROUND_ROBIN"

  health_checker {
    protocol          = "HTTP"
    port              = 0
    url_path          = "/api/v2/health"
    return_code       = 200
    interval_ms       = 10000
    timeout_in_millis = 3000
    retries           = 3
  }
}

resource "oci_load_balancer_backend" "split_stable" {
  count            = var.canary_percent < 100 ? 1 : 0
  load_balancer_id = oci_load_balancer_load_balancer.api.id
  backendset_name  = oci_load_balancer_backend_set.split.name
  ip_address       = data.oci_core_vnic.api.private_ip_address
  port             = 8000
  weight           = local.stable_weight
}

resource "oci_load_balancer_backend" "split_canary" {
  count            = var.canary_percent > 0 ? 1 : 0
  load_balancer_id = oci_load_balancer_load_balancer.api.id
  backendset_name  = oci_load_balancer_backend_set.split.name
  ip_address       = data.oci_core_vnic.api.private_ip_address
  port             = 8001
  weight           = var.canary_percent
}

resource "oci_load_balancer_load_balancer_routing_policy" "canary" {
  load_balancer_id           = oci_load_balancer_load_balancer.api.id
  name                       = "canary_routes"
  condition_language_version = "V1"

  rules {
    name      = "forzar_canary"
    condition = "any(http.request.headers[(i 'x-canary')] eq (i 'true'))"
    actions {
      name             = "FORWARD_TO_BACKENDSET"
      backend_set_name = oci_load_balancer_backend_set.canary.name
    }
  }

  rules {
    name      = "forzar_stable"
    condition = "any(http.request.headers[(i 'x-canary')] eq (i 'false'))"
    actions {
      name             = "FORWARD_TO_BACKENDSET"
      backend_set_name = oci_load_balancer_backend_set.stable.name
    }
  }
}

resource "oci_load_balancer_listener" "http" {
  load_balancer_id         = oci_load_balancer_load_balancer.api.id
  name                     = "http"
  default_backend_set_name = oci_load_balancer_backend_set.split.name
  routing_policy_name      = oci_load_balancer_load_balancer_routing_policy.canary.name
  port                     = 80
  protocol                 = "HTTP"

  depends_on = [
    oci_load_balancer_backend.split_stable,
    oci_load_balancer_backend.stable,
    oci_load_balancer_backend.canary,
  ]
}
