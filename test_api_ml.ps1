# PowerShell API Testing Script for ML Model Integration
# 
# This script tests the ML model through the API endpoints
# Make sure Docker services are running before executing

Write-Host "🚀 Testing ML Model Integration via API" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

$BaseUrl = "http://localhost:8000"
$UserId = 1

Write-Host "📡 Testing API connectivity..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$BaseUrl/health" -TimeoutSec 5
    Write-Host "✅ API is accessible" -ForegroundColor Green
} catch {
    Write-Host "❌ Cannot connect to API. Start Docker services:" -ForegroundColor Red
    Write-Host "   cd infra; docker-compose up -d" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🧪 Test 1: Trigger Credit Evaluation" -ForegroundColor Cyan
Write-Host "POST $BaseUrl/credit/evaluate/$UserId" -ForegroundColor Gray
Write-Host "---"

try {
    $evalResponse = Invoke-RestMethod -Uri "$BaseUrl/credit/evaluate/$UserId" -Method POST
    Write-Host "Response: $(ConvertTo-Json $evalResponse -Depth 3)" -ForegroundColor White
    
    $taskId = $evalResponse.task_id
    if (-not $taskId) {
        Write-Host "❌ No task_id received" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Task ID: $taskId" -ForegroundColor Green
} catch {
    Write-Host "❌ Credit evaluation failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "⏳ Waiting 3 seconds for task to complete..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "🧪 Test 2: Check Task Status" -ForegroundColor Cyan
Write-Host "GET $BaseUrl/credit/status/$taskId" -ForegroundColor Gray
Write-Host "---"

try {
    $statusResponse = Invoke-RestMethod -Uri "$BaseUrl/credit/status/$taskId" -Method GET
    Write-Host "Response: $(ConvertTo-Json $statusResponse -Depth 5)" -ForegroundColor White
    
    if ($statusResponse.status -eq "success") {
        Write-Host "✅ Task completed successfully!" -ForegroundColor Green
        
        $creditEval = $statusResponse.result.credit_evaluation
        if ($creditEval) {
            Write-Host "🎯 ML Model Results:" -ForegroundColor Magenta
            Write-Host "  Risk Score: $($creditEval.risk_score)" -ForegroundColor White
            Write-Host "  Approved: $($creditEval.approved)" -ForegroundColor White
            Write-Host "  New Credit Limit: $($creditEval.new_credit_limit)" -ForegroundColor White
            Write-Host "  Interest Rate: $($creditEval.interest_rate)" -ForegroundColor White
        }
    } else {
        Write-Host "⚠️ Task status: $($statusResponse.status)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Status check failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "🧪 Test 3: Multiple Evaluations (check randomness)" -ForegroundColor Cyan
Write-Host "---"

$riskScores = @()
for ($i = 1; $i -le 3; $i++) {
    Write-Host "Evaluation $($i):" -ForegroundColor Yellow
    try {
        $taskResponse = Invoke-RestMethod -Uri "$BaseUrl/credit/evaluate/$UserId" -Method POST
        $newTaskId = $taskResponse.task_id
        Start-Sleep -Seconds 2
        $status = Invoke-RestMethod -Uri "$BaseUrl/credit/status/$newTaskId" -Method GET
        
        if ($status.status -eq "success" -and $status.result.credit_evaluation) {
            $riskScore = $status.result.credit_evaluation.risk_score
            $riskScores += $riskScore
            Write-Host "  Risk Score: $riskScore" -ForegroundColor White
        } else {
            Write-Host "  Status: $($status.status)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  Failed: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🎯 ML Model Integration Indicators:" -ForegroundColor Magenta
Write-Host "  ✅ Different risk scores = ML randomness working" -ForegroundColor Green
Write-Host "  ✅ Scores between 0.0-1.0 = Valid range" -ForegroundColor Green
Write-Host "  ✅ Features_used object = ML features processed" -ForegroundColor Green

if ($riskScores.Count -gt 1) {
    $uniqueScores = $riskScores | Sort-Object -Unique
if ($uniqueScores.Count -gt 1) {
        Write-Host "✅ Randomness confirmed: $($uniqueScores.Count) unique scores" -ForegroundColor Green
    } else {
        Write-Host "⚠️ All scores identical - check randomness" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✅ ML Model API testing completed!" -ForegroundColor Green
