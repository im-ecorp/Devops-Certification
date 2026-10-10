variable "zone_id" {
  description = "ID of an existing Cloudflare zone (Dashboard > domain > Overview)."
  type        = string

  validation {
    condition     = can(regex("^[0-9a-f]{32}$", var.zone_id))
    error_message = "zone_id must be a 32-character lowercase hexadecimal Cloudflare Zone ID."
  }
}

variable "domain" {
  description = "Domain of that zone, without a scheme or trailing dot (for example, example.com)."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9.-]*[a-z0-9])?\\.[a-z]{2,}$", var.domain))
    error_message = "Use a lowercase domain such as example.com, not a URL."
  }
}

variable "ipv4_address" {
  description = "A-record content. The default is a documentation-only IP."
  type        = string
  default     = "192.0.2.10"

  validation {
    condition     = can(cidrnetmask("${var.ipv4_address}/32"))
    error_message = "ipv4_address must be a valid IPv4 address."
  }
}

variable "ttl" {
  description = "DNS-only TTL in seconds; 1 means automatic."
  type        = number
  default     = 300

  validation {
    condition     = var.ttl == 1 || (var.ttl >= 60 && var.ttl <= 86400 && floor(var.ttl) == var.ttl)
    error_message = "ttl must be 1 (automatic) or a whole number from 60 to 86400."
  }
}
