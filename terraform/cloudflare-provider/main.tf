# The provider reads CLOUDFLARE_API_TOKEN from your environment.
provider "cloudflare" {}

# 1. A Record (IPv4 Address)
resource "cloudflare_dns_record" "practice_a" {
  zone_id = var.zone_id
  name    = "tf-a.${var.domain}"
  type    = "A"
  content = var.ipv4_address
  ttl     = var.ttl
  proxied = false
  comment = "Terraform practice - A record"
}

# 2. CNAME Record (Alias)
resource "cloudflare_dns_record" "practice_cname" {
  zone_id = var.zone_id
  name    = "tf-cname.${var.domain}"
  type    = "CNAME"
  content = "tf-a.${var.domain}"
  ttl     = var.ttl
  proxied = false
  comment = "Terraform practice - CNAME record"
}

# 3. TXT Record (Text verification)
resource "cloudflare_dns_record" "practice_txt" {
  zone_id = var.zone_id
  name    = "tf-txt.${var.domain}"
  type    = "TXT"
  content = "terraform-practice-verification-string"
  ttl     = var.ttl
  comment = "Terraform practice - TXT record"
}

# 4. MX Record (Mail routing)
resource "cloudflare_dns_record" "practice_mx" {
  zone_id  = var.zone_id
  name     = "tf-mx.${var.domain}"
  type     = "MX"
  content  = "mail.${var.domain}"
  ttl      = var.ttl
  priority = 10
  comment  = "Terraform practice - MX record"
}
