terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.67"
    }
  }

  required_version = ">= 0.14.6"
  
  backend "s3" {
    bucket         = "inflation-price-tracker-production"
    key            = "state/terraform.tfstate"
    region         = "us-east-2"
    encrypt        = true
    kms_key_id     = "alias/inflation-price-tracker-production-terraform-bucket-key"
    use_lockfile   = true
  }
}

provider "aws" {
  region = "us-east-2"
}

resource "aws_s3_bucket" "inflation-price-tracker" {
  bucket = "inflation-price-tracker-production"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "quotes" {
  bucket = aws_s3_bucket.inflation-price-tracker.id 

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.inflation-price-tracker-production-terraform-bucket-key.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_ownership_controls" "inflation-price-tracker" {
  bucket = aws_s3_bucket.inflation-price-tracker.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "inflation-price-tracker" {
  depends_on = [aws_s3_bucket_ownership_controls.inflation-price-tracker]

  bucket = aws_s3_bucket.inflation-price-tracker.id
  acl    = "private"
}

resource "aws_s3_bucket_public_access_block" "block" {
  bucket = aws_s3_bucket.inflation-price-tracker.id
 
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_kms_key" "inflation-price-tracker-production-terraform-bucket-key" {
  description             = "This key is used to encrypt bucket objects"
  deletion_window_in_days = 10
  enable_key_rotation     = true
}
 
resource "aws_kms_alias" "key-alias" {
  name          = "alias/inflation-price-tracker-production-terraform-bucket-key"
  target_key_id = aws_kms_key.inflation-price-tracker-production-terraform-bucket-key.key_id
}

data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "../ingestion/package"
  output_path = "target_webscraper_deployment_package.zip"
}

resource "aws_lambda_function" "target_webscraper" {
  filename          = "target_webscraper_deployment_package.zip"
  function_name     = "target_webscraper_api"
  role              = aws_iam_role.target_webscraper_role.arn 
  handler           = "target_webscraper.lambda_handler"
  timeout           = 600
  memory_size       = 128
  architectures     = ["x86_64"]

  source_code_hash  = data.archive_file.lambda.output_base64sha256
  runtime           = "python3.10"
}

resource "aws_iam_role" "target_webscraper_role" {
  name               = "target_webscraper_role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  inline_policy {
    name = "lambda_basic_execution_role"

    policy = jsonencode({
      "Version": "2012-10-17",
      "Statement": [
          {
              "Effect": "Allow",
              "Action": "logs:CreateLogGroup",
              "Resource": "arn:aws:logs:us-east-2:487577641151:*"
          },
          {
              "Effect": "Allow",
              "Action": [
                  "logs:CreateLogStream",
                  "logs:PutLogEvents"
              ],
              "Resource": [
                  "arn:aws:logs:us-east-2:487577641151:log-group:/aws/lambda/target_webscraper_api:*"
              ]
          },
          {
            "Effect": "Allow",
            "Action": [
                "s3:*",
                "s3-object-lambda:*"
            ],
            "Resource": "*"
          },
          {
            "Effect": "Allow",
            "Action": [
                "kms:*",
            ],
            "Resource": "*"
          }
      ]
    })
  }
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_cloudwatch_log_group" "target_webscraper_api" {
  name = "/aws/lambda/target_webscraper_api"
  retention_in_days = 0
}

data "archive_file" "target_store_location_webscraper_lambda" {
  type        = "zip"
  source_dir  = "../ingestion/target_store_location_webscraper_package"
  output_path = "target_store_location_webscraper_package.zip"
}

resource "aws_lambda_function" "target_store_location_webscraper" {
  filename          = "target_store_location_webscraper_package.zip"
  function_name     = "target_store_location_webscraper_api"
  role              = aws_iam_role.target_store_location_webscraper_role.arn 
  handler           = "target_store_location_webscraper.lambda_handler"
  timeout           = 600
  memory_size       = 512
  architectures     = ["x86_64"]

  source_code_hash  = data.archive_file.lambda.output_base64sha256
  runtime           = "python3.10"
}

resource "aws_iam_role" "target_store_location_webscraper_role" {
  name               = "target_store_location_webscraper_role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  inline_policy {
    name = "lambda_basic_execution_role"

    policy = jsonencode({
      "Version": "2012-10-17",
      "Statement": [
          {
              "Effect": "Allow",
              "Action": "logs:CreateLogGroup",
              "Resource": "arn:aws:logs:us-east-2:487577641151:*"
          },
          {
              "Effect": "Allow",
              "Action": [
                  "logs:CreateLogStream",
                  "logs:PutLogEvents"
              ],
              "Resource": [
                  "arn:aws:logs:us-east-2:487577641151:log-group:/aws/lambda/target_store_location_webscraper_api:*"
              ]
          },
          {
            "Effect": "Allow",
            "Action": [
                "s3:*",
                "s3-object-lambda:*"
            ],
            "Resource": "*"
          },
          {
            "Effect": "Allow",
            "Action": [
                "kms:*",
            ],
            "Resource": "*"
          }
      ]
    })
  }
}

resource "aws_cloudwatch_log_group" "target_store_location_webscraper_api" {
  name = "/aws/lambda/target_store_location_webscraper_api"
  retention_in_days = 0
}

data "archive_file" "albertsons_store_location_webscraper_lambda" {
  type        = "zip"
  source_dir  = "../ingestion/albertsons_store_location_webscraper_package"
  output_path = "albertsons_store_location_webscraper_package.zip"
}

resource "aws_lambda_function" "albertsons_store_location_webscraper" {
  filename          = "albertsons_store_location_webscraper_package.zip"
  function_name     = "albertsons_store_location_webscraper_api"
  role              = aws_iam_role.albertsons_store_location_webscraper_role.arn 
  handler           = "albertsons_store_location_webscraper.lambda_handler"
  timeout           = 600
  memory_size       = 128
  architectures     = ["x86_64"]

  source_code_hash  = data.archive_file.lambda.output_base64sha256
  runtime           = "python3.10"
}

resource "aws_iam_role" "albertsons_store_location_webscraper_role" {
  name               = "albertsons_store_location_webscraper_role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  inline_policy {
    name = "lambda_basic_execution_role"

    policy = jsonencode({
      "Version": "2012-10-17",
      "Statement": [
          {
              "Effect": "Allow",
              "Action": "logs:CreateLogGroup",
              "Resource": "arn:aws:logs:us-east-2:487577641151:*"
          },
          {
              "Effect": "Allow",
              "Action": [
                  "logs:CreateLogStream",
                  "logs:PutLogEvents"
              ],
              "Resource": [
                  "arn:aws:logs:us-east-2:487577641151:log-group:/aws/lambda/albertsons_store_location_webscraper_api:*"
              ]
          },
          {
            "Effect": "Allow",
            "Action": [
                "s3:*",
                "s3-object-lambda:*"
            ],
            "Resource": "*"
          },
          {
            "Effect": "Allow",
            "Action": [
                "kms:*",
            ],
            "Resource": "*"
          }
      ]
    })
  }
}

resource "aws_cloudwatch_log_group" "albertsons_store_location_webscraper_api" {
  name = "/aws/lambda/albertsons_store_location_webscraper_api"
  retention_in_days = 0
}

data "archive_file" "target_store_location_transformer_lambda" {
  type        = "zip"
  source_dir  = "../ingestion/target_store_location_transformer_package"
  output_path = "target_store_location_transformer_package.zip"
}

resource "aws_lambda_function" "target_store_location_transformer" {
  filename          = "target_store_location_transformer_package.zip"
  function_name     = "target_store_location_transformer"
  role              = aws_iam_role.target_store_location_transformer_role.arn 
  handler           = "target_store_location_transformer.lambda_handler"
  timeout           = 600
  memory_size       = 1024
  architectures     = ["x86_64"]

  source_code_hash  = data.archive_file.lambda.output_base64sha256
  runtime           = "python3.10"
}

resource "aws_iam_role" "target_store_location_transformer_role" {
  name               = "target_store_location_transformer"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  inline_policy {
    name = "lambda_basic_execution_role"

    policy = jsonencode({
      "Version": "2012-10-17",
      "Statement": [
          {
              "Effect": "Allow",
              "Action": "logs:CreateLogGroup",
              "Resource": "arn:aws:logs:us-east-2:487577641151:*"
          },
          {
              "Effect": "Allow",
              "Action": [
                  "logs:CreateLogStream",
                  "logs:PutLogEvents"
              ],
              "Resource": [
                  "arn:aws:logs:us-east-2:487577641151:log-group:/aws/lambda/target_store_location_transformer:*"
              ]
          },
          {
            "Effect": "Allow",
            "Action": [
                "s3:*",
                "s3-object-lambda:*"
            ],
            "Resource": "*"
          },
          {
            "Effect": "Allow",
            "Action": [
                "kms:*",
            ],
            "Resource": "*"
          }
      ]
    })
  }
}

resource "aws_cloudwatch_log_group" "target_store_location_transformer" {
  name = "/aws/lambda/target_store_location_transformer"
  retention_in_days = 0
}

resource "aws_s3_object" "store_locations_s3_table_creation_script" {
  bucket = aws_s3_bucket.inflation-price-tracker.id
  key    = "deployments/glue/scripts/store_locations_s3_table_creation.py"
  source = "../ingestion/glue_scripts/store_locations_s3_table_creation.py"
}

resource "aws_glue_job" "store_location_s3_table_creation" {
  name              = "store_location_s3_table_creation"
  description       = "Glue job to create the store_location S3 table"
  role_arn          = aws_iam_role.store_location_s3_table_creation_role.arn
  glue_version      = "5.0"
  max_retries       = 0
  timeout           = 600
  number_of_workers = 2
  worker_type       = "G.1X"
  execution_class   = "STANDARD"

  command {
    script_location = "s3://${aws_s3_bucket.inflation-price-tracker.bucket}/${aws_s3_object.store_locations_s3_table_creation_script.key}"
    name            = "glueetl"
    python_version  = "3"
  }

  notification_property {
    notify_delay_after = 3 # delay in minutes
  }

  default_arguments = {
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://aws-glue-assets-487577641151-us-east-2/sparkHistoryLogs/"
    "--enable-job-insights"              = "true"
    "--enable-observability-metrics"     = "true"
    "--enable-glue-datacatalog"          = "true"
    "--job-bookmark-option"              = "job-bookmark-disable"
    "--job-language"                     = "python"
    "--TempDir"                          = "s3://aws-glue-assets-487577641151-us-east-2/temporary/"
    "--enable-auto-scaling"              = "true"
  }

  execution_property {
    max_concurrent_runs = 1
  }
}

resource "aws_iam_role" "store_location_s3_table_creation_role" {
  name = "store_location_s3_table_creation_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  inline_policy {
    name = "glue_etl_job_execution_role"

    policy = jsonencode({
      "Version": "2012-10-17",
      "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:*",
                "s3-object-lambda:*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3tables:*"
            ],
            "Resource": "*"
        }
      ]
    })
  }
}

/*

resource "aws_db_instance" "quotes_generator" {
  identifier             = "quotes-generator"
  instance_class         = "db.t3.micro"
  allocated_storage      = 5
  engine                 = "postgres"
  engine_version         = "15.7"
  db_name                = "quotes_db"
  username               = "postgres"
  password               = var.db_password
  parameter_group_name   = aws_db_parameter_group.quotes_generator.name
  publicly_accessible    = false
  skip_final_snapshot    = true
  vpc_security_group_ids = [aws_security_group.rds_ec2_1.id] 
  db_subnet_group_name   = aws_db_subnet_group.quotes_subnet_group.name
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
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.quotes_gateway.id
  }
}

resource "aws_route_table_association" "quotes_2" {
  subnet_id      = aws_subnet.quotes_2.id
  route_table_id = aws_route_table.quotes_route_table.id
}

resource "aws_route_table_association" "quotes_3" {
  subnet_id      = aws_subnet.quotes_3.id
  route_table_id = aws_route_table.quotes_route_table.id
}

resource "aws_subnet" "quotes_1" {
  cidr_block        = "172.31.0.0/20"
  vpc_id            = aws_vpc.quotes_main.id
  availability_zone = "us-east-2a"
}

resource "aws_subnet" "quotes_2" {
  cidr_block              = "172.31.16.0/20"
  vpc_id                  = aws_vpc.quotes_main.id
  availability_zone       = "us-east-2b"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "quotes_3" {
  cidr_block              = "172.31.32.0/20"
  vpc_id                  = aws_vpc.quotes_main.id
  availability_zone       = "us-east-2c"
  map_public_ip_on_launch = true
}

resource "aws_db_subnet_group" "quotes_subnet_group" {
  name = "quotes_subnet_group"
  subnet_ids = [aws_subnet.quotes_1.id, aws_subnet.quotes_2.id, aws_subnet.quotes_3.id]
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
    rule_no    = 100
    action     = "deny"
    cidr_block = "0.0.0.0/0"    
    from_port  = 0
    to_port    = 0
  }

  ingress {
    protocol   = "-1"
    rule_no    = 1
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "deny"
    cidr_block = "0.0.0.0/0"    
    from_port  = 0
    to_port    = 0
  }

  egress {
    protocol   = "-1"
    rule_no    = 1
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

resource "aws_security_group" "primary" {
  name        = "primary"
  vpc_id      = aws_vpc.quotes_main.id
}

resource "aws_security_group_rule" "allow_ssh_access" {
  security_group_id = aws_security_group.primary.id
  description       = "Rule to allow SSH connections from internet to reach EC2"
  cidr_blocks       = ["0.0.0.0/0"]
  from_port         = 22
  protocol          = "tcp"
  to_port           = 22
  type              = "ingress"
}

resource "aws_security_group_rule" "allow_ssh_egress" {
  security_group_id = aws_security_group.primary.id
  description       = "Rule to allow SSH connections from EC2 to reach internet"
  cidr_blocks       = ["0.0.0.0/0"]
  from_port         = 22
  protocol          = "tcp"
  to_port           = 22
  type              = "egress"
}

resource "aws_security_group_rule" "allow_http_egress" {
  security_group_id = aws_security_group.primary.id
  description       = "Rule to allow HTTP connections from EC2 to reach internet"
  cidr_blocks       = ["0.0.0.0/0"]
  from_port         = 80
  protocol          = "tcp"
  to_port           = 80
  type              = "egress"
}

resource "aws_security_group_rule" "allow_http_egress_port_8000" {
  security_group_id = aws_security_group.primary.id
  description       = "Rule to allow HTTP connections from EC2 to reach internet"
  cidr_blocks       = ["0.0.0.0/0"]
  from_port         = 8000
  protocol          = "tcp"
  to_port           = 8000
  type              = "egress"
}

resource "aws_security_group_rule" "allow_https_egress" {
  security_group_id = aws_security_group.primary.id
  description       = "Rule to allow HTTP connections from EC2 to reach internet"
  cidr_blocks       = ["0.0.0.0/0"]
  from_port         = 443
  protocol          = "tcp"
  to_port           = 443
  type              = "egress"
}

# an ingress rule to allow my personal IP to access this for development
# can be removed/changed once I open it up to more people
resource "aws_vpc_security_group_ingress_rule" "allow_internet_access" {
  security_group_id = aws_security_group.primary.id
  description       = "Rule to allow connections from internet to reach EC2"
  cidr_ipv4         = "98.45.195.5/32"
  from_port         = 80
  ip_protocol       = "tcp"
  to_port           = 80
}

# an ingress rule to allow my personal IP to access this for development
# can be removed/changed once I open it up to more people
resource "aws_vpc_security_group_ingress_rule" "allow_internet_access_port_8000" {
  security_group_id = aws_security_group.primary.id
  description       = "Rule to allow connections from internet to reach EC2"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 8000
  ip_protocol       = "tcp"
  to_port           = 8000
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

resource "aws_iam_group_policy" "admin_access_policy" {
  name  = "admin_access_policy"
  group = aws_iam_group.admin_group_test.name

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  policy = jsonencode({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "*"
            }
        ]
    })
}

resource "aws_iam_group_policy" "admin_iam_user_change_password_policy" {
  name  = "admin_iam_user_change_password_policy"
  group = aws_iam_group.admin_group_test.name

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  policy = jsonencode({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "iam:ChangePassword"
                ],
                "Resource": [
                    "arn:aws:iam::*:user/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iam:GetAccountPasswordPolicy"
                ],
                "Resource": "*"
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
    ami                     = data.aws_ami.ubuntu.id
    instance_type           = "t2.micro"
    key_name                = aws_key_pair.apiuser.key_name
    vpc_security_group_ids  = [aws_security_group.ec2_rds_1.id, aws_security_group.primary.id]
    subnet_id               = aws_subnet.quotes_2.id

    user_data = <<-EOL
    #!/bin/bash -xe

    echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICjJ7onCRh/3ruUpmlviryTyyYWJHWwm7cmIIJMIw8xv robert.i.sandor@gmail.com" >> ~/.ssh/authorized_keys
    echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICjJ7onCRh/3ruUpmlviryTyyYWJHWwm7cmIIJMIw8xv apiuser" >> ~/.ssh/authorized_keys

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

resource "aws_route53_zone" "primary" {
  name = "quotes-generator.net"
}

resource "aws_route53_record" "www" {
  zone_id = aws_route53_zone.primary.zone_id
  name    = "quotes-generator.net"
  type    = "A"
  ttl     = 300
  records = [aws_instance.web.public_ip] # 3.140.238.209
}

resource "aws_route53_record" "nameserver" {
  zone_id = aws_route53_zone.primary.zone_id
  name    = "quotes-generator.net"
  type    = "NS"
  ttl     = 172800
  records = [
    "ns-557.awsdns-05.net.", 
    "ns-419.awsdns-52.com.", 
    "ns-1492.awsdns-58.org.", 
    "ns-1915.awsdns-47.co.uk."
  ]
}

resource "aws_route53_record" "start_of_authority" {
  zone_id = aws_route53_zone.primary.zone_id
  name    = "quotes-generator.net"
  type    = "SOA"
  ttl     = 900
  records = ["ns-557.awsdns-05.net. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400"]
}
*/