"""
Signal handler utility for browser-use.
"""
import logging
import signal
import sys
import time
from typing import Callable, Dict, Optional, Set

logger = logging.getLogger(__name__)

class SignalHandler:
    """
    Utility class to handle signals.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SignalHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, loop=None, pause_callback=None, resume_callback=None, 
                 custom_exit_callback=None, exit_on_second_int=False):
        if self._initialized:
            return
            
        self._initialized = True
        self._loop = loop
        self._pause_callback = pause_callback
        self._resume_callback = resume_callback
        self._custom_exit_callback = custom_exit_callback
        self._exit_on_second_int = exit_on_second_int
        self._last_sigint_time = 0
        self._handlers: Dict[int, Set[Callable[[], None]]] = {}
        self._original_handlers: Dict[int, Optional[Callable]] = {}
        
        for sig in [signal.SIGINT, signal.SIGTERM]:
            self._original_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, self._handle_signal)
            self._handlers[sig] = set()
    
    def register(self, sig: int = None, handler: Callable[[], None] = None) -> None:
        """
        Register a handler for a signal.
        
        Args:
            sig: Signal number. If None, registers for SIGINT and SIGTERM.
            handler: Handler function. If None, uses internal callbacks.
        """
        if sig is None:
            for sig_type in [signal.SIGINT, signal.SIGTERM]:
                if sig_type not in self._handlers:
                    self._handlers[sig_type] = set()
                    self._original_handlers[sig_type] = signal.getsignal(sig_type)
                    signal.signal(sig_type, self._handle_signal)
            return
            
        if sig not in self._handlers:
            self._handlers[sig] = set()
            self._original_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, self._handle_signal)
            
        if handler:
            self._handlers[sig].add(handler)
    
    def unregister(self, sig: int = None, handler: Callable[[], None] = None) -> None:
        """
        Unregister a handler for a signal.
        
        Args:
            sig: Signal number. If None, unregisters all handlers.
            handler: Handler function. If None, unregisters all handlers for the given signal.
        """
        if sig is None and handler is None:
            for sig_type in list(self._handlers.keys()):
                if sig_type in self._original_handlers:
                    signal.signal(sig_type, self._original_handlers[sig_type])
            self._handlers.clear()
            return
            
        if handler is None and sig in self._handlers:
            if sig in self._original_handlers:
                signal.signal(sig, self._original_handlers[sig])
                del self._handlers[sig]
                del self._original_handlers[sig]
            return
            
        if sig in self._handlers and handler in self._handlers[sig]:
            self._handlers[sig].remove(handler)
            
            if not self._handlers[sig] and sig in self._original_handlers:
                signal.signal(sig, self._original_handlers[sig])
                del self._handlers[sig]
                del self._original_handlers[sig]
    
    def _handle_signal(self, sig, frame):
        """
        Handle a signal by calling all registered handlers.
        
        Args:
            sig: Signal number.
            frame: Current stack frame.
        """
        logger.debug(f"Received signal {sig}")
        
        if sig == signal.SIGINT:
            current_time = time.time()
            
            if self._exit_on_second_int and current_time - self._last_sigint_time < 2.0:
                logger.info("Received second SIGINT within 2 seconds, exiting...")
                sys.exit(1)
                
            self._last_sigint_time = current_time
            
            if self._pause_callback and callable(self._pause_callback):
                try:
                    self._pause_callback()
                    return  # Don't propagate the signal further
                except Exception as e:
                    logger.error(f"Error in pause callback: {e}")
        
        if sig == signal.SIGTERM and self._custom_exit_callback and callable(self._custom_exit_callback):
            try:
                self._custom_exit_callback()
            except Exception as e:
                logger.error(f"Error in custom exit callback: {e}")
        
        if sig in self._handlers:
            for handler in self._handlers[sig]:
                try:
                    handler()
                except Exception as e:
                    logger.error(f"Error in signal handler: {e}")
        
        original = self._original_handlers.get(sig)
        if callable(original) and original not in (signal.SIG_IGN, signal.SIG_DFL):
            original(sig, frame)
        elif original == signal.SIG_DFL:
            if sig == signal.SIGINT:
                raise KeyboardInterrupt()
            elif sig == signal.SIGTERM:
                sys.exit(0)
