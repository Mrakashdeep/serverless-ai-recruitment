variable "aws_region" {
  default = "ap-south-1"
}

variable "project_name" {
  default = "serverless-recruitment"
}

variable "ollama_ngrok_url" {
  description = "ngrok tunnel URL for Ollama LLM inference"
  type        = string
}

variable "jwt_secret" {
  description = "Secret key for JWT HS256 signing"
  type        = string
  sensitive   = true
}
