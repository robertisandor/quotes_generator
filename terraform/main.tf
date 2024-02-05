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

resource "aws_iam_group" "admin_group_test" {
  name = "admin_group_test"
  path = "/admin_group_test/"
}

resource "aws_iam_user_group_membership" "admin_group_membership" {
  user = aws_iam_user.admin_user.name

  groups = [
    aws_iam_group.admin_group_test.name,
  ]
}

resource "aws_iam_user" "admin_user" {
  name = "admin_test"
}

resource "aws_iam_group_policy" "admin_policy" {
  name  = "admin_db_policy"
  group = aws_iam_group.admin_group_test.name

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  policy = jsonencode({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": "rds:DescribeDBParameterGroups",
                "Resource": "arn:aws:rds:*:487577641151:pg:*"
            }
        ]
    })
}
