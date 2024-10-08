output "ec2_hostname" {
  description = "EC2 instance public IP"
  value	      = aws_instance.web.public_ip
  sensitive   = true
}

output "rds_hostname" {
  description = "RDS instance hostname"
  value       = aws_db_instance.quotes_generator.address
  sensitive   = true
}

output "rds_username" {
  description = "RDS instance root username"
  value       = aws_db_instance.quotes_generator.username
  sensitive   = true
}

output "rds_password" {
  description = "RDS instance root password"
  value       = aws_db_instance.quotes_generator.password  
  sensitive   = true
}
