"""
Caching system for Clintra to improve performance.
"""
import json
import hashlib
import time
from typing import Any, Optional, Dict
from functools import wraps
import logging

logger = logging.getLogger("clintra.cache")

class MemoryCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry['expires']:
                logger.debug(f"Cache hit for key: {key}")
                return entry['value']
            else:
                # Expired, remove it
                del self.cache[key]
                logger.debug(f"Cache expired for key: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }
        logger.debug(f"Cache set for key: {key}, TTL: {ttl}s")
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Cache deleted for key: {key}")
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        logger.debug("Cache cleared")
    
    def cleanup_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time >= entry['expires']
        ]
        for key in expired_keys:
            del self.cache[key]
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

# Global cache instance
cache = MemoryCache(default_ttl=300)

def cached(prefix: str, ttl: int = 300):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def cache_search_results(query: str, results: Any, ttl: int = 600) -> None:
    """Cache search results."""
    key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
    cache.set(key, results, ttl)

def get_cached_search_results(query: str) -> Optional[Any]:
    """Get cached search results."""
    key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
    return cache.get(key)

def cache_compound_data(compound_name: str, data: Any, ttl: int = 1800) -> None:
    """Cache compound data."""
    key = f"compound:{hashlib.md5(compound_name.lower().encode()).hexdigest()}"
    cache.set(key, data, ttl)

def get_cached_compound_data(compound_name: str) -> Optional[Any]:
    """Get cached compound data."""
    key = f"compound:{hashlib.md5(compound_name.lower().encode()).hexdigest()}"
    return cache.get(key)

def cache_protein_data(pdb_id: str, data: Any, ttl: int = 3600) -> None:
    """Cache protein data."""
    key = f"protein:{pdb_id.upper()}"
    cache.set(key, data, ttl)

def get_cached_protein_data(pdb_id: str) -> Optional[Any]:
    """Get cached protein data."""
    key = f"protein:{pdb_id.upper()}"
    return cache.get(key)

def cache_graph_data(query: str, graph_type: str, data: Any, ttl: int = 900) -> None:
    """Cache graph generation data."""
    key = f"graph:{hashlib.md5(f'{query}:{graph_type}'.encode()).hexdigest()}"
    cache.set(key, data, ttl)

def get_cached_graph_data(query: str, graph_type: str) -> Optional[Any]:
    """Get cached graph data."""
    key = f"graph:{hashlib.md5(f'{query}:{graph_type}'.encode()).hexdigest()}"
    return cache.get(key)

def invalidate_search_cache(query: str = None) -> None:
    """Invalidate search cache."""
    if query:
        key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
        cache.delete(key)
    else:
        # Clear all search cache entries
        keys_to_delete = [key for key in cache.cache.keys() if key.startswith('search:')]
        for key in keys_to_delete:
            cache.delete(key)

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    current_time = time.time()
    total_entries = len(cache.cache)
    expired_entries = sum(
        1 for entry in cache.cache.values()
        if current_time >= entry['expires']
    )
    
    return {
        "total_entries": total_entries,
        "active_entries": total_entries - expired_entries,
        "expired_entries": expired_entries,
        "cache_size_mb": sum(
            len(json.dumps(entry['value']).encode()) 
            for entry in cache.cache.values()
        ) / (1024 * 1024)
    }

