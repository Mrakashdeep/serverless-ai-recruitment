# Serverless AI-Driven Recruitment System with Event-Driven Resume and Code Evaluation

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Terraform](https://img.shields.io/badge/Terraform-1.5+-purple.svg)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-Free%20Tier-orange.svg)](https://aws.amazon.com/free/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-green.svg)](https://github.com/features/actions)

> A production-grade, event-driven serverless recruitment platform that automates candidate evaluation using local Large Language Models (LLMs), while preserving human oversight at critical decision gates. Built entirely on the AWS free tier with 98% cost savings over managed AI services.

---

**Academic Project** — IIT Patna, Executive M.Tech in Cloud Computing (2024–2026)  
**Student:** Akashdeep Choudhury | Roll No: `24A07RES24` | Enrollment: `PRVENO-001147249`

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [System Architecture](#system-architecture)
4. [Technology Stack](#technology-stack)
5. [Key Innovations](#key-innovations)
6. [Project Structure](#project-structure)
7. [AWS Infrastructure](#aws-infrastructure)
8. [API Reference](#api-reference)
9. [AI Evaluation Pipeline](#ai-evaluation-pipeline)
10. [Monitoring & Observability](#monitoring--observability)
11. [CI/CD Pipeline](#cicd-pipeline)
12. [Security](#security)
13. [Getting Started](#getting-started)
14. [Cost Analysis](#cost-analysis)
15. [Load Testing](#load-testing)
16. [Acknowledgements](#acknowledgements)

---

## Project Overview

The Serverless AI-Driven Recruitment System addresses the inefficiency and cost of modern technical hiring pipelines. Traditional screening tools are either rule-based and inflexible, or rely on expensive cloud-hosted LLM services that are cost-prohibitive at scale.

This system introduces a fully serverless, event-driven architecture where:

- Candidates submit resumes and complete AI-generated coding challenges through a web portal
- Every submission is processed asynchronously via SQS-triggered Lambda functions
- AI evaluation is powered by a locally hosted Llama 3 (8B) model via Ollama, connected securely to AWS through an ngrok tunnel
- Recruiters retain full authority at each decision gate — advancing or rejecting candidates before the next AI stage begins
- All infrastructure is defined as code using Terraform, and the entire deployment pipeline is automated via GitHub Actions

The system was designed to demonstrate that a rigorously evaluated, cloud-native distributed system can be built and operated at near-zero cost without sacrificing reliability, security, or observability.

---

## Architecture Diagram

> *(Architecture diagram image to be added here)*

---

## System Architecture

The system follows a staged, event-driven pipeline:

```
Recruiter Dashboard / Candidate Portal
            │
            ▼
    AWS API Gateway (REST)
    8 Endpoints | JWT Auth | CORS
            │
            ▼
    Lambda Authorizer
    JWT HS256 Validation
    AWS Secrets Manager
            │
            ▼
    Ingress Lambda (Router)
    Routes 8 API paths
            │
     ┌──────┴───────┐
     ▼              ▼
   Amazon S3    DynamoDB
  (Resumes,    (Submissions,
   Code files)  Job Configs)
     │
     ▼
 Resume SQS Queue ──────► Resume Eval Lambda ──► Ollama (Llama 3)
                                                        │
                                              DynamoDB Update
                                            (RESUME_EVALUATED)
                                                        │
                                              Recruiter Decision
                                             (ADVANCE or REJECT)
                                                        │
 Question SQS Queue ────► Question Gen Lambda ──► Ollama (Llama 3)
                                                        │
                                              3 Personalised Questions
                                              saved to DynamoDB
                                                        │
                                              Candidate Coding Session
                                                        │
 Code SQS Queue ────────► Code Eval Lambda ──────► Ollama (Llama 3)
                                                        │
                                              Final Decision Engine
                                              (avg_score ≥ 60 AND
                                               code=PASS AND
                                               resume=SHORTLIST)
                                                        │
                                          ┌─────────────┴─────────────┐
                                          ▼                           ▼
                                    SHORTLISTED                  REJECTED
                                          │
                                  DLQs (3 queues)
                                  CloudWatch Alarms
                                  CloudWatch Dashboards
```

### Workflow Stages

| Stage | Actor | Action | AWS Resource |
|-------|-------|--------|-------------|
| 1 | Recruiter | Create job posting with AI evaluation prompts | API Gateway → Ingress Lambda → DynamoDB |
| 2 | Candidate | Submit resume and personal details | API Gateway → Ingress Lambda → S3 + SQS |
| 3 | AI | Evaluate resume against job criteria | Resume Eval Lambda → Ollama LLM |
| 4 | Recruiter | Review AI result and decide to advance or reject | API Gateway → Ingress Lambda → DynamoDB |
| 5 | AI | Generate 3 personalised coding questions | Question Gen Lambda → Ollama LLM |
| 6 | Candidate | Solve coding challenges in 30-minute session | API Gateway → Ingress Lambda → S3 + SQS |
| 7 | AI | Evaluate code and compute final hiring decision | Code Eval Lambda → Ollama LLM → DynamoDB |

---

## Technology Stack

### Cloud Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Compute | AWS Lambda (Python 3.12) | Serverless function execution |
| API Layer | AWS API Gateway (REST) | Endpoint management and JWT auth |
| Database | AWS DynamoDB | State management (submissions, jobs) |
| Queue | AWS SQS | Async event-driven message passing |
| Storage | AWS S3 | Resume and code artefact storage |
| Secrets | AWS Secrets Manager | JWT secret, SMTP credentials, Ollama URL |
| Monitoring | AWS CloudWatch | Dashboards, alarms, insights queries |

### AI / LLM

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM Runtime | Ollama | Local model server |
| Model | Meta-Llama-3-8B | Resume and code evaluation |
| Tunnel | Ngrok | Secure Lambda-to-Ollama connectivity |
| Prompt Design | Two-Layer Governance | Recruiter criteria + enforced JSON output |
| JSON Parsing | 5-Strategy Fallback | 100% LLM output success rate |

### DevOps

| Component | Technology | Purpose |
|-----------|-----------|---------|
| IaC | Terraform 1.5+ | All AWS resources defined as code |
| CI/CD | GitHub Actions | Automated validation and deployment |
| Security Scanning | Bandit, tfsec, Checkov | Static analysis across Python and Terraform |
| Linting | Flake8, Ruff | Code quality enforcement |
| Dependency Scanning | Safety | Weekly CVE scanning |

---

## Key Innovations

### 1. Two-Layer Prompt Governance

A key architectural contribution is the separation of AI evaluation criteria from AI output structure:

- **Layer 1 (Dynamic):** Recruiter-defined evaluation instructions stored in DynamoDB `job-configs`. Non-technical recruiters can describe what to look for in a candidate without any coding knowledge. These instructions change per job role.
- **Layer 2 (Fixed):** Enforced JSON output schema embedded in Lambda code. Regardless of what instructions the recruiter provides, the model is always required to return a structured JSON object `{ "score": 0-100, "verdict": "SHORTLIST"/"REJECT", "summary": "..." }`.

This separation prevents prompt injection from breaking the system, and empowers business stakeholders to control AI behaviour through natural language.

### 2. Robust 5-Strategy JSON Parser

LLMs frequently return malformed or verbose output when strict JSON is expected. The system implements a five-strategy fallback parsing chain:

1. Direct `json.loads()` on the full response
2. Extract the first `{...}` block using regex
3. Strip markdown code fences and retry
4. Search for JSON within the surrounding text
5. Use keyword extraction as a last resort (score/verdict parsing without JSON)

This approach achieves 100% parse success across all tested responses.

### 3. Cost-Optimised AI Inference

By routing Lambda invocations to a locally hosted Ollama instance via an ngrok tunnel, the system avoids the per-token charges of AWS Bedrock (estimated $50–100/month for equivalent workloads). Monthly operational cost is **~$1.20**, attributable solely to AWS Secrets Manager after the 30-day free trial.

### 4. Human-in-the-Loop Decision Gates

Rather than a fully automated pipeline, the system introduces a mandatory recruiter review after the resume evaluation stage. This gate:

- Prevents unsuitable candidates from consuming compute resources during the coding stage
- Keeps the recruiter accountable for shortlisting decisions
- Reduces false positives from AI evaluation

### 5. Event-Driven Async Processing

All heavy computation (resume evaluation, question generation, code evaluation) is decoupled from the API request lifecycle via SQS. The API acknowledges receipt immediately, while Lambda functions process asynchronously in the background. Dead-letter queues capture all failures for analysis.

---

## Project Structure

```
serverless-recruitment-system/
│
├── .github/
│   └── workflows/
│       ├── ci-cd.yml               # Main CI/CD pipeline
│       ├── pr-validation.yml       # Pull request validation
│       └── dependency-scan.yml     # Weekly CVE scanning
│
├── frontend/
│   ├── recruiter.html              # Recruiter dashboard UI
│   └── candidate.html              # Candidate submission portal
│
├── lambdas/
│   ├── authorizer/
│   │   └── handler.py              # JWT HS256 token validation
│   ├── ingress/
│   │   └── handler.py              # API router (8 endpoints)
│   ├── resume_eval/
│   │   └── handler.py              # AI resume evaluation
│   ├── code_eval/
│   │   └── handler.py              # AI code evaluation + final decision
│   ├── question_gen/
│   │   └── handler.py              # AI personalised question generation
│   └── email_notifier/
│       └── handler.py              # SMTP email notification (ready)
│
├── terraform/
│   ├── main.tf                     # Provider and backend config
│   ├── lambda.tf                   # Lambda functions and event source mappings
│   ├── api_gateway.tf              # REST API, resources, methods, integrations
│   ├── storage.tf                  # DynamoDB tables, S3 bucket
│   ├── sqs.tf                      # SQS queues and DLQs
│   ├── iam.tf                      # IAM roles and least-privilege policies
│   ├── secrets.tf                  # Secrets Manager resources
│   ├── monitoring.tf               # CloudWatch dashboards, alarms, queries
│   ├── variables.tf                # Input variables
│   ├── outputs.tf                  # Output values
│   └── terraform.tfvars            # Variable values (not committed)
│
├── scripts/
│   ├── seed_jobs.py                # Create test job configurations
│   ├── generate_token.py           # JWT token generation utility
│   └── load_test.py                # 5-user concurrent load test
│
├── demo.html                       # Interactive architecture walkthrough
├── DEPLOYMENT.md                   # Step-by-step deployment guide
├── PROJECT_STATUS.md               # Implementation progress tracker
├── .gitignore                      # Excludes secrets, state files, caches
└── README.md                       # This file
```

---

## AWS Infrastructure

### Lambda Functions

| Function | Runtime | Timeout | Memory | Trigger |
|----------|---------|---------|--------|---------|
| `authorizer` | Python 3.12 | 30s | 128MB | API Gateway (Custom Auth) |
| `ingress` | Python 3.12 | 30s | 128MB | API Gateway (all routes) |
| `resume_eval` | Python 3.12 | 300s | 128MB | SQS (resume queue) |
| `code_eval` | Python 3.12 | 300s | 128MB | SQS (code queue) |
| `question_gen` | Python 3.12 | 300s | 128MB | SQS (question queue) |
| `email_notifier` | Python 3.12 | 30s | 128MB | Manual / future trigger |

### DynamoDB Tables

| Table | Partition Key | Purpose |
|-------|---------------|---------|
| `serverless-recruitment-submissions` | `submission_id` (String) | Candidate submissions, scores, status |
| `serverless-recruitment-job-configs` | `job_id` (String) | Job definitions and AI evaluation prompts |

### SQS Queues

| Queue | Type | Consumer | Max Receives |
|-------|------|----------|-------------|
| `resume` | Standard | Resume Eval Lambda | 3 |
| `code` | Standard | Code Eval Lambda | 3 |
| `question` | Standard | Question Gen Lambda | 3 |
| `resume-dlq` | Standard | CloudWatch Alarm | — |
| `code-dlq` | Standard | CloudWatch Alarm | — |
| `question-dlq` | Standard | CloudWatch Alarm | — |

### IAM Policies (Least Privilege)

The `lambda-exec` role grants only the minimum permissions required:

- `s3:GetObject`, `s3:PutObject` on the submissions bucket
- `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:UpdateItem`, `dynamodb:Scan` on both tables
- `sqs:SendMessage`, `sqs:ReceiveMessage`, `sqs:DeleteMessage` on all queues
- `secretsmanager:GetSecretValue` on named secrets only
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`

---

## API Reference

All endpoints require a valid JWT Bearer token in the `Authorization` header.

### Authentication

```bash
# Generate token
python3 scripts/generate_token.py

# Use in requests
export JWT_TOKEN=<token>
curl -H "Authorization: Bearer $JWT_TOKEN" ...
```

### Endpoints

#### `POST /jobs` — Create Job Posting

```json
Request Body:
{
  "job_id": "sde-2026-01",
  "job_role": "Senior Python Developer",
  "required_skills": "Python, AWS, FastAPI, Docker",
  "description": "Build scalable serverless systems",
  "custom_instructions": "Look for hands-on cloud experience...",
  "code_instructions": "Code must have proper error handling..."
}

Response: { "message": "Job created successfully" }
```

#### `POST /submit` — Submit Application

```json
Request Body:
{
  "job_id": "sde-2026-01",
  "candidate_name": "Alice Johnson",
  "email": "alice@example.com",
  "resume_content": "5 years Python experience..."
}

Response: { "submission_id": "uuid-here" }
```

#### `GET /results?submission_id=<id>` — Get Evaluation Results

```json
Response:
{
  "submission_id": "uuid",
  "candidate_name": "Alice Johnson",
  "status": "RESUME_EVALUATED",
  "resume_score": 85,
  "resume_verdict": "SHORTLIST",
  "resume_summary": "Strong cloud experience...",
  "code_score": null,
  "final_status": null
}
```

#### `POST /decision` — Recruiter Advance or Reject

```json
Request Body:
{
  "submission_id": "uuid",
  "decision": "ADVANCE"   // or "REJECT"
}
```

#### `GET /questions?submission_id=<id>` — Get Coding Questions

```json
Response:
{
  "questions": [
    {
      "question_id": "q1",
      "title": "Async API Handler",
      "difficulty": "MEDIUM",
      "description": "Build a FastAPI endpoint...",
      "tags": ["Python", "FastAPI"]
    }
  ]
}
```

#### `POST /code-submit` — Submit Code Solution

```json
Request Body:
{
  "submission_id": "uuid",
  "solutions": {
    "q1": "from fastapi import FastAPI...",
    "q2": "def solution():...",
    "q3": "class Node:..."
  }
}
```

#### `GET /report?submission_id=<id>` — Generate Evaluation Report

Returns a full structured report for a completed submission, suitable for recruiter records.

---

## AI Evaluation Pipeline

### Resume Evaluation

The Resume Eval Lambda constructs a two-layer prompt:

```
LAYER 1 (Dynamic — from DynamoDB job-configs):
"Look for hands-on AWS serverless experience, not just theory.
 Prioritize candidates who have led cloud migrations..."

LAYER 2 (Fixed — hardcoded in Lambda):
"Evaluate the following resume and return ONLY valid JSON:
 {
   "score": <0-100>,
   "verdict": "SHORTLIST" or "REJECT",
   "summary": "<brief justification>"
 }
 Resume: <resume_content>"
```

**Typical latency:** 19–45 seconds  
**Output:** Score (0–100), verdict (SHORTLIST/REJECT), summary

### Question Generation

The Question Gen Lambda generates three coding questions personalised to the candidate's resume and the job's required skills. Questions are rated EASY, MEDIUM, and HARD and include sample input/output pairs.

**Typical latency:** 50–60 seconds  
**Output:** Array of 3 structured question objects

### Code Evaluation

The Code Eval Lambda evaluates all three submitted solutions for correctness, code quality, edge case handling, and best practices.

**Final decision logic:**

```python
avg_score = (resume_score + code_score) / 2

final_status = (
    "SHORTLISTED"
    if avg_score >= 60
       and code_verdict == "PASS"
       and resume_verdict == "SHORTLIST"
    else "REJECTED"
)
```

**Typical latency:** 45–75 seconds

---

## Monitoring & Observability

### CloudWatch Dashboards

Two dashboards are deployed via Terraform:

**1. Performance Dashboard** (`serverless-recruitment-performance`)

| Widget | Metrics |
|--------|---------|
| Lambda Duration | `AWS/Lambda Duration` for resume_eval, code_eval |
| Lambda Invocations | `AWS/Lambda Invocations` for resume_eval, code_eval |
| Lambda Errors | `AWS/Lambda Errors` (all functions) |
| SQS Throughput | `NumberOfMessagesSent` for resume queue |

**2. Business Dashboard** (`serverless-recruitment-business`)

| Widget | Metrics |
|--------|---------|
| DynamoDB Reads | `ConsumedReadCapacityUnits` for submissions table |
| API Gateway Traffic | `Count` for API requests |
| DLQ Monitoring | `ApproximateNumberOfMessagesVisible` for resume-dlq |

### CloudWatch Alarms

| Alarm | Condition | Significance |
|-------|-----------|-------------|
| `high-error-rate` | Lambda errors > 10 in 10 minutes | System instability |
| `dlq-messages` | Any message in resume-dlq | Processing failure |
| `high-latency` | Lambda duration avg > 60s over 2 periods | LLM degradation |

### CloudWatch Insights Queries

**Correlation Trace** — trace a single submission across all Lambdas:

```sql
fields @timestamp, function_name, correlation_id, message
| filter correlation_id = '<submission_id>'
| sort @timestamp asc
```

**Error Analysis** — breakdown of errors by 5-minute window:

```sql
fields @timestamp, level, message
| filter level = 'ERROR'
| stats count() by bin(5m)
```

---

## CI/CD Pipeline

Three GitHub Actions workflows enforce code quality, security, and automated deployment.

### Workflow Overview

```
Pull Request opened
        │
        ▼
PR Validation (pr-validation.yml)
  • Bandit security scan
  • Flake8 + Ruff linting
  • Terraform fmt + validate
  • PR size check
  • Auto-comment on success
        │
        ▼
Merge to main
        │
        ▼
CI/CD Pipeline (ci-cd.yml)
  │
  ├── Job 1: python-security
  │     • Bandit (static analysis)
  │     • Flake8 (code quality)
  │     • Ruff (fast linting)
  │     • Upload Bandit JSON report
  │
  ├── Job 2: terraform-security
  │     • terraform fmt -check
  │     • terraform validate
  │     • tfsec (Terraform security)
  │     • Checkov (IaC compliance)
  │     • Upload security reports
  │
  ├── Job 3: deploy (needs jobs 1+2)
  │     • Configure AWS credentials
  │     • terraform init + plan + apply
  │     • Lambda deployment via Terraform
  │     • Output deployment summary
  │
  └── Job 4: integration-tests (needs job 3)
        • API health checks
        • Smoke test key endpoints
```

**Weekly Dependency Scan** (`dependency-scan.yml`)  
Runs every Sunday, scans `requirements.txt` files for CVEs using Safety, and opens a GitHub issue if vulnerabilities are found.

### Required GitHub Secrets

| Secret | Value |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |

### Rollback Strategy

If a deployment introduces a regression:

```bash
# Option 1: Revert commit and push to main (triggers re-deploy)
git revert <bad-commit-sha>
git push origin main

# Option 2: Target-destroy a specific resource
cd terraform
terraform plan -destroy -target=aws_lambda_function.code_eval
terraform apply

# Option 3: Roll back to previous Lambda version manually
aws lambda update-function-code \
  --function-name serverless-recruitment-code-eval \
  --s3-bucket <previous-package-bucket> \
  --s3-key <previous-package-key>
```

---

## Security

### Authentication

- JWT tokens (HS256) with 24-hour expiry issued per recruiter session
- Token signing secret stored in AWS Secrets Manager, fetched at Lambda cold start
- Lambda Authorizer validates every request before routing

### Encryption

- S3 bucket: Server-side encryption (AES-256) enabled
- DynamoDB: Encryption at rest enabled by default
- Secrets Manager: All secrets encrypted with AWS-managed KMS keys
- In-transit: HTTPS enforced on all API Gateway endpoints

### IAM

- Single `lambda-exec` role shared across all functions with least-privilege inline policies
- No wildcard resource permissions (`*`) in any policy
- API Gateway uses a dedicated `apigw-exec` role

### Code Security

- Bandit scans Lambda code for known vulnerability patterns (SQL injection, hardcoded secrets, insecure hashing)
- tfsec and Checkov scan Terraform for misconfigured security groups, public S3 buckets, unencrypted resources

---

## Getting Started

### Prerequisites

- AWS Account (free tier is sufficient)
- Terraform >= 1.5 installed
- Python 3.12 installed
- [Ollama](https://ollama.ai/) installed locally
- [Ngrok](https://ngrok.com/) account and CLI

### Step 1: Clone the Repository

```bash
git clone https://github.com/<your-username>/serverless-recruitment-system.git
cd serverless-recruitment-system
```

### Step 2: Configure AWS Credentials

```bash
aws configure
# Enter: Access Key, Secret Key, Region (ap-south-1), Output format (json)
```

### Step 3: Start Ollama and Ngrok

```bash
# Terminal 1: Start Ollama
ollama serve
ollama pull llama3

# Terminal 2: Start ngrok tunnel
ngrok http 11434

# Copy the ngrok HTTPS URL (e.g. https://abc123.ngrok-free.app)
```

### Step 4: Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### Step 5: Update Ollama URL in Secrets Manager

```bash
aws secretsmanager update-secret \
  --secret-id serverless-recruitment/ollama-ngrok-url \
  --secret-string '{"url":"https://your-ngrok-url.ngrok-free.app"}' \
  --region ap-south-1
```

### Step 6: Seed Test Data

```bash
cd scripts
python3 seed_jobs.py
```

### Step 7: Generate JWT and Test

```bash
# Generate token
python3 generate_token.py

# Run load test (5 concurrent users)
python3 load_test.py
```

### Step 8: View Dashboards

Open the CloudWatch Console and navigate to:

- `serverless-recruitment-performance`
- `serverless-recruitment-business`

---

## Cost Analysis

| AWS Service | Free Tier Limit | Usage | Monthly Cost |
|-------------|----------------|-------|-------------|
| Lambda | 1M invocations, 400,000 GB-seconds | ~500 invocations | **$0.00** |
| API Gateway | 1M REST API calls | ~500 requests | **$0.00** |
| DynamoDB | 25 WCU + 25 RCU + 25GB | < 1 WCU/RCU | **$0.00** |
| SQS | 1M requests | ~1,500 messages | **$0.00** |
| S3 | 5GB storage | < 10MB | **$0.00** |
| CloudWatch | 5GB log ingestion | < 100MB | **$0.00** |
| Secrets Manager | 30-day free trial per secret | 3 secrets | **$1.20**** |
| **Total** | | | **~$1.20/month** |

> *\*After the 30-day free trial, Secrets Manager charges $0.40 per secret per month.*

**Comparison:**

| Approach | Monthly Cost | Notes |
|----------|-------------|-------|
| This system (Ollama) | ~$1.20 | Local LLM via ngrok |
| AWS Bedrock (Claude Haiku) | ~$30–60 | Based on token usage |
| AWS Bedrock (Claude Sonnet) | ~$80–150 | Higher capability |
| OpenAI GPT-4o | ~$50–100 | API-based pricing |

**Cost savings: 97–99% compared to all managed LLM alternatives.**

---

## Load Testing

The included load test script simulates 5 concurrent candidate submissions and measures system throughput.

```bash
cd scripts
python3 load_test.py
```

**Sample Output:**

```
============================================================
SERVERLESS RECRUITMENT - LIGHT LOAD TEST
============================================================
Started: 2026-05-14 17:42:22
Concurrent users: 5
API: https://nin1zoih0d.execute-api.ap-south-1.amazonaws.com/prod
============================================================
✓ Alice Johnson #0: Submitted (ID: 13baa68f...)
✓ Bob Smith #1: Submitted (ID: 8e149b40...)
✓ Carol Martinez #2: Submitted (ID: 30376d3a...)
✓ David Lee #3: Submitted (ID: 1bacc1e6...)
✓ Eve Wilson #4: Submitted (ID: 000a9dbe...)
  → Resume evaluated: SHORTLIST (85/100)
  → Resume evaluated: REJECT (20/100)
  → Resume evaluated: REJECT (40/100)
  → Resume evaluated: REJECT (40/100)
  → Resume evaluated: REJECT (20/100)
============================================================
Duration: 127.2s | Successful: 5/5 | Failed: 0/5
============================================================
```

**Observed Performance Metrics:**

| Metric | Value |
|--------|-------|
| API submission latency | < 500ms |
| Lambda cold start | ~530ms |
| Resume evaluation (p50) | ~35s |
| Resume evaluation (p99) | ~75s |
| SQS message processing delay | < 1s |
| DynamoDB write latency | < 20ms |
| Concurrent Lambda executions | 5 (within free tier) |

---

## Acknowledgements

- **IIT Patna** — for project guidance and academic framework
- **Meta AI** — for the open-source Llama 3 model
- **Ollama** — for the local LLM runtime
- **HashiCorp** — for Terraform
- **Anthropic** — for Claude (AI-assisted development)
- **AWS** — for the free tier infrastructure

---

## Author

**Akashdeep Choudhury**  
Executive M.Tech in Cloud Computing, Batch 2024–2026  
Indian Institute of Technology Patna  
Roll No: `24A07RES24` | Enrollment: `PRVENO-001147249`

---
*Last updated: May 14, 2026*