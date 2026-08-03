# AI Healthcare System — Production Multi-Region Terraform Infrastructure
# Provisioning: AWS EKS Kubernetes Cluster, RDS PostgreSQL (HIPAA Encryption), Redis ElastiCache, S3 Data Lake

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "environment" {
  type    = string
  default = "production"
}

# 1. VPC Infrastructure
resource "aws_vpc" "healthcare_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "ai-healthcare-vpc-${var.environment}"
    Compliance  = "HIPAA-FDA-21CFR11"
    Environment = var.environment
  }
}

# 2. AWS EKS Kubernetes Cluster for Microservices & Agent Swarms
resource "aws_eks_cluster" "healthcare_eks" {
  name     = "ai-healthcare-cluster-${var.environment}"
  role_arn = var.eks_role_arn

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  tags = {
    Environment = var.environment
    Compliance  = "HIPAA"
  }
}

# 3. RDS PostgreSQL Instance (Encrypted at rest with KMS for PHI data)
resource "aws_db_instance" "healthcare_db" {
  allocated_storage     = 100
  max_allocated_storage = 1000
  engine                = "postgres"
  engine_version        = "15.4"
  instance_class        = "db.r6g.xlarge"
  db_name               = "healthcaredb"
  username              = "dbadmin"
  password              = var.db_password
  storage_encrypted     = true
  kms_key_id            = var.kms_key_arn
  skip_final_snapshot   = false

  tags = {
    Name       = "ai-healthcare-db-${var.environment}"
    Compliance = "HIPAA-KMS-Encrypted"
  }
}

# 4. S3 Data Lake Bucket for Open Table ACID Snapshots
resource "aws_s3_bucket" "datalake_bucket" {
  bucket = "ai-healthcare-datalake-${var.environment}"

  tags = {
    Name       = "Healthcare-S3-Data-Lake"
    Compliance = "HIPAA-S3-AES256"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "datalake_encrypt" {
  bucket = aws_s3_bucket.datalake_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
