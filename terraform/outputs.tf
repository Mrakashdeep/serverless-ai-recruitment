output "api_gateway_url" {
  value       = "${aws_api_gateway_stage.prod.invoke_url}"
  description = "Base URL for the API Gateway"
}

output "submit_endpoint" {
  value       = "${aws_api_gateway_stage.prod.invoke_url}/submit"
  description = "POST endpoint for candidate submissions"
}

output "results_endpoint" {
  value       = "${aws_api_gateway_stage.prod.invoke_url}/results"
  description = "GET endpoint for recruiter dashboard"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.submissions.bucket
  description = "S3 bucket for resume and code storage"
}

output "dynamodb_table_name" {
  value       = aws_dynamodb_table.submissions.name
  description = "DynamoDB table for submission state"
}

output "resume_queue_url" {
  value       = aws_sqs_queue.resume.url
  description = "Resume evaluation SQS queue URL"
}

output "code_queue_url" {
  value       = aws_sqs_queue.code.url
  description = "Code evaluation SQS queue URL"
}

output "job_configs_table_name" {
  value       = aws_dynamodb_table.job_configs.name
  description = "DynamoDB table for recruiter job configurations"
}
