#!/usr/bin/env python3
"""
Test login functionality step by step
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.database import init_db, get_async_session
from src.models.user import User
from src.auth.jwt import verify_password

async def test_login():
    await init_db()
    
    username = "admin"
    password = "admin123"
    
    print(f"Testing login for username: {username}")
    print(f"Password: {password}")
    print()
    
    async with get_async_session() as db:
        # Test user lookup
        print("1. Testing get_by_username...")
        user = await User.get_by_username(db, username)
        
        if user:
            print(f"✅ User found: {user.email}")
            print(f"   Role: {user.role}")
            print(f"   Is active: {user.is_active}")
            print(f"   Password hash: {user.password_hash[:50]}...")
            
            # Test password verification
            print("\n2. Testing password verification...")
            is_valid = verify_password(password, user.password_hash)
            print(f"   Password valid: {'✅ YES' if is_valid else '❌ NO'}")
            
            if not is_valid:
                # Test other common passwords
                test_passwords = ["admin", "password", "123456", "convergio"]
                print("\n   Testing other passwords:")
                for test_pwd in test_passwords:
                    is_valid = verify_password(test_pwd, user.password_hash)
                    print(f"   '{test_pwd}': {'✅ MATCH' if is_valid else '❌ No match'}")
        else:
            print("❌ User not found")
            
            # Check what users exist
            print("\n   Checking existing users...")
            from sqlalchemy import text
            result = await db.execute(text("SELECT email FROM users WHERE deleted_at IS NULL LIMIT 5"))
            users = result.fetchall()
            for user_row in users:
                print(f"   - {user_row.email}")
                
            # Check if email lookup works
            print(f"\n   Testing direct email lookup...")
            user_by_email = await User.get_by_email(db, "admin@convergio.io")
            if user_by_email:
                print(f"   ✅ Direct email lookup found: {user_by_email.email}")
                is_valid = verify_password(password, user_by_email.password_hash)
                print(f"   Password valid: {'✅ YES' if is_valid else '❌ NO'}")

if __name__ == "__main__":
    asyncio.run(test_login())