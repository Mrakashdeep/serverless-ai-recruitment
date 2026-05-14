# Deployment Guide

## Prerequisites

1. **GitHub Secrets** (Settings → Secrets and variables → Actions):
   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

2. **AWS IAM User** with permissions:
   - Lambda full access
   - API Gateway full access
   - DynamoDB full access
   - S3 full access
   - SQS full access
   - IAM role creation
   - CloudWatch full access
   - Secrets Manager full access

## Workflows

### 1. CI/CD Pipeline (`ci-cd.yml`)
**Triggers:** Push to main/develop, PRs to main

**Jobs:**
- **python-security**: Bandit, Flake8, Ruff
- **terraform-security**: tfsec, Checkov
- **deploy**: Terraform apply (main branch only)
- **integration-tests**: Post-deployment health checks

### 2. PR Validation (`pr-validation.yml`)
**Triggers:** All PRs

**Checks:**
- Python security & linting
- Terraform format & validate
- PR size check
- Auto-comment on success

### 3. Dependency Scan (`dependency-scan.yml`)
**Triggers:** Weekly (Sunday) + manual

**Actions:**
- Scan Python dependencies for CVEs
- Create GitHub issue if vulnerabilities found

## Deployment Process

### Manual Deployment
```bash
cd terraform
terraform plan
terraform apply
```

### Automated Deployment (via GitHub Actions)
1. Create PR with changes
2. Wait for validation checks ✅
3. Merge to `main`
4. Auto-deploy triggered
5. Integration tests run

## Rollback Strategy

If deployment fails:
```bash
cd terraform
terraform plan -destroy -target=aws_lambda_function.problematic_function
terraform apply
```

Or revert commit and push to `main`.

## Monitoring Post-Deployment

1. Check CloudWatch Dashboards
2. Review CloudWatch Logs
3. Monitor CloudWatch Alarms
4. Check DLQs for failed messages

## Security Best Practices

- ✅ Never commit AWS credentials
- ✅ Use GitHub Secrets for sensitive data
- ✅ Run security scans before merge
- ✅ Review tfsec/Checkov reports
- ✅ Keep dependencies updated

## Troubleshooting

**Terraform Init Fails:**
- Check AWS credentials in secrets
- Verify IAM permissions

**Lambda Deployment Fails:**
- Check Lambda package size (<250MB)
- Verify IAM role exists

**Tests Fail:**
- Check API Gateway URL in outputs
- Verify Ollama/ngrok running
