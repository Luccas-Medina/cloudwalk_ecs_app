# CloudWalk Empathic Credit System (ECS)
**Advanced Emotional Intelligence for Credit Assessment**

A comprehensive credit evaluation system that integrates real-time emotional data processing with machine learning to provide empathic, responsible lending decisions.

## 🚀 Features

- **Real-time Emotion Processing**: WebSocket-based emotional data streaming
- **Machine Learning Integration**: ML-powered credit risk assessment with circuit breaker protection
- **Privacy-First Approach**: GDPR/LGPD compliant data handling with comprehensive privacy controls
- **Advanced Analytics**: Real-time emotional insights and trend analysis
- **Responsive Dashboard**: Live emotion monitoring and system health dashboard
- **Credit Deployment**: Automated credit offer generation and management
- **Background Processing**: Celery-based asynchronous task processing

## 📋 System Requirements

### Prerequisites
- **Docker** (with Docker Compose)
- **Python 3.11+**
- **Git**

### Optional (for mobile development)
- **Flutter SDK**
- **Dart SDK**

## 🛠️ Quick Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd cloudwalk_ecs_app
```

### 2. Environment Setup
```bash
# Copy environment template
cp infra/.env.example infra/.env

# Edit environment variables if needed
# The default configuration should work for local development
```

### 3. Start the System
```bash
# Navigate to infrastructure directory
cd infra

# Start all services with Docker Compose
docker-compose up -d

# Verify all services are running
docker-compose ps
```

### 4. Verify Installation
```bash
# Return to project root
cd ..

# Run system verification
python verify_system.py
```

You should see:
```
🎉 ALL SYSTEMS OPERATIONAL - READY FOR PRODUCTION
✅ Repository commit approved
```

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CloudWalk ECS Architecture                  │
├─────────────────────────────────────────────────────────────────┤
│  🌐 API Layer (FastAPI)                                        │
│  ├── Credit Evaluation & Deployment                            │
│  ├── Real-time Emotion Processing (WebSocket)                  │
│  ├── Privacy & Analytics APIs                                  │
│  └── Circuit Breaker Monitoring                                │
├─────────────────────────────────────────────────────────────────┤
│  🧠 Processing Layer                                            │
│  ├── Machine Learning Model (Protected by Circuit Breaker)     │
│  ├── Emotional Analytics Engine                                │
│  ├── Privacy Manager (GDPR Compliance)                         │
│  └── Background Tasks (Celery)                                 │
├─────────────────────────────────────────────────────────────────┤
│  💾 Data Layer                                                 │
│  ├── PostgreSQL (User & Emotion Data)                          │
│  ├── Redis (Caching & Sessions)                                │
│  └── RabbitMQ (Message Queue)                                  │
├─────────────────────────────────────────────────────────────────┤
│  📱 Client Layer                                               │
│  ├── Web Dashboard (React/HTML)                                │
│  ├── Mobile App (Flutter)                                      │
│  └── API Clients                                               │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration

### Environment Variables
The system uses the following key environment variables (configured in `infra/.env`):

```env
# Database Configuration
POSTGRES_DB=ecs_db
POSTGRES_USER=ecs_user
POSTGRES_PASSWORD=ecs_password
DATABASE_URL=postgresql://ecs_user:ecs_password@db:5432/ecs_db

# RabbitMQ Configuration
RABBITMQ_DEFAULT_USER=ecs_user
RABBITMQ_DEFAULT_PASS=ecs_password

# Application Configuration
ENVIRONMENT=development
DEBUG=true
```

### Service Ports
- **Backend API**: http://localhost:8000
- **Web Dashboard**: http://localhost:8000/dashboard
- **Database**: localhost:5432
- **RabbitMQ Management**: http://localhost:15672
- **Redis**: localhost:6379

## 📊 Accessing Emotion Analysis

### 1. **Public Dashboard - Real-time Overview**
```
URL: http://localhost:8000/dashboard
```
- Live emotion metrics display
- Real-time valence/arousal distributions
- Current system emotional state
- Stress level monitoring

### 2. **API Endpoints - Detailed Analytics**

#### Public Emotion Overview
```bash
curl http://localhost:8000/api/v1/dashboard/emotion-overview
```

#### Authenticated Analytics (admin:test)
```bash
# System-wide trends
curl -u admin:test http://localhost:8000/api/v1/analytics/system/trends

# Live metrics
curl -u admin:test http://localhost:8000/api/v1/analytics/live/metrics

# User emotional profile
curl -u admin:test http://localhost:8000/api/v1/analytics/user/999/profile

# Credit-emotion correlations
curl -u admin:test http://localhost:8000/api/v1/analytics/credit/correlations

# Comprehensive export
curl -u admin:test http://localhost:8000/api/v1/analytics/export
```

### 3. **Privacy Management**
```bash
# Privacy compliance metrics
curl -u admin:test http://localhost:8000/api/v1/privacy/metrics

# User consent management
curl -u admin:test http://localhost:8000/api/v1/privacy/consent/999

# GDPR data export
curl -u admin:test http://localhost:8000/api/v1/privacy/export/999
```

### 4. **Interactive Testing**
Generate test emotion data:
```bash
python advanced_emotion_producer.py
```

## 🧪 Testing & Development

### System Verification
```bash
# Comprehensive system test
python verify_system.py

# Check service status
cd infra && docker-compose ps

# View logs
docker-compose logs -f backend
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Generate Test Data
```bash
# Advanced emotion data producer
python advanced_emotion_producer.py

# Select from test scenarios:
# 1. Single user stream
# 2. Multiple users (5 min)
# 3. Emotion scenarios
# 4. Stress test (10 users)
# 5. All scenarios
```

## 🔒 Security & Authentication

### Default Credentials
- **Admin API Access**: `admin:test`
- **Database**: `ecs_user:ecs_password`
- **RabbitMQ**: `ecs_user:ecs_password`

⚠️ **Important**: Change these credentials before production deployment!

### Authentication Levels
- **Public Endpoints**: Dashboard overview, health checks
- **Admin Endpoints**: Analytics, privacy management, monitoring
- **User Endpoints**: Credit evaluation, emotion streaming (with token)

## 📦 Services Overview

### Core Services
- **backend**: FastAPI application server
- **db**: PostgreSQL database
- **redis**: Redis cache and session store
- **rabbitmq**: Message queue for background processing
- **celery**: Background task processor

### Service Health
Check individual service health:
```bash
cd infra

# Backend health
curl http://localhost:8000/

# Database connection
docker-compose exec db psql -U ecs_user -d ecs_db -c "SELECT 1;"

# RabbitMQ management
open http://localhost:15672  # Login: ecs_user:ecs_password
```

## 🎯 Key Use Cases

### 1. **Credit Evaluation**
```bash
# Request credit evaluation
curl -u admin:test -X POST http://localhost:8000/credit/evaluate/999 \
  -H "Content-Type: application/json" \
  -d '{"user_id": 999, "amount": 10000, "purpose": "business_expansion"}'
```

### 2. **Real-time Emotion Streaming**
Connect to WebSocket endpoint:
```
ws://localhost:8000/ws/emotions/stream?user_id=999&session_id=test&token=dev_ingest_token_please_change
```

### 3. **Credit Offer Management**
```bash
# Create credit offer
curl -u admin:test -X POST http://localhost:8000/api/v1/credit/offers \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 999,
    "credit_limit": 25000,
    "interest_rate": 0.035,
    "term_months": 18
  }'
```

## 🔍 Monitoring & Observability

### Circuit Breaker Monitoring
```bash
# Circuit breaker health
curl -u admin:test http://localhost:8000/monitoring/health

# Circuit breaker status
curl -u admin:test http://localhost:8000/monitoring/circuit-breakers
```

### System Metrics
- Real-time processing rates
- Emotional volatility indicators
- Privacy compliance scores
- ML model performance metrics

## 🗂️ Project Structure

```
cloudwalk_ecs_app/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   ├── analytics/         # Emotional analytics engine
│   │   ├── core/              # Core configuration
│   │   ├── ml/                # Machine learning integration
│   │   ├── patterns/          # Circuit breaker patterns
│   │   ├── privacy/           # Privacy management
│   │   └── services/          # Business logic services
├── infra/                     # Infrastructure configuration
│   ├── docker-compose.yml    # Service orchestration
│   ├── .env                   # Environment variables
│   └── Dockerfile.*           # Container definitions
├── mobile/                    # Flutter mobile application
└── docs/                      # Documentation files
```

## 🚀 Production Deployment

### Security Checklist
- [ ] Change default passwords
- [ ] Configure proper SSL certificates
- [ ] Set up secure key management (AWS KMS/Azure Key Vault)
- [ ] Enable production logging and monitoring
- [ ] Configure firewall rules
- [ ] Set up backup procedures

### Environment Configuration
```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<secure-random-key>
DATABASE_URL=<production-database-url>
ALLOWED_HOSTS=<your-domain>
```

## 🔄 Assumptions Made

### 1. **Development Environment**
- Docker and Docker Compose are available
- Local development on localhost
- Default ports (8000, 5432, 6379, 5672, 15672) are available

### 2. **Authentication**
- Basic HTTP auth for admin functions (admin:test)
- Token-based auth for WebSocket connections
- Production-ready OAuth2/JWT integration planned for future

### 3. **Data Privacy**
- GDPR/LGPD compliance framework implemented
- Pseudonymization and differential privacy techniques applied
- User consent defaults to basic emotional processing only

### 4. **Machine Learning**
- ML model is pre-trained and available
- Circuit breaker pattern protects against ML service failures
- Fallback scoring mechanism for high availability

### 5. **Scalability**
- Designed for microservices architecture
- Horizontal scaling through container orchestration
- Background processing handles high-volume operations

## 🆘 Troubleshooting

### Common Issues

#### Backend Not Starting
```bash
# Check logs
cd infra && docker-compose logs backend

# Common fixes
docker-compose down && docker-compose up -d
```

#### Database Connection Issues
```bash
# Verify database is running
docker-compose ps db

# Check database logs
docker-compose logs db
```

#### Permission Errors
```bash
# On Windows, ensure Docker has proper permissions
# On Linux/Mac, check file ownership
sudo chown -R $USER:$USER .
```

### Getting Help
- Check service logs: `docker-compose logs <service-name>`
- Run system verification: `python verify_system.py`
- Review documentation in `/docs` folder

## 📚 Additional Documentation

- **[Privacy & Analytics Implementation](PRIVACY_ANALYTICS_IMPLEMENTATION.md)**: Detailed privacy and analytics features
- **[Circuit Breaker Implementation](CIRCUIT_BREAKER_IMPLEMENTATION.md)**: Resilience patterns documentation
- **[Real-time Emotion Processing](REALTIME_EMOTION_PROCESSING.md)**: Emotion processing system details
- **[Database Schema](DATABASE_SCHEMA.md)**: Database design and queries
- **[Production Ready Report](PRODUCTION_READY_REPORT.md)**: Production deployment guide

---

**🎉 CloudWalk Empathic Credit System - Where Technology Meets Empathy**

*Building responsible financial technology that understands human emotions and promotes financial wellbeing.*
