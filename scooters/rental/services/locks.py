"""
This module provides a simple lock mechanism using Django's cache backend.
"""
import time

from django.core.cache import cache

def acquire_lock(key:str, ttl_seconds: int = 5) -> bool:
    return cache.add(key, '1', timeout=ttl_seconds)

def release_lock(key:str) -> bool:
    cache.delete(key)


class lock_scope:
    def __init__(self, key:str, ttl_seconds: int = 5):
        self.key = key
        self.ttl= ttl_seconds
        self.acquired = False

    def __enter__(self):
        self.acquired = acquire_lock(self.key, self.ttl)
        return self.acquired

    def __exit__(self, exc_type, exc, tb):
        release_lock(self.key)