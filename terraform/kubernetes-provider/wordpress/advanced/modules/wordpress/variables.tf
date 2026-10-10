variable "namespace" {
  description = "Dedicated namespace owned by the WordPress lab."
  type        = string
  default     = "tf-k8s-practice"
  nullable    = false
  validation {
    condition     = length(var.namespace) <= 63 && can(regex("^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", var.namespace))
    error_message = "namespace must be a Kubernetes DNS label of at most 63 characters."
  }
}

variable "storage_class_name" {
  description = "StorageClass for both PVCs; null selects the cluster default."
  type        = string
  default     = null
  validation {
    condition     = var.storage_class_name == null ? true : length(trimspace(var.storage_class_name)) > 0
    error_message = "storage_class_name must be null or a non-empty StorageClass name."
  }
}

variable "database_storage_size" {
  description = "MariaDB PVC size in Mi or Gi."
  type        = string
  default     = "5Gi"
  nullable    = false
  validation {
    condition     = can(regex("^[1-9][0-9]*(Mi|Gi)$", var.database_storage_size))
    error_message = "database_storage_size must be a positive Mi or Gi quantity."
  }
}

variable "wordpress_storage_size" {
  description = "WordPress files PVC size in Mi or Gi."
  type        = string
  default     = "5Gi"
  nullable    = false
  validation {
    condition     = can(regex("^[1-9][0-9]*(Mi|Gi)$", var.wordpress_storage_size))
    error_message = "wordpress_storage_size must be a positive Mi or Gi quantity."
  }
}
