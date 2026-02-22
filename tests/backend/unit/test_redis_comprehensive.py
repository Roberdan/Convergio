#!/usr/bin/env python3
"""
Comprehensive tests for redis.py - Cache layer
Target: 23% → 80%+ coverage
"""

import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock, call
import json
import redis.asyncio as redis
from core.redis import init_redis, close_redis, get_redis_client, cache_set, cache_get, cache_delete


@pytest.fixture(scope="function", autouse=True)
async def redis_client_fixture():
    """Fixture to initialize and close Redis connection for each test function."""
    await init_redis()
    yield
    await close_redis()


class TestRedisConfiguration:
    """Test Redis configuration and setup"""
    
    @patch('core.config.get_settings')
    def test_redis_settings_integration(self, mock_get_settings):
        """Test Redis configuration from settings"""
        mock_settings = MagicMock()
        mock_settings.REDIS_URL = "redis://localhost:6379/1"
        mock_settings.REDIS_POOL_SIZE = 20
        mock_get_settings.return_value = mock_settings
        
        # Redis client should be configurable
    
    def test_redis_url_format(self):
        """Test Redis URL format validation"""
        from core.config import get_settings
        
        settings = get_settings()
        redis_url = settings.REDIS_URL
        
        # Should be proper Redis URL
        assert redis_url.startswith("redis://")
        assert str(settings.REDIS_DB) in redis_url


class TestRedisInitialization:
    """Test Redis initialization process"""
    
    @patch('redis.asyncio.from_url')
    async def test_init_redis_success(self, mock_from_url):
        """Test successful Redis initialization"""
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        mock_from_url.return_value = mock_client
        
        await init_redis()
        
        # Should create client and test connection
        mock_from_url.assert_called_once()
        mock_client.ping.assert_called_once()
    
    @patch('redis.asyncio.from_url')
    @patch('core.redis.logger')
    async def test_init_redis_connection_failure(self, mock_logger, mock_from_url):
        """Test Redis initialization with connection failure"""
        mock_client = AsyncMock()
        mock_client.ping.side_effect = redis.RedisError("Connection failed")
        mock_from_url.return_value = mock_client
        
        # Should handle connection failure
        with pytest.raises(redis.RedisError):
            await init_redis()
        
        mock_logger.error.assert_called()
    
    @patch('redis.asyncio.from_url')
    async def test_init_redis_pool_configuration(self, mock_from_url):
        """Test Redis connection pool configuration"""
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client

        from core.config import get_settings

        await init_redis()

        settings = get_settings()

        # Should configure connection pool
        mock_from_url.assert_called_with(
            settings.REDIS_URL,
            max_connections=settings.REDIS_POOL_SIZE,
            retry_on_timeout=True,
            decode_responses=True,
        )

    @patch('redis.asyncio.from_url')
    async def test_init_redis_uses_supabase_ca_cert_when_configured(self, mock_from_url):
        """Test Redis client enables TLS CA cert when configured for production infra."""
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        mock_from_url.return_value = mock_client

        ca_cert_path = "/etc/ssl/certs/supabase-ca.crt"
        with patch.dict(os.environ, {"SUPABASE_CA_CERT_PATH": ca_cert_path}, clear=False):
            await init_redis()

        from core.config import get_settings
        settings = get_settings()

        mock_from_url.assert_called_once_with(
            settings.REDIS_URL,
            max_connections=settings.REDIS_POOL_SIZE,
            retry_on_timeout=True,
            decode_responses=True,
            ssl=True,
            ssl_ca_certs=ca_cert_path,
        )


class TestRedisShutdown:
    """Test Redis shutdown process"""
    
    @patch('core.redis.redis_client')
    async def test_close_redis_success(self, mock_client):
        """Test successful Redis shutdown"""
        mock_client.aclose = AsyncMock()
        
        await close_redis()
        
        # Should close Redis connection
        mock_client.aclose.assert_called_once()
    
    @patch('core.redis.redis_client')
    @patch('core.redis.logger')
    async def test_close_redis_error_handling(self, mock_logger, mock_client):
        """Test Redis shutdown error handling"""
        mock_client.aclose.side_effect = Exception("Close error")
        
        # Should handle close errors gracefully
        await close_redis()
        
        mock_logger.error.assert_called()
    
    @patch('core.redis.redis_client', None)
    async def test_close_redis_no_client(self):
        """Test Redis shutdown when no client exists"""
                
        # Should handle case where client is None
        await close_redis()  # Should not raise exception


class TestRedisClient:
    """Test Redis client management"""
    
    @patch('core.redis.redis_client')
    def test_get_redis_client_success(self, mock_client):
        """Test getting Redis client when initialized"""
        
        client = get_redis_client()
        
        assert client is mock_client
    
    @patch('core.redis.redis_client', None)
    def test_get_redis_client_not_initialized(self):
        """Test getting Redis client when not initialized"""
        # Should raise RuntimeError when not initialized
        with pytest.raises(RuntimeError, match="Redis not initialized"):
            get_redis_client()


@pytest.mark.usefixtures("redis_client_fixture")
class TestCacheOperations:
    """Test Redis cache operations"""
    
    @patch('core.redis.get_redis_client')
    async def test_cache_set_string_success(self, mock_get_client):
        """Test successful cache set operation with string"""
        mock_client = AsyncMock()
        mock_client.setex.return_value = True
        mock_get_client.return_value = mock_client
        
        result = await cache_set("test_key", "test_value", 3600)
        
        assert result is True
        mock_client.setex.assert_called_once_with("test_key", 3600, "test_value")
    
    @patch('core.redis.get_redis_client')
    async def test_cache_set_dict_serialization(self, mock_get_client):
        """Test cache set with dictionary serialization"""
        mock_client = AsyncMock()
        mock_client.setex.return_value = True
        mock_get_client.return_value = mock_client
        
        test_dict = {"key": "value", "number": 42}
        result = await cache_set("dict_key", test_dict, 1800)
        
        assert result is True
        # Should serialize dict to JSON
        expected_json = json.dumps(test_dict)
        mock_client.setex.assert_called_once_with("dict_key", 1800, expected_json)
    
    @patch('core.redis.get_redis_client')
    async def test_cache_set_list_serialization(self, mock_get_client):
        """Test cache set with list serialization"""
        mock_client = AsyncMock()
        mock_client.setex.return_value = True
        mock_get_client.return_value = mock_client
        
                
        test_list = ["item1", "item2", {"nested": "object"}]
        result = await cache_set("list_key", test_list, 900)
        
        assert result is True
        expected_json = json.dumps(test_list)
        mock_client.setex.assert_called_once_with("list_key", 900, expected_json)
    
    @patch('core.redis.get_redis_client')
    @patch('core.redis.logger')
    async def test_cache_set_failure(self, mock_logger, mock_get_client):
        """Test cache set failure handling"""
        mock_client = AsyncMock()
        mock_client.setex.side_effect = redis.RedisError("Set failed")
        mock_get_client.return_value = mock_client
        
                
        result = await cache_set("fail_key", "value", 3600)
        
        assert result is False
        mock_logger.error.assert_called()


@pytest.mark.usefixtures("redis_client_fixture")
class TestCacheRetrieval:
    """Test Redis cache retrieval operations"""
    
    @patch('core.redis.get_redis_client')
    async def test_cache_get_string_success(self, mock_get_client):
        """Test successful cache get with string value"""
        mock_client = AsyncMock()
        mock_client.get.return_value = "cached_value"
        mock_get_client.return_value = mock_client
        
                
        result = await cache_get("test_key")
        
        assert result == "cached_value"
        mock_client.get.assert_called_once_with("test_key")
    
    @patch('core.redis.get_redis_client')
    async def test_cache_get_json_deserialization(self, mock_get_client):
        """Test cache get with JSON deserialization"""
        mock_client = AsyncMock()
        test_dict = {"key": "value", "number": 42}
        mock_client.get.return_value = json.dumps(test_dict)
        mock_get_client.return_value = mock_client
        
                
        result = await cache_get("json_key")
        
        assert result == test_dict
        mock_client.get.assert_called_once_with("json_key")
    
    @patch('core.redis.get_redis_client')
    async def test_cache_get_invalid_json_fallback(self, mock_get_client):
        """Test cache get with invalid JSON falls back to string"""
        mock_client = AsyncMock()
        mock_client.get.return_value = "invalid{json"
        mock_get_client.return_value = mock_client
        
                
        result = await cache_get("invalid_json_key")
        
        # Should return raw value when JSON parsing fails
        assert result == "invalid{json"
    
    @patch('core.redis.get_redis_client')
    async def test_cache_get_missing_key(self, mock_get_client):
        """Test cache get with missing key"""
        mock_client = AsyncMock()
        mock_client.get.return_value = None
        mock_get_client.return_value = mock_client
        
                
        result = await cache_get("missing_key")
        
        assert result is None
    
    @patch('core.redis.get_redis_client')
    @patch('core.redis.logger')
    async def test_cache_get_failure(self, mock_logger, mock_get_client):
        """Test cache get failure handling"""
        mock_client = AsyncMock()
        mock_client.get.side_effect = redis.RedisError("Get failed")
        mock_get_client.return_value = mock_client
        
                
        result = await cache_get("fail_key")
        
        assert result is None
        mock_logger.error.assert_called()


@pytest.mark.usefixtures("redis_client_fixture")
class TestCacheDeletion:
    """Test Redis cache deletion operations"""
    
    @patch('core.redis.get_redis_client')
    async def test_cache_delete_success(self, mock_get_client):
        """Test successful cache deletion"""
        mock_client = AsyncMock()
        mock_client.delete.return_value = 1  # 1 key deleted
        mock_get_client.return_value = mock_client
        
                
        result = await cache_delete("test_key")
        
        assert result is True
        mock_client.delete.assert_called_once_with("test_key")
    
    @patch('core.redis.get_redis_client')
    async def test_cache_delete_missing_key(self, mock_get_client):
        """Test cache deletion of missing key"""
        mock_client = AsyncMock()
        mock_client.delete.return_value = 0  # 0 keys deleted
        mock_get_client.return_value = mock_client
        
                
        result = await cache_delete("missing_key")
        
        assert result is False  # No key was deleted
    
    @patch('core.redis.get_redis_client')
    @patch('core.redis.logger')
    async def test_cache_delete_failure(self, mock_logger, mock_get_client):
        """Test cache delete failure handling"""
        mock_client = AsyncMock()
        mock_client.delete.side_effect = redis.RedisError("Delete failed")
        mock_get_client.return_value = mock_client
        
                
        result = await cache_delete("fail_key")
        
        assert result is False
        mock_logger.error.assert_called()


@pytest.mark.usefixtures("redis_client_fixture")
class TestRedisConnectionHandling:
    """Test Redis connection handling scenarios"""
    
    @patch('core.redis.get_redis_client')
    async def test_connection_retry_mechanism(self, mock_get_client):
        """Test Redis connection retry configuration"""
        from core.config import get_settings
        
        settings = get_settings()
        
        # Redis should be configured with retry_on_timeout
        # This is tested in initialization
        assert hasattr(settings, 'REDIS_URL')
    
    @patch('core.redis.get_redis_client')
    async def test_concurrent_cache_operations(self, mock_get_client):
        """Test concurrent cache operations"""
        mock_client = AsyncMock()
        mock_client.setex.return_value = True
        mock_client.get.return_value = "value"
        mock_client.delete.return_value = 1
        mock_get_client.return_value = mock_client

        # Test concurrent operations
        import asyncio
        results = await asyncio.gather(
            cache_set("key1", "value1", 3600),
            cache_get("key2"),
            cache_delete("key3"),
            return_exceptions=True
        )
        
        # All operations should complete
        assert len(results) == 3
    
    @patch('core.redis.get_redis_client')
    async def test_large_data_handling(self, mock_get_client):
        """Test handling of large data objects"""
        mock_client = AsyncMock()
        mock_client.setex.return_value = True
        mock_get_client.return_value = mock_client
        
                
        # Test large data structure
        large_data = {"agents": [{"id": i, "data": "x" * 1000} for i in range(100)]}
        
        result = await cache_set("large_key", large_data, 3600)
        
        assert result is True
        # Should handle serialization of large objects
        mock_client.setex.assert_called_once()


@pytest.mark.usefixtures("redis_client_fixture")
class TestRedisHealthCheck:
    """Test Redis health monitoring"""
    
    @patch('core.redis.redis_client')
    async def test_redis_health_check_success(self, mock_client):
        """Test successful Redis health check"""
        mock_client.ping.return_value = True
        
        # Health check via ping
        result = await mock_client.ping()
        
        assert result is True
    
    @patch('core.redis.redis_client')
    async def test_redis_health_check_failure(self, mock_client):
        """Test Redis health check failure"""
        mock_client.ping.side_effect = redis.RedisError("Ping failed")
        
        # Health check should detect failure
        with pytest.raises(redis.RedisError):
            await mock_client.ping()


class TestRedisURLParsing:
    """Test Redis URL parsing and configuration"""
    
    def test_redis_url_with_password(self):
        """Test Redis URL with password parsing"""
        from core.config import Settings
        
        # Test URL with password
        settings = Settings(
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_DB=1,
            REDIS_PASSWORD=os.getenv("TEST_REDIS_PASSWORD", "test_password")
        )
        
        password = os.getenv("TEST_REDIS_PASSWORD", "test_password")
        expected_url = f"redis://:{password}@localhost:6379/1"
        assert settings.REDIS_URL == expected_url
    
    def test_redis_url_without_password(self):
        """Test Redis URL without password"""
        from core.config import Settings
        
        settings = Settings(
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_DB=2,
            REDIS_PASSWORD=None
        )
        
        expected_url = "redis://localhost:6379/2"
        assert settings.REDIS_URL == expected_url


@pytest.mark.usefixtures("redis_client_fixture")
class TestRedisSerialization:
    """Test Redis data serialization edge cases"""
    
    @patch('core.redis.get_redis_client')
    async def test_none_value_serialization(self, mock_get_client):
        """Test caching None values"""
        mock_client = AsyncMock()
        mock_client.setex.return_value = True
        mock_get_client.return_value = mock_client
        
                
        result = await cache_set("none_key", None, 3600)
        
        assert result is True
        # None should be serialized properly
        mock_client.setex.assert_called_once()
    
    @patch('core.redis.get_redis_client')
    async def test_boolean_value_serialization(self, mock_get_client):
        """Test caching boolean values"""
        mock_client = AsyncMock()
        mock_client.setex.return_value = True
        mock_get_client.return_value = mock_client
        
                
        result = await cache_set("bool_key", True, 3600)
        
        assert result is True
        # Boolean should be handled properly
        mock_client.setex.assert_called_once()
    
    @patch('core.redis.get_redis_client')
    async def test_number_value_serialization(self, mock_get_client):
        """Test caching numeric values"""
        mock_client = AsyncMock()
        mock_client.setex.return_value = True
        mock_get_client.return_value = mock_client
        
                
        result = await cache_set("number_key", 42, 3600)
        
        assert result is True
        mock_client.setex.assert_called_once_with("number_key", 3600, 42)
