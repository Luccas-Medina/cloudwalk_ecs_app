# CloudWalk Empathic Credit System - Database Schema Documentation

## Overview

This document describes the complete relational database schema for the CloudWalk Empathic Credit System, designed to store user profiles, transaction history, emotional data, and credit evaluations.

## Database Design Principles

- **PostgreSQL** as the primary relational database
- **Proper normalization** to reduce data redundancy
- **Strategic indexing** for efficient query performance
- **Foreign key constraints** for data integrity
- **Timezone-aware timestamps** for global operations
- **JSONB fields** for flexible data storage

## Schema Tables

### 1. Users Table

**Purpose**: Store comprehensive user profiles and current credit information.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Credit Information
    credit_limit FLOAT DEFAULT 0.0 NOT NULL,
    credit_type VARCHAR(50) DEFAULT 'Short-Term' NOT NULL,
    last_credit_evaluation TIMESTAMP WITH TIME ZONE,
    credit_score FLOAT,
    
    -- Account Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    risk_category VARCHAR(20) DEFAULT 'Medium' NOT NULL
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_credit_limit ON users(credit_limit);
CREATE INDEX idx_users_risk_category ON users(risk_category);
CREATE INDEX idx_users_last_evaluation ON users(last_credit_evaluation);
```

**Key Features**:
- Unique email constraint for user identification
- Credit information stored directly for quick access
- Risk categorization for business analytics
- Audit timestamps for user lifecycle tracking

### 2. Transactions Table

**Purpose**: Store complete financial transaction history for credit analysis.

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount FLOAT NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    description TEXT,
    merchant_category VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Strategic Indexes for Performance
CREATE INDEX idx_user_transaction_date ON transactions(user_id, timestamp);
CREATE INDEX idx_transaction_amount_date ON transactions(amount, timestamp);
CREATE INDEX idx_user_transaction_type ON transactions(user_id, transaction_type);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
```

**Key Features**:
- Composite indexes for efficient user-specific queries
- Transaction type categorization (credit, debit, transfer)
- Merchant category for spending pattern analysis
- Optimized for time-series financial analysis

### 3. Emotional Events Table

**Purpose**: Store real-time emotional data from multiple sources for empathic credit decisions.

```sql
CREATE TABLE emotional_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    source VARCHAR(50),
    
    -- Emotional Analysis
    emotion_label VARCHAR(50),
    valence FLOAT,  -- [-1..1] negative to positive
    arousal FLOAT,  -- [0..1] low to high intensity
    confidence FLOAT,  -- [0..1] model confidence
    
    context TEXT,
    raw_payload JSONB,
    
    -- Timestamps
    timestamp TIMESTAMP WITH TIME ZONE,  -- Original event time
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Time-series Optimized Indexes
CREATE INDEX idx_user_emotion_time ON emotional_events(user_id, ingested_at);
CREATE INDEX idx_user_emotion_label ON emotional_events(user_id, emotion_label);
CREATE INDEX idx_emotion_valence_arousal ON emotional_events(valence, arousal);
CREATE INDEX idx_user_session ON emotional_events(user_id, session_id);
CREATE INDEX idx_emotion_source_time ON emotional_events(source, ingested_at);
CREATE INDEX idx_emotional_events_ingested_at ON emotional_events(ingested_at);
```

**Key Features**:
- Multi-source emotional data ingestion
- Valence-Arousal model for emotional positioning
- Session tracking for contextual analysis
- Time-series optimization for real-time processing

### 4. Credit Evaluations Table

**Purpose**: Historical tracking of ML model results and credit decisions.

```sql
CREATE TABLE credit_evaluations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- ML Model Results
    risk_score FLOAT NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    features_used JSONB NOT NULL,
    
    -- Credit Decision
    approved BOOLEAN NOT NULL,
    credit_limit_offered FLOAT,
    interest_rate FLOAT,
    credit_type VARCHAR(50),
    
    -- Decision Context
    evaluation_reason VARCHAR(255),
    decision_factors JSONB,
    
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Analytics Optimized Indexes
CREATE INDEX idx_user_evaluation_time ON credit_evaluations(user_id, evaluated_at);
CREATE INDEX idx_risk_score_time ON credit_evaluations(risk_score, evaluated_at);
CREATE INDEX idx_approval_time ON credit_evaluations(approved, evaluated_at);
CREATE INDEX idx_model_version ON credit_evaluations(model_version);
```

**Key Features**:
- Complete ML model result tracking
- Decision audit trail for compliance
- Feature storage for model debugging
- Time-series analysis of risk score changes

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│     USERS       │◄─────┤   TRANSACTIONS  │
│                 │ 1:N  │                 │
│ • id (PK)       │      │ • id (PK)       │
│ • name          │      │ • user_id (FK)  │
│ • email (UQ)    │      │ • amount        │
│ • credit_limit  │      │ • timestamp     │
│ • credit_type   │      └─────────────────┘
│ • risk_category │
└─────────────────┘
         ▲                ┌─────────────────┐
         │ 1:N            │ EMOTIONAL_EVENTS│
         └───────────────►│                 │
                          │ • id (PK)       │
                          │ • user_id (FK)  │
                          │ • emotion_label │
                          │ • valence       │
                          │ • arousal       │
                          │ • ingested_at   │
                          └─────────────────┘
         ▲
         │ 1:N            ┌─────────────────┐
         └───────────────►│CREDIT_EVALUATIONS│
                          │                 │
                          │ • id (PK)       │
                          │ • user_id (FK)  │
                          │ • risk_score    │
                          │ • approved      │
                          │ • evaluated_at  │
                          └─────────────────┘
```

## Example SQL Queries

### Query 1: Retrieve all emotional events for a user in the last week

```sql
-- Get all emotional events for user in the last 7 days
SELECT 
    ee.id,
    ee.emotion_label,
    ee.valence,
    ee.arousal,
    ee.confidence,
    ee.source,
    ee.ingested_at,
    u.name as user_name
FROM emotional_events ee
JOIN users u ON ee.user_id = u.id
WHERE ee.user_id = $1  -- Parameter: user_id
  AND ee.ingested_at >= NOW() - INTERVAL '7 days'
ORDER BY ee.ingested_at DESC;

-- Performance: Uses idx_user_emotion_time index
-- Expected execution time: < 10ms for typical datasets
```

**Use Case**: Real-time emotional state analysis for credit decisions.

### Query 2: Identify high-risk customers based on credit score thresholds

```sql
-- Find high-risk customers with recent evaluations
SELECT DISTINCT
    u.id,
    u.name,
    u.email,
    u.credit_limit,
    u.risk_category,
    ce.risk_score,
    ce.approved,
    ce.evaluated_at,
    COUNT(t.id) as transaction_count_30d,
    AVG(ee.valence) as avg_emotional_valence
FROM users u
JOIN credit_evaluations ce ON u.id = ce.user_id
LEFT JOIN transactions t ON u.id = t.user_id 
    AND t.timestamp >= NOW() - INTERVAL '30 days'
LEFT JOIN emotional_events ee ON u.id = ee.user_id 
    AND ee.ingested_at >= NOW() - INTERVAL '30 days'
WHERE ce.risk_score >= 0.6  -- High risk threshold
  AND ce.evaluated_at = (
      -- Get most recent evaluation for each user
      SELECT MAX(ce2.evaluated_at) 
      FROM credit_evaluations ce2 
      WHERE ce2.user_id = u.id
  )
  AND u.is_active = TRUE
GROUP BY u.id, u.name, u.email, u.credit_limit, u.risk_category, 
         ce.risk_score, ce.approved, ce.evaluated_at
ORDER BY ce.risk_score DESC, ce.evaluated_at DESC;

-- Performance: Uses idx_risk_score_time and idx_user_evaluation_time indexes
-- Expected execution time: < 50ms for datasets up to 100K users
```

**Use Case**: Risk management and portfolio analysis for business intelligence.

### Query 3: Analyze emotional patterns before credit applications

```sql
-- Emotional state analysis 24 hours before credit evaluation
SELECT 
    u.id as user_id,
    u.name,
    ce.risk_score,
    ce.approved,
    ce.evaluated_at,
    COUNT(ee.id) as emotion_events_count,
    AVG(ee.valence) as avg_valence_24h,
    AVG(ee.arousal) as avg_arousal_24h,
    STRING_AGG(DISTINCT ee.emotion_label, ', ') as emotions_detected
FROM users u
JOIN credit_evaluations ce ON u.id = ce.user_id
LEFT JOIN emotional_events ee ON u.id = ee.user_id
    AND ee.ingested_at BETWEEN 
        ce.evaluated_at - INTERVAL '24 hours' 
        AND ce.evaluated_at
WHERE ce.evaluated_at >= NOW() - INTERVAL '30 days'
GROUP BY u.id, u.name, ce.risk_score, ce.approved, ce.evaluated_at
HAVING COUNT(ee.id) > 0  -- Only users with emotional data
ORDER BY ce.evaluated_at DESC;
```

**Use Case**: Research emotional predictors of credit decisions.

### Query 4: Transaction pattern analysis for credit evaluation

```sql
-- Comprehensive financial behavior analysis
SELECT 
    u.id,
    u.name,
    u.current_credit_limit,
    -- Transaction Analysis
    COUNT(t.id) as total_transactions,
    SUM(CASE WHEN t.transaction_type = 'credit' THEN t.amount ELSE 0 END) as total_credits,
    SUM(CASE WHEN t.transaction_type = 'debit' THEN t.amount ELSE 0 END) as total_debits,
    AVG(t.amount) as avg_transaction_amount,
    -- Recent Activity
    COUNT(CASE WHEN t.timestamp >= NOW() - INTERVAL '30 days' THEN 1 END) as transactions_30d,
    -- Spending Categories
    COUNT(DISTINCT t.merchant_category) as merchant_categories,
    -- Risk Indicators
    MAX(t.amount) as largest_transaction,
    STDDEV(t.amount) as transaction_volatility
FROM users u
LEFT JOIN transactions t ON u.id = t.user_id
WHERE u.is_active = TRUE
GROUP BY u.id, u.name, u.current_credit_limit
HAVING COUNT(t.id) > 0  -- Only users with transaction history
ORDER BY u.credit_limit DESC;
```

**Use Case**: ML feature engineering for credit risk modeling.

## Database Performance Considerations

### Index Strategy

1. **Primary Keys**: Automatic B-tree indexes
2. **Foreign Keys**: Indexed for JOIN performance
3. **Time-series**: Composite indexes on (user_id, timestamp)
4. **Search Fields**: Individual indexes on frequently queried columns
5. **Analytics**: Covering indexes for common GROUP BY queries

### Query Optimization

- **Parameterized Queries**: Prevent SQL injection and enable plan caching
- **LIMIT Clauses**: Pagination for large result sets
- **Index Hints**: Use EXPLAIN ANALYZE for query plan analysis
- **Partitioning**: Consider time-based partitioning for large tables

### Maintenance

```sql
-- Regular maintenance commands
REINDEX DATABASE cloudwalk_ecs;
VACUUM ANALYZE;
UPDATE pg_stat_reset();
```

## Security Considerations

1. **Data Encryption**: Sensitive fields encrypted at application level
2. **Access Control**: Role-based database permissions
3. **Audit Logging**: Track all data modifications
4. **Backup Strategy**: Regular encrypted backups with point-in-time recovery
5. **PII Protection**: Compliance with data protection regulations

## Scalability Notes

- **Read Replicas**: For analytics and reporting workloads
- **Connection Pooling**: PgBouncer for connection management
- **Monitoring**: PostgreSQL metrics and slow query logging
- **Archiving**: Move old data to separate analytics warehouse

This schema supports the full CloudWalk Empathic Credit System requirements with optimal performance for real-time credit decisions and comprehensive analytics.
