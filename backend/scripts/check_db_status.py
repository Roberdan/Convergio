#!/usr/bin/env python3
"""
Check database population status
"""

import asyncio
import asyncpg
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/convergio_db")


async def check_status():
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Get all tables
        tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
        """)
        
        print("\n" + "="*60)
        print("DATABASE POPULATION STATUS")
        print("="*60)
        
        empty_tables = []
        populated_tables = []
        
        for table in tables:
            table_name = table['tablename']
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            
            if count > 0:
                populated_tables.append((table_name, count))
            else:
                empty_tables.append(table_name)
        
        # Show populated tables
        print(f"\n✅ POPULATED TABLES ({len(populated_tables)}):")
        print("-"*40)
        for name, count in sorted(populated_tables, key=lambda x: x[1], reverse=True):
            print(f"  {name:30} {count:,} rows")
        
        # Show empty tables
        print(f"\n❌ EMPTY TABLES ({len(empty_tables)}):")
        print("-"*40)
        for name in empty_tables:
            print(f"  {name}")
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY:")
        print(f"  Total tables: {len(tables)}")
        print(f"  Populated: {len(populated_tables)} ({len(populated_tables)*100//len(tables)}%)")
        print(f"  Empty: {len(empty_tables)} ({len(empty_tables)*100//len(tables)}%)")
        
        # Calculate total rows
        total_rows = sum(count for _, count in populated_tables)
        print(f"  Total rows: {total_rows:,}")
        print("="*60)
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_status())