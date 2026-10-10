output "record_a" {
  description = "A record name and IP."
  value       = "${cloudflare_dns_record.practice_a.name} -> ${cloudflare_dns_record.practice_a.content}"
}

output "record_cname" {
  description = "CNAME record alias."
  value       = "${cloudflare_dns_record.practice_cname.name} -> ${cloudflare_dns_record.practice_cname.content}"
}

output "record_txt" {
  description = "TXT record content."
  value       = "${cloudflare_dns_record.practice_txt.name} -> ${cloudflare_dns_record.practice_txt.content}"
}

output "record_mx" {
  description = "MX record content."
  value       = "${cloudflare_dns_record.practice_mx.name} -> ${cloudflare_dns_record.practice_mx.content} (Priority: ${cloudflare_dns_record.practice_mx.priority})"
}
