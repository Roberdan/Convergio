#!/usr/bin/env python3
"""
Test roberdan password hash
"""

import bcrypt

# Hash for roberdan@convergio.local
roberdan_hash = "$2a$10$V.Llggvgbrw0eqgy07DdcuZ2KpU2BWR5iLarsHU2z2v5H4YIfZwSe"

test_passwords = [
    "admin123",
    "admin", 
    "password",
    "convergio",
    "roberdan",
    "123456",
    "Convergio123",
    "roberto",
    "roberdan123"
]

print(f"Testing passwords against roberdan hash:")
print(f"Hash: {roberdan_hash}")
print()

for password in test_passwords:
    try:
        result = bcrypt.checkpw(password.encode('utf-8'), roberdan_hash.encode('utf-8'))
        print(f"'{password}' -> {'✅ MATCH' if result else '❌ No match'}")
    except Exception as e:
        print(f"'{password}' -> Error: {e}")