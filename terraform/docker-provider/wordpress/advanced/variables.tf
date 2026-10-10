variable "docker_host" {
  type        = string
  description = "Docker daemon endpoint for this practice lab."
  default     = "unix:///var/run/docker.sock"
}
variable "project_name" {
  type    = string
  default = "tf-docker-practice"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,39}$", var.project_name))
    error_message = "Use a lowercase name starting with a letter, at most 40 characters."
  }
}
variable "wordpress_port" {
  type    = number
  default = 8080
  validation {
    condition     = var.wordpress_port >= 1024 && var.wordpress_port <= 65535 && floor(var.wordpress_port) == var.wordpress_port
    error_message = "Choose an integer port between 1024 and 65535."
  }
}
variable "wordpress_image" {
  type    = string
  default = "wordpress:php8.3-apache"
}
variable "database_image" {
  type    = string
  default = "mariadb:11.4"
}
