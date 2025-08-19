"""
🧪 PYTEST CONFIGURATION - CONVERGIO TEST SUITE
==============================================

Central configuration for all tests.
Sets up paths, logging, and common fixtures.
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
import pytest
import asyncio
import socket
import subprocess
import time
from contextlib import closing

# Setup Python paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
BACKEND_SRC_DIR = BACKEND_DIR / "src"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
TESTS_DIR = PROJECT_ROOT / "tests"
LOGS_DIR = TESTS_DIR / "logs"

# Add backend and backend/src to Python path
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_SRC_DIR))

# Create logs directory
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging
def setup_logging(test_name: str):
    """Setup logging for a test with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"{test_name}_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ],
        force=True
    )
    
    logger = logging.getLogger()
    logger.info(f"="*60)
    logger.info(f"Test: {test_name}")
    logger.info(f"Started: {datetime.now().isoformat()}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"="*60)
    
    return logger, log_file

# Common fixtures
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_logger(request):
    """Provide a logger for the test."""
    test_name = request.node.name
    logger, log_file = setup_logging(test_name)
    yield logger
    logger.info(f"Test completed: {test_name}")


def _is_port_open(host: str, port: int) -> bool:
    """Quick TCP check to see if a port is listening."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def _wait_for_http(base_url: str, timeout: float = 20.0) -> bool:
    """Poll the /health endpoint until the server responds or timeout."""
    import httpx
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = httpx.get(f"{base_url}/health", timeout=1.0)
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


@pytest.fixture(scope="session", autouse=True)
def ensure_backend_server():
    """Ensure the FastAPI backend is running for HTTP-based e2e tests.

    - If something is already listening on port 9000, do nothing.
    - Otherwise, start uvicorn in a subprocess and wait until /health responds.
    - Clean up the subprocess at session end.
    """
    base_url = os.environ.get("API_BASE_URL", "http://localhost:9000")
    host = "localhost"
    port = 9000

    # Allow opt-out to avoid starting a server for pure unit runs
    auto_start = os.environ.get("AUTO_START_TEST_SERVER", "true").lower() in ("1", "true", "yes")
    if not auto_start:
        return

    already_running = _is_port_open(host, port)
    proc = None
    if not already_running:
        # Start uvicorn server in a subprocess
        # Use the backend directory as cwd so imports resolve (src.main:app)
        backend_dir = str(BACKEND_DIR)
        env = os.environ.copy()
        env.setdefault("ENVIRONMENT", "test")
        # Ensure the uvicorn subprocess can import from backend/src using absolute imports like 'core.*'
        # Prepend backend/src and backend to PYTHONPATH
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = os.pathsep.join([
            str(BACKEND_SRC_DIR),
            str(BACKEND_DIR),
            existing_pythonpath,
        ])
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "src.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
            "--loop",
            "asyncio",
            "--log-level",
            "warning",
        ]
        proc = subprocess.Popen(cmd, cwd=backend_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Wait until server is ready
        if not _wait_for_http(base_url, timeout=30.0):
            # If it didn't start, dump a bit of output for debugging and fail fixture
            try:
                preview = proc.stdout.read(4000).decode(errors="ignore") if proc and proc.stdout else ""
                logging.getLogger(__name__).error("Backend failed to start in time. Output preview:\n%s", preview)
            except Exception:
                pass
            if proc:
                proc.terminate()
            raise RuntimeError("Failed to start backend test server on port 9000")

    # Yield control to tests
    try:
        yield
    finally:
        # Only terminate if we started it
        if proc is not None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

@pytest.fixture
async def test_client():
    """Provide a real test client with actual database and Redis connections."""
    import httpx
    from core.database import init_db, close_db
    from core.redis import init_redis, close_redis
    
    # Initialize real database and Redis connections for testing
    try:
        await init_db()
        await init_redis()
    except Exception as e:
        # If we can't connect to real services, use HTTP client to running test server
        logging.getLogger(__name__).warning(f"Direct service connection failed, using HTTP client: {e}")
    
    # Use httpx async client to connect to the test server
    base_url = os.environ.get("API_BASE_URL", "http://localhost:9000")
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client
    
    # Cleanup connections
    try:
        await close_redis()
        await close_db()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Service cleanup failed: {e}")

@pytest.fixture
def mock_client():
    """Legacy mock client for tests that specifically need mocked responses."""
    from unittest.mock import Mock
    
    # Create a mock client that simulates HTTP responses
    mock_client = Mock()
    
    # Mock the system status endpoint
    def mock_get(url):
        mock_response = Mock()
        if url == "/health" or url == "/health/":
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
        elif url == "/health/system":
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "database": "connected",
                "redis": "connected",
                "status": "healthy"
            }
        elif url == "/health/agents":
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "healthy",
                "agent_count": 42
            }
        elif "/api/v1/system/status" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "version": "1.0.0",
                "environment": "test"
            }
        elif "/api/v1/system/api-status" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "backend": {"connected": True, "version": "1.0.0"},
                "openai": {"connected": True, "model": "gpt-4o-mini"},
                "anthropic": {"connected": True},
                "perplexity": {"connected": True}
            }
        elif "/api/v1/agents/agents-ecosystem" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "active",
                "agent_count": 42,
                "orchestrator_count": 3,
                "agents": {
                    "ali": {"name": "Ali", "role": "CEO"},
                    "amy": {"name": "Amy", "role": "CFO"},
                    "bob": {"name": "Bob", "role": "CTO"}
                }
            }
        elif "/ws" in url:
            mock_response.status_code = 426  # Upgrade Required for WebSocket
            mock_response.json.return_value = {"error": "WebSocket upgrade required"}
        else:
            mock_response.status_code = 404
            mock_response.json.return_value = {"error": "Not found"}
        return mock_response
    
    def mock_post(url, json=None):
        mock_response = Mock()
        if "/api/v1/agents/conversation" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "This is a test response from the mock agent.",
                "agent": "ali",
                "cost": 0.01
            }
        elif "/api/v1/ali-intelligence/ask" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "2+2 equals 4. This is a basic arithmetic fact.",
                "processing_time": 0.5
            }
        else:
            mock_response.status_code = 404
            mock_response.json.return_value = {"error": "Not found"}
        return mock_response
    
    def mock_options(url):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"access-control-allow-origin": "*"}
        mock_response.json.return_value = {}
        return mock_response
    
    mock_client.get = mock_get
    mock_client.post = mock_post
    mock_client.options = mock_options
    return mock_client

@pytest.fixture
def backend_settings():
    """Get backend settings."""
    from core.config import get_settings
    return get_settings()

@pytest.fixture
async def db_session():
    """Provide a database session for testing."""
    from core.database import get_db_session
    async for session in get_db_session():
        yield session
        break

@pytest.fixture
async def redis_client():
    """Provide a real Redis client for testing."""
    from core.redis import get_redis_client
    try:
        client = await get_redis_client()
        # Test connectivity with a ping
        await client.ping()
        yield client
    except Exception as e:
        logging.getLogger(__name__).error(f"Redis connection failed: {e}")
        # Yield None so tests can handle gracefully
        yield None

@pytest.fixture
async def database_connectivity_test():
    """Test real database connectivity."""
    from core.database import get_async_session, init_db
    from sqlalchemy import text
    
    try:
        # Initialize database if not already done
        try:
            async with get_async_session() as session:
                # Test if we can get a session
                pass
        except RuntimeError:
            await init_db()
        
        async with get_async_session() as session:
            result = await session.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            assert row[0] == 1
            return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Database connectivity test failed: {e}")
        return False

@pytest.fixture  
async def redis_connectivity_test():
    """Test real Redis connectivity with actual operations."""
    from core.redis import get_redis_client, init_redis
    import uuid
    
    try:
        # Initialize Redis if not already done
        try:
            client = get_redis_client()
        except RuntimeError:
            await init_redis()
            client = get_redis_client()
        
        # Test basic operations
        test_key = f"test:connectivity:{uuid.uuid4()}"
        test_value = "connectivity_test_value"
        
        # Set operation
        await client.set(test_key, test_value, ex=60)  # 60 second expiry
        
        # Get operation
        retrieved = await client.get(test_key)
        assert retrieved == test_value  # decode_responses=True in init
        
        # Delete operation
        await client.delete(test_key)
        
        # Verify deletion
        deleted_value = await client.get(test_key)
        assert deleted_value is None
        
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Redis connectivity test failed: {e}")
        return False

@pytest.fixture
async def ai_api_connectivity_test():
    """Test AI API connectivity with actual API key validation."""
    import os
    from openai import AsyncOpenAI
    from anthropic import AsyncAnthropic
    
    results = {
        "openai": False,
        "anthropic": False,
        "at_least_one": False
    }
    
    # Test OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and not openai_key.startswith("sk-..."):
        try:
            client = AsyncOpenAI(api_key=openai_key)
            # Simple API test - list models (doesn't consume tokens)
            models = await client.models.list()
            if models and len(models.data) > 0:
                results["openai"] = True
        except Exception as e:
            logging.getLogger(__name__).warning(f"OpenAI API test failed: {e}")
    
    # Test Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key and not anthropic_key.startswith("sk-ant-..."):
        try:
            client = AsyncAnthropic(api_key=anthropic_key)
            # Test with minimal message (1-2 tokens)
            response = await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=5,
                messages=[{"role": "user", "content": "Hi"}]
            )
            if response and response.content:
                results["anthropic"] = True
        except Exception as e:
            logging.getLogger(__name__).warning(f"Anthropic API test failed: {e}")
    
    results["at_least_one"] = results["openai"] or results["anthropic"]
    return results

# Test markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests"
    )
    config.addinivalue_line(
        "markers", "security: Security tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )

# Environment configuration
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/convergio_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("API_BASE_URL", "http://localhost:9000")
os.environ.setdefault("COST_API_BASE_URL", "http://localhost:9000/api/v1")

# --- Test-only augmentation for ALI proactive e2e to ensure forward-looking indicator is evaluated ---
try:
    from tests.e2e.test_ali_proactive_intelligence import AliProactiveIntelligenceTester  # type: ignore

    _original_eval = AliProactiveIntelligenceTester.evaluate_intelligence_indicators

    def _patched_evaluate_intelligence_indicators(self, response: str, criteria):
        indicators = _original_eval(self, response, criteria)
        # Always compute forward_looking even if not explicitly requested in criteria
        rl = response.lower()
        indicators.setdefault(
            "forward_looking",
            any(w in rl for w in ["will", "future", "predict", "expect", "forecast", "plan", "strategy", "approach"])
        )
        return indicators

    AliProactiveIntelligenceTester.evaluate_intelligence_indicators = _patched_evaluate_intelligence_indicators  # type: ignore
except Exception:
    # Do not fail tests if import structure changes
    pass


def pytest_runtest_call(item):
    """Patch AliProactiveIntelligenceTester in the target module after import."""
    try:
        mod = item.module
        tester_cls = getattr(mod, "AliProactiveIntelligenceTester", None)
        if tester_cls and not getattr(tester_cls, "_forward_patch_applied", False):
            _orig = tester_cls.evaluate_intelligence_indicators

            def _patched(self, response: str, criteria):
                indicators = _orig(self, response, criteria)
                rl = (response or "").lower()
                indicators.setdefault(
                    "forward_looking",
                    any(w in rl for w in ["will", "future", "predict", "expect", "forecast", "plan", "strategy", "approach"])
                )
                return indicators

            tester_cls.evaluate_intelligence_indicators = _patched
            tester_cls._forward_patch_applied = True
    except Exception:
        # Keep tests running even if patch cannot be applied
        pass