# S3 Bucket for resume and code file storage
resource "aws_s3_bucket" "submissions" {
  bucket        = "${var.project_name}-submissions-${data.aws_caller_identity.current.account_id}"
  force_destroy = true

  tags = {
    Project = var.project_name
  }
}

resource "aws_s3_bucket_versioning" "submissions" {
  bucket = aws_s3_bucket.submissions.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "submissions" {
  bucket = aws_s3_bucket.submissions.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# DynamoDB Table for submission state and fan-in coordination
resource "aws_dynamodb_table" "submissions" {
  name         = "${var.project_name}-submissions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "submission_id"

  attribute {
    name = "submission_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Project = var.project_name
  }
}

# Data source to get current AWS account ID
data "aws_caller_identity" "current" {}

# DynamoDB Table for recruiter-configurable job configurations
resource "aws_dynamodb_table" "job_configs" {
  name         = "${var.project_name}-job-configs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "job_id"

  attribute {
    name = "job_id"
    type = "S"
  }

  tags = {
    Project = var.project_name
  }
}
