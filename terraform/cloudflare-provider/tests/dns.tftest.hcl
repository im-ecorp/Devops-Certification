mock_provider "cloudflare" {}

variables {
  zone_id = "00000000000000000000000000000000"
  domain  = "example.com"
}

run "validate_diverse_records" {
  command = plan

  assert {
    condition     = cloudflare_dns_record.practice_a.type == "A"
    error_message = "A record must be created."
  }

  assert {
    condition     = cloudflare_dns_record.practice_cname.type == "CNAME" && cloudflare_dns_record.practice_cname.content == "tf-a.example.com"
    error_message = "CNAME must point to the A record."
  }

  assert {
    condition     = cloudflare_dns_record.practice_txt.type == "TXT"
    error_message = "TXT record must be created."
  }

  assert {
    condition     = cloudflare_dns_record.practice_mx.type == "MX" && cloudflare_dns_record.practice_mx.priority == 10
    error_message = "MX record must have a priority."
  }
}
