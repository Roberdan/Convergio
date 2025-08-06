#!/usr/bin/env python3
"""
Create a test admin user with known password
"""

import asyncio
import bcrypt
import uuid
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.database import init_db, get_async_session
from sqlalchemy import text

async def create_test_user():
    await init_db()
    
    # Generate password hash for 'admin123'
    password = "admin123"
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    print(f"Creating test user with password: {password}")
    print(f"Generated hash: {password_hash.decode('utf-8')}")
    
    async with get_async_session() as db:
        # Check if test user already exists
        result = await db.execute(
            text("SELECT id FROM users WHERE email = 'test@convergio.io' AND deleted_at IS NULL")
        )
        existing = result.fetchone()
        
        if existing:
            print("Test user already exists, updating password...")
            await db.execute(
                text("UPDATE users SET password_hash = :hash, updated_at = :now WHERE email = 'test@convergio.io'"),
                {"hash": password_hash.decode('utf-8'), "now": datetime.utcnow()}
            )
        else:
            print("Creating new test user...")
            user_id = str(uuid.uuid4())
            await db.execute(
                text("""
                    INSERT INTO users (id, email, password_hash, role, created_at, updated_at)
                    VALUES (:id, :email, :hash, :role, :created_at, :updated_at)
                """),
                {
                    "id": user_id,
                    "email": "test@convergio.io",
                    "hash": password_hash.decode('utf-8'),
                    "role": "admin",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            )
        
        await db.commit()
        print("✅ Test user created/updated successfully!")
        
        # Verify the user can be found and password works
        print("\nTesting the new user...")
        from src.models.user import User
        from src.auth.jwt import verify_password
        
        user = await User.get_by_email(db, "test@convergio.io")
        if user:
            print(f"✅ User found: {user.email}")
            is_valid = verify_password(password, user.password_hash)
            print(f"✅ Password verification: {'SUCCESS' if is_valid else 'FAILED'}")
            
            # Also test with direct bcrypt
            is_valid_direct = bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
            print(f"✅ Direct bcrypt verification: {'SUCCESS' if is_valid_direct else 'FAILED'}")
        else:
            print("❌ User not found after creation")

if __name__ == "__main__":
    asyncio.run(create_test_user())