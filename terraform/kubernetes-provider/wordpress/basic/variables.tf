variable "kube_context" {
  type        = string
  description = "The specific context from your kubeconfig to use for this practice lab."
}

variable "kube_config_path" {
  type        = string
  description = "Path to the Kubernetes configuration file."
  default     = "~/.kube/config"
}

variable "db_password" {
  type        = string
  description = "The WordPress database user password. Required; do not set a default."
  sensitive   = true
}

variable "storage_class_name" {
  type        = string
  description = "Optional custom storage class. Defaults to the cluster's default storage class if null."
  default     = null
}
