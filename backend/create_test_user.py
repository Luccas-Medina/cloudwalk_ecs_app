#!/usr/bin/env python3
"""
Script to create test user for credit evaluation testing
"""

import sys
import os
sys.path.append('/app')

from app.core.db import SessionLocal, engine
# Import models directly from models.py file to avoid registry conflicts
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import models as models_module
User = models_module.User
Base = models_module.Base
from sqlalchemy.orm import Session

def create_test_user():
    """Create a test user for credit evaluation"""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        # Check if user with ID 1 already exists
        existing_user = db.query(User).filter(User.id == 1).first()
        if existing_user:
            print(f"✅ User 1 already exists: {existing_user.name} ({existing_user.email})")
            return existing_user
        
        # Create test user
        test_user = User(
            id=1,
            name="Test User",
            email="test@cloudwalk.com",
            credit_limit=0.0,
            credit_type="Short-Term"
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"✅ Created test user: {test_user.name} (ID: {test_user.id})")
        return test_user
        
    except Exception as e:
        db.rollback()
        print(f"❌ Failed to create test user: {e}")
        return None
    finally:
        db.close()

def check_database_status():
    """Check database connection and table status"""
    db: Session = SessionLocal()
    try:
        # Check total users
        user_count = db.query(User).count()
        print(f"📊 Total users in database: {user_count}")
        
        # List all users
        users = db.query(User).limit(5).all()
        for user in users:
            print(f"  - User {user.id}: {user.name} ({user.email})")
            
        return True
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Setting up test data for credit evaluation...")
    
    # Check database status
    if check_database_status():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
        sys.exit(1)
    
    # Create test user
    user = create_test_user()
    if user:
        print("🎯 Test user ready for credit evaluation!")
        print(f"You can now test with: POST /credit/evaluate/{user.id}")
    else:
        print("❌ Failed to create test user")
        sys.exit(1)
