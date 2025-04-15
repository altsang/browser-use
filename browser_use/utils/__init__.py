"""
Utility functions for browser-use.
"""
import asyncio
import functools
import logging
import os
import time
from typing import Any, Callable, TypeVar, Awaitable, Type, cast, List

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')

def time_execution_sync(name: str) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator to time the execution of a synchronous function.
    
    Args:
        name (str): Name to use in the log message.
        
    Returns:
        Callable: Decorated function.
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                duration = end_time - start_time
                logger.debug(f"{name} took {duration:.4f} seconds")
        return wrapper
    return decorator

def time_execution_async(name: str) -> Callable[[Callable[..., Awaitable[R]]], Callable[..., Awaitable[R]]]:
    """
    Decorator to time the execution of an asynchronous function.
    
    Args:
        name (str): Name to use in the log message.
        
    Returns:
        Callable: Decorated function.
    """
    def decorator(func: Callable[..., Awaitable[R]]) -> Callable[..., Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> R:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                duration = end_time - start_time
                logger.debug(f"{name} took {duration:.4f} seconds")
        return wrapper
    return decorator

def singleton(cls: Type[T]) -> Type[T]:
    """
    Decorator to create a singleton class.
    
    Args:
        cls: The class to make a singleton.
        
    Returns:
        The singleton class.
    """
    instances = {}
    
    @functools.wraps(cls)
    def get_instance(*args: Any, **kwargs: Any) -> T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return cast(T, instances[cls])
    
    return cast(Type[T], get_instance)

def check_env_variables(keys: List[str], any_or_all=all) -> bool:
    """
    Check if required environment variables are set.
    
    Args:
        keys: List of environment variable names to check.
        any_or_all: Function to use for checking (all or any).
        
    Returns:
        bool: True if the required environment variables are set, False otherwise.
    """
    return any_or_all(os.getenv(key) and os.getenv(key).strip() for key in keys)
