# Dead Letter Queues
resource "aws_sqs_queue" "resume_dlq" {
  name                      = "${var.project_name}-resume-dlq"
  message_retention_seconds = 1209600  # 14 days

  tags = {
    Project = var.project_name
  }
}

resource "aws_sqs_queue" "code_dlq" {
  name                      = "${var.project_name}-code-dlq"
  message_retention_seconds = 1209600  # 14 days

  tags = {
    Project = var.project_name
  }
}

# Resume Evaluation Queue
resource "aws_sqs_queue" "resume" {
  name                       = "${var.project_name}-resume"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 86400  # 1 day

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.resume_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Project = var.project_name
  }
}

# Code Evaluation Queue
resource "aws_sqs_queue" "code" {
  name                       = "${var.project_name}-code"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 86400  # 1 day

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.code_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Project = var.project_name
  }
}

# Question Generation Queue
resource "aws_sqs_queue" "question_dlq" {
  name                      = "${var.project_name}-question-dlq"
  message_retention_seconds = 1209600

  tags = { Project = var.project_name }
}

resource "aws_sqs_queue" "question" {
  name                       = "${var.project_name}-question"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 86400

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.question_dlq.arn
    maxReceiveCount     = 3
  })

  tags = { Project = var.project_name }
}
