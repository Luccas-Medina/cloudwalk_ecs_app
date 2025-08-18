"""Enhanced database schema with comprehensive indexing

Revision ID: enhanced_schema_v2
Revises: initial_tables
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'enhanced_schema_v2'
down_revision = 'initial_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Drop existing tables if they exist (for clean migration)
    op.execute("DROP TABLE IF EXISTS credit_evaluations CASCADE;")
    op.execute("DROP TABLE IF EXISTS emotional_events CASCADE;")
    op.execute("DROP TABLE IF EXISTS transactions CASCADE;")
    op.execute("DROP TABLE IF EXISTS users CASCADE;")
    
    # Create enhanced users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Credit Information
        sa.Column('credit_limit', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('credit_type', sa.String(length=50), nullable=False, server_default='Short-Term'),
        sa.Column('last_credit_evaluation', sa.DateTime(timezone=True), nullable=True),
        sa.Column('credit_score', sa.Float(), nullable=True),
        
        # Account Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('risk_category', sa.String(length=20), nullable=False, server_default='Medium'),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('merchant_category', sa.String(length=100), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Create emotional_events table
    op.create_table('emotional_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        
        # Emotional Analysis
        sa.Column('emotion_label', sa.String(length=50), nullable=True),
        sa.Column('valence', sa.Float(), nullable=True),
        sa.Column('arousal', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('raw_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # Timestamps
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Create credit_evaluations table
    op.create_table('credit_evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        
        # ML Model Results
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('features_used', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        
        # Credit Decision
        sa.Column('approved', sa.Boolean(), nullable=False),
        sa.Column('credit_limit_offered', sa.Float(), nullable=True),
        sa.Column('interest_rate', sa.Float(), nullable=True),
        sa.Column('credit_type', sa.String(length=50), nullable=True),
        
        # Decision Context
        sa.Column('evaluation_reason', sa.String(length=255), nullable=True),
        sa.Column('decision_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Create indexes for users table
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_credit_limit', 'users', ['credit_limit'])
    op.create_index('idx_users_risk_category', 'users', ['risk_category'])
    op.create_index('idx_users_last_evaluation', 'users', ['last_credit_evaluation'])
    
    # Create strategic indexes for transactions table
    op.create_index('idx_user_transaction_date', 'transactions', ['user_id', 'timestamp'])
    op.create_index('idx_transaction_amount_date', 'transactions', ['amount', 'timestamp'])
    op.create_index('idx_user_transaction_type', 'transactions', ['user_id', 'transaction_type'])
    op.create_index('idx_transactions_timestamp', 'transactions', ['timestamp'])
    
    # Create time-series optimized indexes for emotional_events table
    op.create_index('idx_user_emotion_time', 'emotional_events', ['user_id', 'ingested_at'])
    op.create_index('idx_user_emotion_label', 'emotional_events', ['user_id', 'emotion_label'])
    op.create_index('idx_emotion_valence_arousal', 'emotional_events', ['valence', 'arousal'])
    op.create_index('idx_user_session', 'emotional_events', ['user_id', 'session_id'])
    op.create_index('idx_emotion_source_time', 'emotional_events', ['source', 'ingested_at'])
    op.create_index('idx_emotional_events_ingested_at', 'emotional_events', ['ingested_at'])
    
    # Create analytics optimized indexes for credit_evaluations table
    op.create_index('idx_user_evaluation_time', 'credit_evaluations', ['user_id', 'evaluated_at'])
    op.create_index('idx_risk_score_time', 'credit_evaluations', ['risk_score', 'evaluated_at'])
    op.create_index('idx_approval_time', 'credit_evaluations', ['approved', 'evaluated_at'])
    op.create_index('idx_model_version', 'credit_evaluations', ['model_version'])


def downgrade():
    # Drop all indexes
    op.drop_index('idx_model_version', table_name='credit_evaluations')
    op.drop_index('idx_approval_time', table_name='credit_evaluations')
    op.drop_index('idx_risk_score_time', table_name='credit_evaluations')
    op.drop_index('idx_user_evaluation_time', table_name='credit_evaluations')
    
    op.drop_index('idx_emotional_events_ingested_at', table_name='emotional_events')
    op.drop_index('idx_emotion_source_time', table_name='emotional_events')
    op.drop_index('idx_user_session', table_name='emotional_events')
    op.drop_index('idx_emotion_valence_arousal', table_name='emotional_events')
    op.drop_index('idx_user_emotion_label', table_name='emotional_events')
    op.drop_index('idx_user_emotion_time', table_name='emotional_events')
    
    op.drop_index('idx_transactions_timestamp', table_name='transactions')
    op.drop_index('idx_user_transaction_type', table_name='transactions')
    op.drop_index('idx_transaction_amount_date', table_name='transactions')
    op.drop_index('idx_user_transaction_date', table_name='transactions')
    
    op.drop_index('idx_users_last_evaluation', table_name='users')
    op.drop_index('idx_users_risk_category', table_name='users')
    op.drop_index('idx_users_credit_limit', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    
    # Drop all tables
    op.drop_table('credit_evaluations')
    op.drop_table('emotional_events')
    op.drop_table('transactions')
    op.drop_table('users')
