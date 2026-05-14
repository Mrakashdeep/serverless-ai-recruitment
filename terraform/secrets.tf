# JWT Secret for Lambda Authorizer
resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "${var.project_name}/jwt-secret"
  recovery_window_in_days = 0

  tags = {
    Project = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = jsonencode({
    jwt_secret     = var.jwt_secret
    shared_hmac_secret = var.jwt_secret
  })
}

# Ollama ngrok URL secret
resource "aws_secretsmanager_secret" "ollama_url" {
  name                    = "${var.project_name}/ollama-ngrok-url"
  recovery_window_in_days = 0

  tags = {
    Project = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "ollama_url" {
  secret_id     = aws_secretsmanager_secret.ollama_url.id
  secret_string = jsonencode({
    url = var.ollama_ngrok_url
  })
}
