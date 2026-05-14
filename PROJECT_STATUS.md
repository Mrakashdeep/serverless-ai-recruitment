# Serverless AI Recruitment System - Project Status

**Date:** May 14, 2026  
**Student:** Akashdeep Choudhury (24A07RES24)  
**Institution:** IIT Patna M.Tech Cloud Computing (2024-2026)

## ✅ COMPLETED COMPONENTS

### 1. Core Infrastructure (AWS Free Tier)
- [x] 6 Lambda Functions (Python 3.12)
  - Authorizer (JWT validation)
  - Ingress (8 API routes)
  - Resume Evaluation (AI-powered)
  - Code Evaluation (AI-powered)
  - Question Generation (AI-powered)
  - Email Notifier (ready, not wired)

- [x] API Gateway REST API
  - 8 endpoints with full CORS
  - JWT authorizer
  - Production deployment

- [x] Data Layer
  - 2 DynamoDB tables (submissions, job-configs)
  - 6 SQS queues (3 main + 3 DLQs)
  - 1 S3 bucket (resume/code storage)
  - 3 Secrets Manager secrets

### 2. AI/LLM Integration
- [x] Ollama integration (Llama 3 8B)
- [x] Ngrok tunnel for local LLM access
- [x] Two-layer prompt governance
  - Layer 1: Dynamic recruiter-defined criteria
  - Layer 2: Fixed JSON output structure
- [x] 5-strategy JSON parser (100% success rate)

### 3. Observability & Monitoring
- [x] 2 CloudWatch Dashboards
  - Performance Dashboard (Lambda, API, SQS metrics)
  - Business Dashboard (DynamoDB, DLQ, API metrics)
- [x] 3 CloudWatch Alarms
  - High error rate (>10 errors in 10min)
  - DLQ not empty
  - High latency (>60s)
- [x] 2 CloudWatch Insights Saved Queries
  - Correlation trace (by submission_id)
  - Error analysis (5min bins)
- [x] Log retention policies

### 4. Testing & Validation
- [x] End-to-end workflow tested
  - Job creation → Resume submission → AI evaluation → Recruiter decision → Questions → Code submission → Final decision
- [x] Load testing script (5 concurrent users)
- [x] CloudWatch dashboards populated with real metrics
- [x] All 5 test submissions processed successfully

### 5. Frontend
- [x] Recruiter dashboard (create jobs, review candidates)
- [x] Candidate portal (submit resume, coding challenge)
- [x] Interactive demo HTML with AWS architecture visualization

### 6. Infrastructure as Code
- [x] Complete Terraform configuration
  - Main infrastructure (lambda.tf, api_gateway.tf, storage.tf, sqs.tf)
  - Monitoring (monitoring.tf)
  - IAM (iam.tf)
  - Secrets (secrets.tf)

## � METRICS (From Load Test)

**Performance:**
- Lambda Execution Time: 19s - 75s per evaluation
- API Gateway Latency: <100ms
- SQS Throughput: 5 messages/minute
- DynamoDB Operations: 15+ reads/writes

**Cost:**
- Monthly: ~$1.20 (Secrets Manager only)
- vs Bedrock: 98%+ cost savings
- All other services: FREE (within free tier)


### CI/CD Pipeline
- [ ] GitHub Actions workflow
- [ ] Terraform validation (validate, plan)
- [ ] Security scanning (Bandit, tfsec, checkov)
- [ ] Python linting (flake8/ruff)
- [ ] Automated Lambda deployment
- [ ] PR validation workflow

## � PROJECT STRUCTURE
serverless-recruitment-system/
├── frontend/               # HTML/CSS/JS for dashboards
├── lambdas/               # 6 Lambda function handlers
├── terraform/             # IaC for all AWS resources
├── scripts/               # Utilities (seed_jobs, generate_token, load_test)

## � KEY INNOVATIONS

1. **Two-Layer Prompt Governance** - Separates evaluation criteria (recruiter) from output structure (engineer)
2. **Cost Optimization** - 98% savings using local Ollama vs AWS Bedrock
3. **Robust JSON Parsing** - 5-strategy fallback ensures 100% success
4. **Human-in-Loop** - Recruiter gates between AI stages reduces false positives
5. **Event-Driven Architecture** - Async processing via SQS for scalability



