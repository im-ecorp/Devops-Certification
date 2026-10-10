# Inputs for our configuration
variable "project_name" {
  description = "The name of the project."
  type        = string
  default     = "terraform-practice"
}

variable "environment" {
  description = "The deployment environment (dev, stage, prod)."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "Environment must be dev, stage, or prod."
  }
}

variable "instance_count" {
  description = "How many instances to simulate."
  type        = number
  default     = 2

  validation {
    condition     = var.instance_count > 0
    error_message = "Instance count must be at least 1."
  }
}
