output "rds_hostname" {
  description = "RDS instance hostname"
  value       = aws_db_instance.quotes_generator.address
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.quotes_generator.port
  sensitive   = true
}

output "rds_username" {
  description = "RDS instance root username"
  value       = aws_db_instance.quotes_generator.username
  sensitive   = true
}

output "ec2_hostname" {
  value	      = aws_instance.web.public_ip
}
