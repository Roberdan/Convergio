#!/usr/bin/env python3
"""
Test script to verify password hashing and check database
"""

import bcrypt
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# Test different passwords against the stored hash
stored_hash = "$2a$12$LQv3c1yqBw2LHKVqY9nA0eBHhcrZWPh/lqwk0Lbt8u4cHj.JqKmFa"

test_passwords = [
    "admin",
    "admin123", 
    "password",
    "convergio",
    "Convergio123",
    "admin@convergio.io",
    "123456"
]

print("Testing passwords against stored hash:")
print(f"Hash: {stored_hash}")
print()

for password in test_passwords:
    try:
        # Test with bcrypt (used by our current system)
        result = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        print(f"'{password}' -> {'✅ MATCH' if result else '❌ No match'}")
    except Exception as e:
        print(f"'{password}' -> Error: {e}")

print("\n" + "="*50)

# Also test database connection and user lookup
async def test_db():
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/convergio_db"
    
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # Test user lookup
        result = await session.execute(
            text("SELECT email, password_hash FROM users WHERE email LIKE 'admin@%' AND deleted_at IS NULL")
        )
        users = result.fetchall()
        
        print(f"Found {len(users)} users matching 'admin@%':")
        for user in users:
            print(f"  - {user.email}: {user.password_hash[:20]}...")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_db())