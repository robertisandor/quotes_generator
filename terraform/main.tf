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

/*
resource "aws_db_instance" "quotes_generator" {
  identifier           = "quotes-generator"
  instance_class       = "db.t3.micro"
  allocated_storage    = 5
  engine               = "postgres"
  engine_version       = "15.4"
  db_name              = "quotes_db"
  username             = "postgres"
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

  parameter {
    name = "rds.force_ssl"
    value = "0"
  }
}

resource "aws_vpc" "quotes_main" {
  cidr_block = "172.31.0.0/16"
  instance_tenancy = "default"
  enable_dns_support = true
  enable_dns_hostnames = true 
  enable_network_address_usage_metrics = false 
}

resource "aws_route_table" "quotes_route_table" {
  vpc_id = aws_vpc.quotes_main.id

  route {
    cidr_block        = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.quotes_gateway.id
  }
}

resource "aws_subnet" "quotes_1" {
  cidr_block = "172.31.0.0/20"
  vpc_id     = aws_vpc.quotes_main.id
}

resource "aws_subnet" "quotes_2" {
  cidr_block = "172.31.16.0/20"
  vpc_id     = aws_vpc.quotes_main.id
}

resource "aws_subnet" "quotes_3" {
  cidr_block = "172.31.32.0/20"
  vpc_id     = aws_vpc.quotes_main.id
}

resource "aws_vpc_dhcp_options" "quotes_dns_resolver" {
  domain_name_servers  = ["AmazonProvidedDNS"]
}

resource "aws_internet_gateway" "quotes_gateway" {
  vpc_id = aws_vpc.quotes_main.id
}

resource "aws_network_acl" "main" {
  vpc_id = aws_vpc.quotes_main.id
  subnet_ids = [aws_subnet.quotes_1.id, aws_subnet.quotes_2.id, aws_subnet.quotes_3.id]

  ingress {
    protocol   = "-1"
    rule_no    = 1
    action     = "deny"
    cidr_block = "0.0.0.0/0"    
    from_port  = 0
    to_port    = 0
  }

  ingress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  egress {
    protocol   = "-1"
    rule_no    = 1
    action     = "deny"
    cidr_block = "0.0.0.0/0"    
    from_port  = 0
    to_port    = 0
  }

  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }
}

resource "aws_security_group" "rds_ec2_1" {
  name        = "rds_ec2_1"
  vpc_id      = aws_vpc.quotes_main.id
}

resource "aws_vpc_security_group_ingress_rule" "allow_tls_ipv6" {
  security_group_id = aws_security_group.rds_ec2_1.id
  description       = "Rule to allow connections from EC2 instances with sg attached"
  cidr_ipv4         = aws_vpc.quotes_main.cidr_block
  from_port         = 5432
  ip_protocol       = "tcp"
  to_port           = 5432
}

resource "aws_security_group" "ec2_rds_1" {
  name        = "ec2_rds_1"
  vpc_id      = aws_vpc.quotes_main.id
}

resource "aws_vpc_security_group_egress_rule" "allow_tls_ipv6" {
  security_group_id = aws_security_group.ec2_rds_1.id
  description       = "Rule to allow connections from EC2 instances with sg attached"
  cidr_ipv4         = aws_vpc.quotes_main.cidr_block
  from_port         = 5432
  ip_protocol       = "tcp"
  to_port           = 5432
}

resource "aws_security_group" "default" {
  name        = "default"
  vpc_id      = aws_vpc.quotes_main.id
}

resource "aws_vpc_security_group_ingress_rule" "allow_ssh_access" {
  security_group_id = aws_security_group.default.id
  description       = "Rule to allow SSH connections from internet to reach EC2"
  cidr_ipv4         = aws_vpc.quotes_main.cidr_block
  from_port         = 22
  ip_protocol       = "ssh"
  to_port           = 22
}

resource "aws_vpc_security_group_ingress_rule" "allow_internet_access" {
  security_group_id = aws_security_group.default.id
  description       = "Rule to allow connections from internet to reach EC2"
  cidr_ipv4         = "98.45.195.5/32"
  from_port         = 80
  ip_protocol       = "tcp"
  to_port           = 80
}

resource "aws_network_interface" "rds_network_interface" {
  subnet_id       = aws_subnet.quotes_1.id
  private_ips     = ["172.31.14.150"]
  security_groups = [aws_security_group.rds_ec2_1.id]
}

resource "aws_network_interface" "ec2_network_interface" {
  subnet_id       = aws_subnet.quotes_2.id
  private_ips     = ["172.31.19.101"]
  security_groups = [aws_security_group.ec2_rds_1.id]
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
*/

resource "aws_iam_user" "admin_user" {
  name = "admin_test"
}

/*
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

resource "aws_key_pair" "apiuser" {
    key_name   = "apiuser"
    public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICjJ7onCRh/3ruUpmlviryTyyYWJHWwm7cmIIJMIw8xv robert.i.sandor@gmail.com"
}

data "aws_ami" "ubuntu" {
    most_recent = true

    filter {
        name   = "name"
        values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
    }

    filter {
        name   = "virtualization-type"
        values = ["hvm"]
    }

    owners = ["099720109477"] # Canonical
}

resource "aws_instance" "web" {
    ami           = data.aws_ami.ubuntu.id
    instance_type = "t2.micro"
    key_name = aws_key_pair.apiuser.key_name

    user_data = <<-EOL
    #!/bin/bash -xe

    echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICjJ7onCRh/3ruUpmlviryTyyYWJHWwm7cmIIJMIw8xv robert.i.sandor@gmail.com" >> ~/.ssh/authorized_keys

    sudo apt-get update
    sudo apt-get install ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update 
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo groupadd docker
    sudo usermod -aG docker $USER

    sudo apt-get install -y postgresql-client
    EOL

    tags = {
        Name = "QuotesApiWeb"
    }
}
*/