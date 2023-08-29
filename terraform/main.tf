terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }

  required_version = ">= 0.14.6"
}

provider "aws" {
  region = "us-east-2"
}

resource "aws_db_instance" "quotes_generator" {
  identifier           = "quotes-generator"
  instance_class       = "db.t3.micro"
  allocated_storage    = 5
  engine               = "postgres"
  engine_version       = "15.4"
  username             = "api"
  password             = var.db_password
#   db_subnet_group_name = aws_db_subnet_group.quotes_generator.name
  parameter_group_name = aws_db_parameter_group.quotes_generator.name
  publicly_accessible  = false
  skip_final_snapshot  = false
}

resource "aws_db_parameter_group" "quotes_generator" {
  name   = "quotes-generator"
  family = "postgres15"

  parameter {
    name  = "log_connections"
    value = "1"
  }
}