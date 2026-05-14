#!/bin/bash
echo "=== AWS Resource Audit for ap-south-1 ==="
echo ""

echo "Lambda Functions:"
aws lambda list-functions --region ap-south-1 --query 'Functions[*].[FunctionName,Runtime,LastModified]' --output table

echo ""
echo "API Gateways:"
aws apigateway get-rest-apis --region ap-south-1 --query 'items[*].[name,id,createdDate]' --output table

echo ""
echo "DynamoDB Tables:"
aws dynamodb list-tables --region ap-south-1 --query 'TableNames' --output table

echo ""
echo "S3 Buckets:"
aws s3 ls

echo ""
echo "SQS Queues:"
aws sqs list-queues --region ap-south-1 --query 'QueueUrls' --output table

echo ""
echo "Secrets Manager Secrets:"
aws secretsmanager list-secrets --region ap-south-1 --query 'SecretList[*].[Name,CreatedDate]' --output table

echo ""
echo "IAM Roles (project specific):"
aws iam list-roles --query 'Roles[?contains(RoleName, `serverless-recruitment`) || contains(RoleName, `recruitment`)].[RoleName,CreateDate]' --output table

echo ""
echo "CloudWatch Log Groups:"
aws logs describe-log-groups --region ap-south-1 --query 'logGroups[*].[logGroupName,creationTime]' --output table

echo ""
echo "=== Cost Check ==="
echo "Checking for resources outside free tier..."
echo ""
echo "Secrets Manager (costs after 30 days):"
aws secretsmanager list-secrets --region ap-south-1 --query 'SecretList[*].Name' --output text | wc -w
echo "secrets found (each ~$0.40/month after free tier)"
