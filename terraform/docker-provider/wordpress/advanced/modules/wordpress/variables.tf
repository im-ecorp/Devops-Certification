variable "network_name" {
  type        = string
  description = "Docker network name to attach containers to"
}

variable "name_prefix" {
  type        = string
  description = "Unique prefix for this application resources."
}
variable "wordpress_image" {
  type    = string
  default = "wordpress:php8.3-apache"
}
variable "database_image" {
  type    = string
  default = "mariadb:11.4"
}

variable "port" {
  type        = number
  description = "Host port for WordPress"
  default     = 8080
}
