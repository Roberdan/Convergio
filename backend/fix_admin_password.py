#!/usr/bin/env python3
"""
Fix admin@convergio.io password to work with admin123
"""

import asyncio
import bcrypt
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.database import init_db, get_async_session
from sqlalchemy import text

async def fix_admin_password():
    await init_db()
    
    # Generate correct password hash for 'admin123'
    password = "admin123"
    salt = bcrypt.gensalt(rounds=12)  # Use same rounds as original
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    print(f"Updating admin@convergio.io password hash...")
    print(f"New hash: {password_hash.decode('utf-8')}")
    
    async with get_async_session() as db:
        # Update admin user password
        await db.execute(
            text("UPDATE users SET password_hash = :hash, updated_at = :now WHERE email = 'admin@convergio.io'"),
            {"hash": password_hash.decode('utf-8'), "now": datetime.utcnow()}
        )
        
        await db.commit()
        print("✅ admin@convergio.io password updated successfully!")
        
        # Test the updated user
        print("\nTesting the updated admin user...")
        from src.models.user import User
        from src.auth.jwt import verify_password
        
        user = await User.get_by_email(db, "admin@convergio.io")
        if user:
            print(f"✅ User found: {user.email}")
            is_valid = verify_password(password, user.password_hash)
            print(f"✅ Password verification: {'SUCCESS' if is_valid else 'FAILED'}")
            
            # Also test with direct bcrypt
            is_valid_direct = bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
            print(f"✅ Direct bcrypt verification: {'SUCCESS' if is_valid_direct else 'FAILED'}")
        else:
            print("❌ User not found")

if __name__ == "__main__":
    asyncio.run(fix_admin_password())