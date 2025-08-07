#!/usr/bin/env python3
"""
🚀 Convergio - REAL Production Startup Script
Launch the unified backend with ZERO technical debt!
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if all dependencies are installed"""
    
    print("🔍 Checking dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required!")
        sys.exit(1)
    
    # Check if we're in the right directory
    if not Path("backend/src/main.py").exists():
        print("❌ Run this script from the Convergio root directory!")
        sys.exit(1)
    
    # Check if .env exists
    if not Path(".env").exists():
        print("❌ .env file not found! Copy from the main Convergio directory.")
        sys.exit(1)
    
    print("✅ Dependencies check passed")


def install_requirements():
    """Install Python requirements"""
    
    print("📦 Installing Python requirements...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"
        ], check=True, cwd=Path.cwd())
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements!")
        sys.exit(1)


def check_environment():
    """Check environment variables"""
    
    print("🔧 Checking environment configuration...")
    
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY", 
        "POSTGRES_HOST",
        "REDIS_HOST"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        sys.exit(1)
    
    print("✅ Environment configuration valid")


def check_services():
    """Check if required services are running"""
    
    print("🔍 Checking required services...")
    
    # Check PostgreSQL
    try:
        import psycopg2  
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", 5432),
            database=os.getenv("POSTGRES_DB", "convergio_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres")
        )
        conn.close()
        print("✅ PostgreSQL connection successful")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("💡 Make sure PostgreSQL is running and database exists")
        sys.exit(1)
    
    # Check Redis
    try:
        import redis
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
        r.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 Make sure Redis is running")
        sys.exit(1)


def test_openai_api():
    """Test OpenAI API connection"""
    
    print("🤖 Testing OpenAI API connection...")
    
    try:
        import httpx
        import asyncio
        
        async def test_api():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": "Hello, test connection"}],
                        "max_tokens": 10
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    print("✅ OpenAI API connection successful")
                    return True
                else:
                    print(f"❌ OpenAI API test failed: {response.status_code}")
                    return False
        
        result = asyncio.run(test_api())
        if not result:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        sys.exit(1)


def count_agents():
    """Count available agents in the system"""
    
    print("🤖 Counting available agents...")
    
    try:
        agents_dir = Path("backend/src/agents/definitions")
        if not agents_dir.exists():
            print("❌ Agents directory not found!")
            return
        
        agent_files = list(agents_dir.glob("*.md"))
        excluded_files = {"CommonValuesAndPrinciples.md", "MICROSOFT_VALUES.md"}
        valid_agents = [f for f in agent_files if f.name not in excluded_files]
        
        print(f"✅ Found {len(valid_agents)} REAL agents ready for deployment:")
        for agent_file in valid_agents[:10]:  # Show first 10
            agent_name = agent_file.stem.replace("-", " ").title()
            print(f"   • {agent_name}")
        
        if len(valid_agents) > 10:
            print(f"   ... and {len(valid_agents) - 10} more agents")
            
    except Exception as e:
        print(f"⚠️ Could not count agents: {e}")


def start_backend():
    """Start the FastAPI backend"""
    
    print("🚀 Starting Convergio Unified Backend...")
    print("=" * 60)
    print("🌐 Backend URL: http://localhost:9000")
    print("📚 API Docs: http://localhost:9000/docs")
    print("❤️ Health Check: http://localhost:9000/health")
    print("🔐 Authentication: http://localhost:9000/api/v1/auth")
    print("🤖 AI Agents: http://localhost:9000/api/v1/agents")
    print("🔍 Vector Search: http://localhost:9000/api/v1/vector")
    print("=" * 60)
    print("🛑 Press Ctrl+C to stop")
    print()
    
    try:
        # Change to backend directory
        os.chdir("backend")
        
        # Start with uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.main:app",
            "--host", "0.0.0.0",
            "--port", "9000", 
            "--reload",
            "--log-level", "info"
        ], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Convergio...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        sys.exit(1)


def main():
    """Main startup sequence"""
    
    print("🚀 CONVERGIO - UNIFIED BACKEND STARTUP")
    print("=" * 50)
    print("🎯 ZERO technical debt | ZERO mocks | ZERO fallbacks")
    print("🤖 REAL AI agents | REAL vector search | REAL everything")
    print("=" * 50)
    print()
    
    # Complete startup sequence
    check_dependencies()
    install_requirements()
    check_environment()
    check_services()
    test_openai_api()
    count_agents()
    
    print()
    print("✅ ALL SYSTEMS GO! Starting backend...")
    print()
    
    start_backend()


if __name__ == "__main__":
    main()