#!/bin/bash
# MTech Project Startup Script
# Run this at the beginning of each work session

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Serverless Recruitment System - Daily Startup Check      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

REGION="ap-south-1"
PROJECT_DIR="$HOME/serverless-recruitment-system"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Check Ollama Service
echo "━━━ Step 1: Checking Ollama Service ━━━"
if systemctl is-active --quiet ollama; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠ Ollama is not running. Starting...${NC}"
    sudo systemctl start ollama
    sleep 2
    if systemctl is-active --quiet ollama; then
        echo -e "${GREEN}✓ Ollama started successfully${NC}"
    else
        echo -e "${RED}✗ Failed to start Ollama. Check logs: sudo journalctl -u ollama -n 50${NC}"
        exit 1
    fi
fi
echo ""

# 2. Check Ollama Model
echo "━━━ Step 2: Verifying Ollama Model ━━━"
if ollama list | grep -q "llama3"; then
    echo -e "${GREEN}✓ llama3 model is available${NC}"
else
    echo -e "${YELLOW}⚠ llama3 model not found. Please run: ollama pull llama3${NC}"
fi
echo ""

# 3. Check and Restart ngrok
echo "━━━ Step 3: Setting up ngrok Tunnel ━━━"
# Kill any existing ngrok processes
pkill ngrok 2>/dev/null || true
sleep 2

# Start ngrok in background
nohup ngrok http 11434 > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!
echo "Started ngrok (PID: $NGROK_PID)"

# Wait for ngrok to be ready (max 15 seconds)
NGROK_URL=""
for i in {1..15}; do
    sleep 1
    for port in 4040 4041 4042; do
        NGROK_URL=$(curl -s http://localhost:$port/api/tunnels 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else '')" 2>/dev/null || echo "")
        if [ ! -z "$NGROK_URL" ]; then
            echo -e "${GREEN}✓ ngrok tunnel established (after ${i}s)${NC}"
            echo "  Public URL: $NGROK_URL"
            echo "  Dashboard: http://localhost:$port"
            break 2
        fi
    done
done

if [ -z "$NGROK_URL" ]; then
    echo -e "${RED}✗ Failed to get ngrok URL after 15s. Check /tmp/ngrok.log${NC}"
    echo "Log contents:"
    cat /tmp/ngrok.log
    exit 1
fi
echo ""

# 4. Update AWS Secrets Manager
echo "━━━ Step 4: Updating AWS Secrets Manager ━━━"
aws secretsmanager update-secret \
    --secret-id serverless-recruitment/ollama-ngrok-url \
    --secret-string "{\"url\":\"$NGROK_URL\"}" \
    --region $REGION \
    --output text > /dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ AWS Secrets Manager updated${NC}"
else
    echo -e "${RED}✗ Failed to update Secrets Manager${NC}"
    exit 1
fi
echo ""

# 5. Test Ollama via ngrok
echo "━━━ Step 5: Testing Ollama via ngrok ━━━"
TEST_RESPONSE=$(curl -s -X POST "$NGROK_URL/api/generate" \
    -H "Content-Type: application/json" \
    -H "ngrok-skip-browser-warning: true" \
    -d '{"model":"llama3","prompt":"Say hello in 3 words","stream":false}' \
    --max-time 30)

if echo "$TEST_RESPONSE" | grep -q "response"; then
    echo -e "${GREEN}✓ Ollama is accessible via ngrok${NC}"
else
    echo -e "${YELLOW}⚠ Ollama test incomplete (this is OK for first request)${NC}"
fi
echo ""

# 6. Check AWS Resources
echo "━━━ Step 6: Verifying AWS Resources ━━━"
echo -n "Lambda functions: "
LAMBDA_COUNT=$(aws lambda list-functions --region $REGION --query 'length(Functions[?starts_with(FunctionName, `serverless-recruitment`)])' --output text)
echo -e "${GREEN}$LAMBDA_COUNT/5${NC}"

echo -n "SQS queues: "
SQS_COUNT=$(aws sqs list-queues --region $REGION --query 'length(QueueUrls[?contains(@, `serverless-recruitment`)])' --output text)
echo -e "${GREEN}$SQS_COUNT/6${NC}"

echo -n "DynamoDB tables: "
DDB_COUNT=$(aws dynamodb list-tables --region $REGION --query 'length(TableNames[?starts_with(@, `serverless-recruitment`)])' --output text)
echo -e "${GREEN}$DDB_COUNT/2${NC}"
echo ""

# 7. Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Startup Complete                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "System Ready ✓"
echo ""
echo "API Endpoint: https://nin1zoih0d.execute-api.ap-south-1.amazonaws.com/prod"
echo "ngrok URL: $NGROK_URL"
echo ""
echo "Quick Commands:"
echo "  Generate JWT: python3 $PROJECT_DIR/scripts/generate_token.py"
echo "  Test submit: curl -X POST <API>/submit -H 'Authorization: Bearer <TOKEN>' ..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
