variable "docker_host" {
  type        = string
  description = "Docker daemon endpoint. Change if using a remote host or Windows."
  default     = "unix:///var/run/docker.sock"
}

variable "project_name" {
  type        = string
  description = "Prefix for all resources to avoid conflicts."
  default     = "tf-docker-basic-wp"
}

variable "db_password" {
  type        = string
  description = "The database password. Required. Do not set a default here."
  sensitive   = true
}

variable "wordpress_port" {
  type        = number
  description = "Port on your host machine to map to WordPress."
  default     = 8083
}
