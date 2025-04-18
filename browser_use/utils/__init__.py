"""
Utility functions for browser-use.
"""
import functools
import logging
import time
from typing import Any, Callable, TypeVar

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
