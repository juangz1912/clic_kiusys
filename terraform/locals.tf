locals {
  name           = "clic-kiusys"
  compartment_id = var.tenancy_ocid
  vcn_cidr       = "10.0.0.0/16"
  subnet_cidr    = "10.0.1.0/24"
  tags = {
    proyecto    = "clic-kiusys"
    seguimiento = "3"
    managed_by  = "terraform"
  }
}
