# alembic/versions/003_add_credit_deployment_tables.py
"""Add credit deployment and notification tables

Revision ID: 003_credit_deployment
Revises: 002_add_emotion_tables
Create Date: 2025-08-15 21:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '003_credit_deployment'
down_revision = '002_add_emotion_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Create credit_offers table
    op.create_table('credit_offers',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('offered_limit', sa.Float(), nullable=False),
        sa.Column('interest_rate', sa.Float(), nullable=False),
        sa.Column('credit_score_used', sa.Integer(), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('risk_assessment', sa.JSON(), nullable=True),
        sa.Column('emotional_context', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('deployed_at', sa.DateTime(), nullable=True),
        sa.Column('deployment_task_id', sa.String(255), nullable=True),
        sa.Column('deployment_attempts', sa.Integer(), default=0),
        sa.Column('deployment_error', sa.Text(), nullable=True),
    )
    
    # Create credit_deployment_events table
    op.create_table('credit_deployment_events',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('offer_id', sa.Integer(), sa.ForeignKey('credit_offers.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('task_id', sa.String(255), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('worker_id', sa.String(100), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
    )
    
    # Create credit_notifications table
    op.create_table('credit_notifications',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('offer_id', sa.Integer(), sa.ForeignKey('credit_offers.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('deep_link', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('device_token', sa.String(500), nullable=True),
        sa.Column('platform', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('push_notification_id', sa.String(255), nullable=True),
        sa.Column('delivery_response', sa.JSON(), nullable=True),
    )
    
    # Create user_credit_profiles table
    op.create_table('user_credit_profiles',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), unique=True, index=True, nullable=False),
        sa.Column('current_limit', sa.Float(), nullable=False, default=0.0),
        sa.Column('available_credit', sa.Float(), nullable=False, default=0.0),
        sa.Column('used_credit', sa.Float(), nullable=False, default=0.0),
        sa.Column('current_interest_rate', sa.Float(), nullable=True),
        sa.Column('credit_score', sa.Integer(), nullable=True),
        sa.Column('risk_category', sa.String(20), nullable=True),
        sa.Column('emotional_stability_score', sa.Float(), nullable=True),
        sa.Column('stress_indicators', sa.JSON(), nullable=True),
        sa.Column('last_emotion_update', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('last_limit_increase', sa.DateTime(), nullable=True),
    )
    
    # Create indexes for better performance
    op.create_index('idx_credit_offers_user_status', 'credit_offers', ['user_id', 'status'])
    op.create_index('idx_credit_offers_expires_at', 'credit_offers', ['expires_at'])
    op.create_index('idx_deployment_events_offer_type', 'credit_deployment_events', ['offer_id', 'event_type'])
    op.create_index('idx_notifications_user_status', 'credit_notifications', ['user_id', 'status'])
    op.create_index('idx_notifications_created_at', 'credit_notifications', ['created_at'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_notifications_created_at')
    op.drop_index('idx_notifications_user_status')
    op.drop_index('idx_deployment_events_offer_type')
    op.drop_index('idx_credit_offers_expires_at')
    op.drop_index('idx_credit_offers_user_status')
    
    # Drop tables
    op.drop_table('user_credit_profiles')
    op.drop_table('credit_notifications')
    op.drop_table('credit_deployment_events')
    op.drop_table('credit_offers')
