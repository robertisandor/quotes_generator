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

resource "aws_iam_user" "dummy_admin_user" {
  name = "dummy_admin_test"
}
