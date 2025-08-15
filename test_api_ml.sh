#!/bin/bash
# API Testing Script for ML Model Integration
# 
# This script tests the ML model through the API endpoints
# Make sure Docker services are running before executing

echo "🚀 Testing ML Model Integration via API"
echo "======================================"

BASE_URL="http://localhost:8000"
USER_ID=1

echo "📡 Testing API connectivity..."
curl -s -o /dev/null -w "Status: %{http_code}\n" "$BASE_URL/health" || {
    echo "❌ Cannot connect to API. Start Docker services:"
    echo "   cd infra && docker-compose up -d"
    exit 1
}

echo "✅ API is accessible"
echo ""

echo "🧪 Test 1: Trigger Credit Evaluation"
echo "POST $BASE_URL/credit/evaluate/$USER_ID"
echo "---"

RESPONSE=$(curl -s -X POST "$BASE_URL/credit/evaluate/$USER_ID")
echo "Response: $RESPONSE"

# Extract task ID
TASK_ID=$(echo "$RESPONSE" | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TASK_ID" ]; then
    echo "❌ No task_id received"
    exit 1
fi

echo "✅ Task ID: $TASK_ID"
echo ""

echo "⏳ Waiting 3 seconds for task to complete..."
sleep 3

echo "🧪 Test 2: Check Task Status"
echo "GET $BASE_URL/credit/status/$TASK_ID"
echo "---"

STATUS_RESPONSE=$(curl -s "$BASE_URL/credit/status/$TASK_ID")
echo "Response: $STATUS_RESPONSE" | jq . 2>/dev/null || echo "Response: $STATUS_RESPONSE"

echo ""
echo "🎯 Look for these indicators of successful ML integration:"
echo "  ✅ 'status': 'success'"
echo "  ✅ 'credit_evaluation' object with risk_score"
echo "  ✅ 'features_used' showing the 6 ML features"
echo "  ✅ risk_score between 0.0 and 1.0"

echo ""
echo "🧪 Test 3: Multiple Evaluations (check randomness)"
echo "---"

for i in {1..3}; do
    echo "Evaluation $i:"
    TASK_RESPONSE=$(curl -s -X POST "$BASE_URL/credit/evaluate/$USER_ID")
    TASK_ID=$(echo "$TASK_RESPONSE" | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)
    sleep 2
    STATUS=$(curl -s "$BASE_URL/credit/status/$TASK_ID")
    RISK_SCORE=$(echo "$STATUS" | grep -o '"risk_score":[0-9.]*' | cut -d':' -f2)
    echo "  Risk Score: $RISK_SCORE"
done

echo ""
echo "✅ ML Model API testing completed!"
echo "If you see different risk scores above, the ML model randomness is working correctly."
