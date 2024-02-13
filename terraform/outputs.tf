output "ec2_hostname" {
  value	      = aws_instance.web.public_ip
}
