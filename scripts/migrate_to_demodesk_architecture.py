#!/usr/bin/env python3
"""
Migration Script: Transform Stellar Sales System to DemoDesk-Style Architecture
Date: October 23, 2025
Purpose: Run database migrations and set up multi-tenant support

Usage:
    python scripts/migrate_to_demodesk_architecture.py
"""

import sys
from pathlib import Path
from sqlalchemy import text
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from core.database.postgres import PostgresManager


def run_sql_file(sql_file_path: Path):
    """Execute SQL file directly using psycopg2."""
    print(f"\n📄 Executing SQL file: {sql_file_path.name}")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Read and execute SQL file
        with open(sql_file_path, 'r') as f:
            sql_script = f.read()
        
        cursor.execute(sql_script)
        print(f"✅ Successfully executed {sql_file_path.name}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error executing {sql_file_path.name}: {e}")
        raise


def verify_tables_created():
    """Verify that all new tables were created successfully."""
    print("\n🔍 Verifying tables...")
    
    postgres_manager = PostgresManager(settings)
    session = postgres_manager.get_session()
    
    expected_tables = [
        'organizations',
        'users',
        'meeting_sessions',
        'suggestions',
        'team_metrics',
        'audit_logs',
        'invitations'
    ]
    
    try:
        result = session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        
        existing_tables = [row[0] for row in result]
        
        print("\n📊 Existing tables:")
        for table in existing_tables:
            status = "✅" if table in expected_tables or table == 'transcripts' else "📋"
            print(f"   {status} {table}")
        
        # Check if all expected tables exist
        missing_tables = [t for t in expected_tables if t not in existing_tables]
        if missing_tables:
            print(f"\n⚠️ Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            print(f"\n✅ All {len(expected_tables)} new tables created successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False
    finally:
        session.close()


def check_demo_user():
    """Check if demo user was created."""
    print("\n👤 Checking demo user...")
    
    postgres_manager = PostgresManager(settings)
    session = postgres_manager.get_session()
    
    try:
        result = session.execute(text("""
            SELECT email, full_name, role 
            FROM users 
            WHERE email = 'admin@demo.com'
        """))
        
        user = result.fetchone()
        if user:
            print(f"✅ Demo user exists:")
            print(f"   Email: {user[0]}")
            print(f"   Name: {user[1]}")
            print(f"   Role: {user[2]}")
            print(f"   Password: password123 (CHANGE THIS IN PRODUCTION!)")
            return True
        else:
            print("⚠️ Demo user not found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking demo user: {e}")
        return False
    finally:
        session.close()


def print_next_steps():
    """Print next steps for the developer."""
    print("\n" + "="*60)
    print("🎉 MIGRATION COMPLETE!")
    print("="*60)
    
    print("\n📝 NEXT STEPS:\n")
    
    print("1. 🔐 Update Demo User Password:")
    print("   >>> from passlib.hash import bcrypt")
    print("   >>> bcrypt.hash('your_new_password')")
    print("   >>> # Update users table with new hash\n")
    
    print("2. 🌐 Set up Frontend:")
    print("   cd /workspace/frontend")
    print("   npm install")
    print("   npm run dev\n")
    
    print("3. 🔌 Add WebSocket Support:")
    print("   # See DEMODESK_QUICKSTART.md for Quick Win #1")
    print("   # Add WebSocket endpoint to api/app.py\n")
    
    print("4. 🎥 Register Zoom App:")
    print("   # Visit https://marketplace.zoom.us/develop/create")
    print("   # See DEMODESK_QUICKSTART.md for Quick Win #2\n")
    
    print("5. 📚 Read the Full Guide:")
    print("   /workspace/docs/DEMODESK_TRANSFORMATION_GUIDE.md")
    print("   /workspace/DEMODESK_QUICKSTART.md\n")
    
    print("="*60)
    print("🚀 You're ready to start building DemoDesk-like features!")
    print("="*60 + "\n")


def main():
    """Main migration orchestrator."""
    print("\n" + "="*60)
    print("🚀 STELLAR SALES SYSTEM → DEMODESK MIGRATION")
    print("="*60)
    
    # Step 1: Run SQL migration
    sql_file = Path(__file__).resolve().parent.parent / "sql" / "add_user_tables.sql"
    
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        print("Make sure you're running this from the project root.")
        sys.exit(1)
    
    try:
        run_sql_file(sql_file)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check that PostgreSQL is running: docker ps")
        print("2. Verify .env file has correct database credentials")
        print("3. Try manually: psql -U postgres -d stellar_sales -f sql/add_user_tables.sql")
        sys.exit(1)
    
    # Step 2: Verify tables
    if not verify_tables_created():
        print("\n⚠️ Some tables may not have been created correctly.")
        print("Check the SQL output above for errors.")
    
    # Step 3: Check demo user
    check_demo_user()
    
    # Step 4: Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
