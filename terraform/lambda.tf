# Zip Lambda packages
data "archive_file" "authorizer" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/authorizer/handler.py"
  output_path = "${path.module}/../lambdas/authorizer/handler.zip"
}

data "archive_file" "ingress" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/ingress/handler.py"
  output_path = "${path.module}/../lambdas/ingress/handler.zip"
}

data "archive_file" "resume_eval" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/resume_eval/handler.py"
  output_path = "${path.module}/../lambdas/resume_eval/handler.zip"
}

data "archive_file" "code_eval" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/code_eval/handler.py"
  output_path = "${path.module}/../lambdas/code_eval/handler.zip"
}

# Lambda Authorizer
resource "aws_lambda_function" "authorizer" {
  filename         = data.archive_file.authorizer.output_path
  function_name    = "${var.project_name}-authorizer"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  source_code_hash = data.archive_file.authorizer.output_base64sha256

  environment {
    variables = {
      JWT_SECRET_ARN = aws_secretsmanager_secret.jwt_secret.arn
    }
  }

  tags = { Project = var.project_name }
}

# Ingress Lambda
resource "aws_lambda_function" "ingress" {
  filename         = data.archive_file.ingress.output_path
  function_name    = "${var.project_name}-ingress"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  source_code_hash = data.archive_file.ingress.output_base64sha256

  environment {
    variables = {
      S3_BUCKET        = aws_s3_bucket.submissions.bucket
      DYNAMODB_TABLE   = aws_dynamodb_table.submissions.name
      RESUME_QUEUE_URL = aws_sqs_queue.resume.url
      CODE_QUEUE_URL   = aws_sqs_queue.code.url
      QUESTION_QUEUE_URL = aws_sqs_queue.question.url
    }
  }

  tags = { Project = var.project_name }
}

# Resume Evaluation Lambda
resource "aws_lambda_function" "resume_eval" {
  filename         = data.archive_file.resume_eval.output_path
  function_name    = "${var.project_name}-resume-eval"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 300
  source_code_hash = data.archive_file.resume_eval.output_base64sha256

  environment {
    variables = {
      S3_BUCKET        = aws_s3_bucket.submissions.bucket
      DYNAMODB_TABLE   = aws_dynamodb_table.submissions.name
      OLLAMA_SECRET_ARN    = aws_secretsmanager_secret.ollama_url.arn
      JOB_CONFIGS_TABLE   = aws_dynamodb_table.job_configs.name
    }
  }

  tags = { Project = var.project_name }
}

# Code Evaluation Lambda
resource "aws_lambda_function" "code_eval" {
  filename         = data.archive_file.code_eval.output_path
  function_name    = "${var.project_name}-code-eval"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 300
  source_code_hash = data.archive_file.code_eval.output_base64sha256

  environment {
    variables = {
      S3_BUCKET         = aws_s3_bucket.submissions.bucket
      DYNAMODB_TABLE    = aws_dynamodb_table.submissions.name
      OLLAMA_SECRET_ARN    = aws_secretsmanager_secret.ollama_url.arn
      JOB_CONFIGS_TABLE   = aws_dynamodb_table.job_configs.name
    }
  }

  tags = { Project = var.project_name }
}

# SQS triggers for evaluation Lambdas
resource "aws_lambda_event_source_mapping" "resume_sqs" {
  event_source_arn = aws_sqs_queue.resume.arn
  function_name    = aws_lambda_function.resume_eval.arn
  batch_size       = 1
}

resource "aws_lambda_event_source_mapping" "code_sqs" {
  event_source_arn = aws_sqs_queue.code.arn
  function_name    = aws_lambda_function.code_eval.arn
  batch_size       = 1
}

# Question Generator Lambda
data "archive_file" "question_gen" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/question_gen/handler.py"
  output_path = "${path.module}/../lambdas/question_gen/handler.zip"
}

resource "aws_lambda_function" "question_gen" {
  filename         = data.archive_file.question_gen.output_path
  function_name    = "${var.project_name}-question-gen"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 300
  source_code_hash = data.archive_file.question_gen.output_base64sha256

  environment {
    variables = {
      S3_BUCKET           = aws_s3_bucket.submissions.bucket
      DYNAMODB_TABLE      = aws_dynamodb_table.submissions.name
      OLLAMA_SECRET_ARN   = aws_secretsmanager_secret.ollama_url.arn
      JOB_CONFIGS_TABLE   = aws_dynamodb_table.job_configs.name
    }
  }

  tags = { Project = var.project_name }
}

resource "aws_lambda_event_source_mapping" "question_sqs" {
  event_source_arn = aws_sqs_queue.question.arn
  function_name    = aws_lambda_function.question_gen.arn
  batch_size       = 1
}

# Email Notifier Lambda
data "archive_file" "email_notifier" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/email_notifier"
  output_path = "${path.module}/.terraform/email_notifier.zip"
}

resource "aws_lambda_function" "email_notifier" {
  filename         = data.archive_file.email_notifier.output_path
  function_name    = "${var.project_name}-email-notifier"
  role            = aws_iam_role.lambda_exec.arn
  handler         = "handler.lambda_handler"
  source_code_hash = data.archive_file.email_notifier.output_base64sha256
  runtime         = "python3.12"
  timeout         = 30

  environment {
    variables = {
      FROM_EMAIL = "noreply@recruitment.system"
    }
  }

  tags = {
    Project = var.project_name
  }
}

# Email Notifier Lambda

