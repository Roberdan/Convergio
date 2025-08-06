#!/usr/bin/env python3
"""
Test bcrypt directly without passlib
"""

import bcrypt

# Test password verification with direct bcrypt
stored_hash = "$2a$12$LQv3c1yqBw2LHKVqY9nA0eBHhcrZWPh/lqwk0Lbt8u4cHj.JqKmFa"
test_password = "admin123"

print(f"Testing password: {test_password}")
print(f"Against hash: {stored_hash}")

try:
    # Convert strings to bytes
    password_bytes = test_password.encode('utf-8')
    hash_bytes = stored_hash.encode('utf-8')
    
    # Test with bcrypt directly
    result = bcrypt.checkpw(password_bytes, hash_bytes)
    print(f"Direct bcrypt result: {'✅ MATCH' if result else '❌ No match'}")
    
    # Test other passwords
    test_passwords = ["admin", "password", "123456", "convergio", "Convergio123", "admin@convergio.io"]
    
    print("\nTesting other passwords:")
    for pwd in test_passwords:
        pwd_bytes = pwd.encode('utf-8')
        result = bcrypt.checkpw(pwd_bytes, hash_bytes)
        print(f"'{pwd}': {'✅ MATCH' if result else '❌ No match'}")
        
except Exception as e:
    print(f"Error: {e}")
    
# Test creating a new hash for comparison
print("\nCreating new hash for 'admin123':")
try:
    new_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
    print(f"New hash: {new_hash.decode('utf-8')}")
    
    # Test the new hash
    result = bcrypt.checkpw("admin123".encode('utf-8'), new_hash)
    print(f"New hash verification: {'✅ MATCH' if result else '❌ No match'}")
except Exception as e:
    print(f"Error creating hash: {e}")