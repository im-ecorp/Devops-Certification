# Display calculated values after an apply
output "full_name" {
  description = "The composed project name."
  value       = local.full_name
}

output "server_names" {
  description = "Generated names for simulated servers."
  value       = local.server_names
}

output "tags" {
  description = "Common metadata map."
  value       = local.common_tags
}
