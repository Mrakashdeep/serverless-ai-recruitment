# Dashboard 1: Performance
resource "aws_cloudwatch_dashboard" "performance" {
  dashboard_name = "${var.project_name}-performance"
  dashboard_body = <<JSON
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Duration", "FunctionName", "serverless-recruitment-resume-eval"],
          ["AWS/Lambda", "Duration", "FunctionName", "serverless-recruitment-code-eval"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "ap-south-1",
        "title": "Lambda Duration (ms)",
        "yAxis": {"left": {"min": 0}}
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", "FunctionName", "serverless-recruitment-resume-eval"],
          ["AWS/Lambda", "Invocations", "FunctionName", "serverless-recruitment-code-eval"]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "ap-south-1",
        "title": "Lambda Invocations"
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Errors"]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "ap-south-1",
        "title": "Lambda Errors"
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/SQS", "NumberOfMessagesSent", "QueueName", "serverless-recruitment-resume"]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "ap-south-1",
        "title": "SQS Messages"
      }
    }
  ]
}
JSON
}

# Dashboard 2: Business
resource "aws_cloudwatch_dashboard" "business" {
  dashboard_name = "${var.project_name}-business"
  dashboard_body = <<JSON
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 24,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "serverless-recruitment-submissions"]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "ap-south-1",
        "title": "DynamoDB Reads"
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/ApiGateway", "Count", "ApiName", "serverless-recruitment-api"]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "ap-south-1",
        "title": "API Requests"
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", "serverless-recruitment-resume-dlq"]
        ],
        "period": 300,
        "stat": "Maximum",
        "region": "ap-south-1",
        "title": "DLQ Messages"
      }
    }
  ]
}
JSON
}

# Alarms
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${var.project_name}-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "Lambda errors > 10 in 10min"
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "dlq_not_empty" {
  alarm_name          = "${var.project_name}-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Average"
  threshold           = "0"
  alarm_description   = "Messages in DLQ"
  
  dimensions = {
    QueueName = aws_sqs_queue.resume_dlq.name
  }
}

resource "aws_cloudwatch_metric_alarm" "high_latency" {
  alarm_name          = "${var.project_name}-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "60000"
  alarm_description   = "Lambda > 60s"
  
  dimensions = {
    FunctionName = aws_lambda_function.resume_eval.function_name
  }
}

resource "aws_cloudwatch_log_group" "email_notifier" {
  name              = "/aws/lambda/${aws_lambda_function.email_notifier.function_name}"
  retention_in_days = 7
  tags = {Project = var.project_name}
}

resource "aws_cloudwatch_query_definition" "correlation_trace" {
  name = "${var.project_name}-correlation-trace"
  log_group_names = [
    "/aws/lambda/${aws_lambda_function.ingress.function_name}",
    "/aws/lambda/${aws_lambda_function.resume_eval.function_name}",
    "/aws/lambda/${aws_lambda_function.code_eval.function_name}"
  ]
  query_string = <<-QUERY
    fields @timestamp, function_name, correlation_id, message
    | filter correlation_id = '<INSERT_SUBMISSION_ID>'
    | sort @timestamp asc
  QUERY
}

resource "aws_cloudwatch_query_definition" "error_analysis" {
  name = "${var.project_name}-errors"
  log_group_names = [
    "/aws/lambda/${aws_lambda_function.resume_eval.function_name}",
    "/aws/lambda/${aws_lambda_function.code_eval.function_name}"
  ]
  query_string = <<-QUERY
    fields @timestamp, level, message
    | filter level = 'ERROR'
    | stats count() by bin(5m)
  QUERY
}
