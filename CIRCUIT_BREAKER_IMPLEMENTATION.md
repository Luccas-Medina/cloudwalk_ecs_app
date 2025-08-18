# Circuit Breaker Pattern Implementation

## 🔧 Overview

The Circuit Breaker pattern has been implemented to protect the CloudWalk Empathic Credit System's ML model service against cascading failures and provide graceful degradation under load.

## 🏗️ Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Circuit Breaker Pattern                     │
├─────────────────────────────────────────────────────────────────┤
│  🎯 Protected ML Model Service                                  │
│  ├── Circuit Breaker Protection                                 │
│  ├── Automatic Failure Detection                                │
│  ├── Intelligent Fallback Mechanisms                            │
│  └── Performance Monitoring                                     │
├─────────────────────────────────────────────────────────────────┤
│  📊 States & Transitions                                        │
│  ├── CLOSED: Normal operation                                   │
│  ├── OPEN: Service failing, blocking requests                   │
│  └── HALF_OPEN: Testing service recovery                        │
├─────────────────────────────────────────────────────────────────┤
│  🔍 Monitoring & Control                                        │
│  ├── Real-time Health Metrics                                   │
│  ├── Performance Analytics                                      │
│  ├── Manual Circuit Control                                     │
│  └── Comprehensive Diagnostics                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Features Implemented

### 1. Circuit Breaker Core (`app/patterns/circuit_breaker.py`)

**Key Features:**
- **Three-State Management**: CLOSED → OPEN → HALF_OPEN → CLOSED
- **Configurable Thresholds**: Failure count, recovery timeout, success threshold
- **Thread-Safe Operations**: Concurrent request handling
- **Comprehensive Metrics**: Success/failure rates, response times, circuit events
- **Decorator Support**: Easy integration with existing functions

**Configuration:**
```python
CircuitBreakerConfig(
    failure_threshold=3,        # Open after 3 failures
    recovery_timeout=30.0,      # Wait 30s before testing recovery
    success_threshold=2,        # Need 2 successes to close
    timeout=5.0,               # 5s timeout for requests
    expected_exception=(MLModelServiceError, TimeoutError, ConnectionError),
    fallback_enabled=True
)
```

### 2. Protected ML Model Service (`app/ml/protected_model.py`)

**Key Features:**
- **Circuit Breaker Integration**: Wraps ML model calls with protection
- **Intelligent Fallback**: Rule-based credit scoring when ML service fails
- **Performance Tracking**: Response times, prediction sources, service health
- **Graceful Degradation**: Maintains service availability during ML failures

**Fallback Algorithm:**
```python
# Rule-based risk assessment when ML service unavailable
def _fallback_risk_score(features):
    risk_score = 0.0
    
    # Financial risk factors
    if transaction_count == 0:
        risk_score += 0.3  # No history is risky
    
    # Emotional risk factors  
    if avg_valence < -0.3 and avg_arousal > 0.7:
        risk_score += 0.2  # High stress indicator
    
    # Emotion-based adjustments
    if last_emotion in ['anger', 'fear', 'sadness']:
        risk_score += 0.15
    
    return max(0.0, min(1.0, risk_score + 0.4))
```

### 3. Enhanced Credit Service (`app/services/credit_service.py`)

**Integration Changes:**
- **Protected ML Calls**: Uses `get_protected_risk_score()` instead of direct ML model
- **Enhanced Logging**: Tracks prediction source and circuit breaker state  
- **Metadata Enrichment**: Returns ML model info including circuit breaker status

**Response Format:**
```json
{
  "approved": true,
  "risk_score": 0.478,
  "new_credit_limit": 196151.03,
  "ml_model_info": {
    "model_version": "v1.0.0",
    "prediction_source": "ml_model",
    "circuit_breaker_state": "closed",
    "response_time": 0.248
  }
}
```

### 4. Monitoring API (`app/api/monitoring.py`)

**Endpoints Available:**
- `GET /monitoring/health` - Overall system health
- `GET /monitoring/circuit-breakers` - All circuit breaker statuses
- `GET /monitoring/circuit-breakers/{name}` - Specific circuit breaker details
- `POST /monitoring/circuit-breakers/{name}/reset` - Manual reset
- `POST /monitoring/circuit-breakers/{name}/open` - Force open for maintenance
- `GET /monitoring/ml-service/health` - ML service detailed health
- `GET /monitoring/ml-service/metrics` - Performance metrics
- `GET /monitoring/diagnostics` - Comprehensive system diagnostics

## 🔄 Circuit Breaker States

### CLOSED State (Normal Operation)
- All requests pass through to ML model
- Failure count tracked and reset on success
- Transitions to OPEN when failure threshold reached

### OPEN State (Service Protection)
- All requests blocked from reaching ML model
- Fallback mechanism automatically activated
- Timer counts down to recovery attempt
- Transitions to HALF_OPEN when recovery timeout expires

### HALF_OPEN State (Recovery Testing)
- Limited requests allowed to test service recovery
- Success count tracked for confidence building
- Transitions to CLOSED after success threshold met
- Returns to OPEN immediately on any failure

## 📊 Monitoring and Metrics

### Health Score Calculation
```python
health_score = 100.0

# Circuit breaker state impact
if circuit_breaker.is_open:
    health_score -= 40
elif circuit_breaker.is_half_open:
    health_score -= 20

# Failure rate impact (0-30% reduction)
health_score -= (failure_rate * 30)

# Fallback usage impact (0-20% reduction)  
health_score -= (fallback_rate * 20)

# Response time impact
if avg_response_time > 2.0:
    health_score -= min(10, (avg_response_time - 2.0) * 5)
```

### Performance Metrics Tracked
- **Total Predictions**: Overall request count
- **ML vs Fallback Ratio**: Service availability indicator
- **Average Response Time**: Performance monitoring
- **Success/Failure Rates**: Reliability tracking
- **Circuit Open Events**: Stability indicator

## 🚀 Usage Examples

### Basic Circuit Breaker Usage
```python
from app.ml.protected_model import get_protected_risk_score

# Protected ML model call with automatic fallback
features = {
    "transaction_count": 15,
    "avg_transaction_amount": 250.0,
    "current_credit_limit": 5000.0,
    "avg_valence": 0.3,
    "avg_arousal": 0.5,
    "last_emotion": "joy"
}

result = get_protected_risk_score(features)
print(f"Risk Score: {result['risk_score']}")
print(f"Source: {result['prediction_source']}")
print(f"Circuit State: {result['circuit_breaker_state']}")
```

### Manual Circuit Control
```python
from app.ml.protected_model import get_protected_ml_service

service = get_protected_ml_service()

# Manual operations
service.reset_circuit_breaker()      # Reset to closed state
service.force_circuit_open()         # Force open for maintenance

# Health monitoring
health = service.get_service_health()
print(f"Health Score: {health['health_score']}")
print(f"Status: {health['status']}")
```

### Decorator Pattern Usage
```python
from app.patterns.circuit_breaker import circuit_breaker, CircuitBreakerConfig

@circuit_breaker(
    name="external_service",
    config=CircuitBreakerConfig(failure_threshold=5),
    fallback_func=my_fallback_function
)
def call_external_service(data):
    # Protected function call
    return external_api.process(data)
```

## 🧪 Testing

### Automated Test Suite
The circuit breaker implementation includes a comprehensive test suite (`test_circuit_breaker.py`):

```bash
# Run circuit breaker tests
python test_circuit_breaker.py
```

**Test Scenarios:**
1. **Normal Operation**: Verify ML model calls work correctly
2. **Failure Simulation**: Test circuit opening on failures
3. **Fallback Mechanism**: Verify fallback activation when circuit is open
4. **Recovery Testing**: Test circuit recovery and closing
5. **Performance Monitoring**: Verify metrics collection
6. **Stress Testing**: Load testing with rapid requests

### Manual Testing via API
```bash
# Check system health
curl -u admin:test http://localhost:8000/monitoring/health

# Force circuit open for testing
curl -u admin:test -X POST http://localhost:8000/monitoring/circuit-breakers/ml_model_service/open

# Test fallback mechanism
curl -u admin:test http://localhost:8000/credit/calculate/1

# Reset circuit breaker
curl -u admin:test -X POST http://localhost:8000/monitoring/circuit-breakers/ml_model_service/reset
```

## 📈 Benefits Achieved

### 1. Resilience
- **Service Protection**: Prevents cascading failures from ML service issues
- **Automatic Recovery**: Self-healing system that tests recovery automatically
- **Graceful Degradation**: Maintains credit evaluation capability during ML downtime

### 2. Observability
- **Real-time Monitoring**: Live circuit breaker state and performance metrics
- **Health Scoring**: Quantitative service health assessment
- **Comprehensive Diagnostics**: Detailed troubleshooting information

### 3. Operational Control
- **Manual Override**: Operators can force circuit states for maintenance
- **Performance Insights**: Detailed metrics for optimization opportunities
- **Proactive Alerting**: Health score degradation indicates potential issues

### 4. Business Continuity
- **High Availability**: Credit services remain available during ML service issues
- **Consistent Experience**: Users receive credit decisions even with backend failures
- **Risk Management**: Fallback algorithm provides conservative risk assessment

## 🔧 Configuration Options

### Circuit Breaker Tuning
```python
# Conservative settings (production)
production_config = CircuitBreakerConfig(
    failure_threshold=3,      # Open quickly on failures
    recovery_timeout=60.0,    # Wait longer before testing recovery  
    success_threshold=3,      # Require more successes to close
    timeout=5.0               # Strict timeout
)

# Aggressive settings (development)
development_config = CircuitBreakerConfig(
    failure_threshold=5,      # Allow more failures
    recovery_timeout=30.0,    # Test recovery sooner
    success_threshold=2,      # Close circuit faster
    timeout=10.0              # More lenient timeout
)
```

### Fallback Behavior
The fallback algorithm can be customized based on business requirements:
- **Conservative**: Higher default risk scores for safety
- **Aggressive**: Lower risk scores to maintain approval rates
- **Adaptive**: Risk scores based on historical patterns

## 🔍 Troubleshooting

### Common Issues

**Circuit Stuck Open:**
```bash
# Check recent failures
curl -u admin:test http://localhost:8000/monitoring/circuit-breakers/ml_model_service

# Manual reset if needed
curl -u admin:test -X POST http://localhost:8000/monitoring/circuit-breakers/ml_model_service/reset
```

**High Fallback Usage:**
```bash
# Check ML service health
curl -u admin:test http://localhost:8000/monitoring/ml-service/health

# Review performance metrics
curl -u admin:test http://localhost:8000/monitoring/ml-service/metrics
```

**Slow Response Times:**
- Check average response times in metrics
- Consider adjusting circuit breaker timeout
- Investigate ML service performance

### Health Score Interpretation
- **90-100**: Excellent - All systems operating normally
- **75-89**: Good - Minor issues, monitoring recommended
- **50-74**: Degraded - Performance issues, investigation needed
- **25-49**: Poor - Significant problems, immediate attention required
- **0-24**: Critical - Service failure, emergency response needed

## 📚 References

- **Circuit Breaker Pattern**: Martin Fowler's Circuit Breaker article
- **Resilience Patterns**: Release It! by Michael Nygard
- **Microservices Patterns**: Chris Richardson's pattern catalog
- **Site Reliability Engineering**: Google SRE practices

This implementation provides enterprise-grade resilience for the CloudWalk ML model service while maintaining business continuity and operational visibility.
