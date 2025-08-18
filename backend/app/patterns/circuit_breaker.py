# app/patterns/circuit_breaker.py
"""
Circuit Breaker Pattern Implementation for ML Model Service

This module implements the circuit breaker pattern to handle failures in
the machine learning model service with automatic recovery and fallback mechanisms.

Circuit Breaker States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is failing, requests are blocked 
- HALF_OPEN: Testing if service has recovered

Features:
- Automatic failure detection and recovery
- Configurable thresholds and timeouts
- Fallback mechanisms for service unavailability
- Comprehensive metrics and monitoring
- Thread-safe implementation
"""

import asyncio
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Callable, Optional, Union
from datetime import datetime, timedelta
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"           # Normal operation
    OPEN = "open"              # Service failing, blocking requests
    HALF_OPEN = "half_open"    # Testing service recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5                    # Failures before opening circuit
    recovery_timeout: float = 60.0               # Seconds before attempting recovery
    success_threshold: int = 3                   # Successes needed to close circuit
    timeout: float = 10.0                        # Request timeout in seconds
    expected_exception: tuple = (Exception,)      # Exceptions that count as failures
    fallback_enabled: bool = True                 # Enable fallback mechanism
    metrics_window_size: int = 100               # Rolling window for metrics


@dataclass
class CircuitBreakerMetrics:
    """Metrics tracking for circuit breaker"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_open_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    average_response_time: float = 0.0
    
    # Rolling window for recent results
    recent_results: list = field(default_factory=list)
    
    def add_result(self, success: bool, response_time: float):
        """Add a result to the metrics"""
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
            self.last_success_time = datetime.now()
        else:
            self.failed_requests += 1
            self.last_failure_time = datetime.now()
        
        # Update average response time
        self.average_response_time = (
            (self.average_response_time * (self.total_requests - 1) + response_time) 
            / self.total_requests
        )
        
        # Maintain rolling window
        self.recent_results.append({
            'success': success,
            'timestamp': datetime.now(),
            'response_time': response_time
        })
        
        # Keep only recent results (last 100 by default)
        if len(self.recent_results) > 100:
            self.recent_results.pop(0)
    
    @property
    def failure_rate(self) -> float:
        """Calculate current failure rate"""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests
    
    @property
    def recent_failure_rate(self) -> float:
        """Calculate failure rate for recent requests"""
        if not self.recent_results:
            return 0.0
        
        recent_failures = sum(1 for r in self.recent_results if not r['success'])
        return recent_failures / len(self.recent_results)


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreakerTimeoutError(Exception):
    """Exception raised when request times out"""
    pass


class CircuitBreaker:
    """
    Circuit Breaker implementation for protecting against cascading failures
    
    This implementation provides:
    - Automatic failure detection
    - Service recovery testing
    - Fallback mechanisms
    - Comprehensive metrics
    - Thread-safe operations
    """
    
    def __init__(self, 
                 name: str,
                 config: Optional[CircuitBreakerConfig] = None,
                 fallback_func: Optional[Callable] = None):
        """
        Initialize circuit breaker
        
        Args:
            name: Unique identifier for this circuit breaker
            config: Configuration parameters
            fallback_func: Function to call when circuit is open
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.fallback_func = fallback_func
        
        # Circuit breaker state
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._lock = threading.RLock()
        
        # Metrics
        self.metrics = CircuitBreakerMetrics()
        
        logger.info(f"Circuit breaker '{name}' initialized with config: {config}")
    
    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit breaker state"""
        return self._state
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)"""
        return self._state == CircuitBreakerState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)"""
        return self._state == CircuitBreakerState.OPEN
    
    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)"""
        return self._state == CircuitBreakerState.HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or fallback result
            
        Raises:
            CircuitBreakerError: When circuit is open and no fallback
            CircuitBreakerTimeoutError: When request times out
        """
        with self._lock:
            # Check if we should attempt the call
            if not self._should_attempt_call():
                return self._handle_blocked_call(func, *args, **kwargs)
            
            # Execute the call with timeout and error handling
            start_time = time.time()
            try:
                result = self._execute_with_timeout(func, *args, **kwargs)
                response_time = time.time() - start_time
                
                self._record_success(response_time)
                return result
                
            except self.config.expected_exception as e:
                response_time = time.time() - start_time
                self._record_failure(response_time, e)
                
                # Try fallback if available
                if self.fallback_func:
                    logger.warning(f"Circuit breaker '{self.name}' calling fallback due to: {e}")
                    return self.fallback_func(*args, **kwargs)
                else:
                    raise
    
    def _should_attempt_call(self) -> bool:
        """Determine if we should attempt the call based on current state"""
        if self._state == CircuitBreakerState.CLOSED:
            return True
        
        elif self._state == CircuitBreakerState.OPEN:
            # Check if enough time has passed to try recovery
            if (self._last_failure_time and 
                time.time() - self._last_failure_time >= self.config.recovery_timeout):
                self._state = CircuitBreakerState.HALF_OPEN
                self._success_count = 0
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN for recovery test")
                return True
            return False
        
        elif self._state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    def _handle_blocked_call(self, func: Callable, *args, **kwargs) -> Any:
        """Handle calls when circuit is open"""
        logger.warning(f"Circuit breaker '{self.name}' is OPEN, blocking call to {func.__name__}")
        
        if self.fallback_func:
            logger.info(f"Circuit breaker '{self.name}' using fallback function")
            return self.fallback_func(*args, **kwargs)
        else:
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is open. Service is currently unavailable."
            )
    
    def _execute_with_timeout(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with timeout protection"""
        if asyncio.iscoroutinefunction(func):
            # Handle async functions
            return asyncio.wait_for(
                func(*args, **kwargs), 
                timeout=self.config.timeout
            )
        else:
            # Handle sync functions with thread-based timeout
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=self.config.timeout)
            
            if thread.is_alive():
                # Timeout occurred
                raise CircuitBreakerTimeoutError(
                    f"Function call timed out after {self.config.timeout} seconds"
                )
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
    
    def _record_success(self, response_time: float):
        """Record successful call"""
        self.metrics.add_result(success=True, response_time=response_time)
        
        if self._state == CircuitBreakerState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._state = CircuitBreakerState.CLOSED
                self._failure_count = 0
                logger.info(f"Circuit breaker '{self.name}' recovered, transitioning to CLOSED")
        
        elif self._state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self._failure_count = max(0, self._failure_count - 1)
    
    def _record_failure(self, response_time: float, exception: Exception):
        """Record failed call"""
        self.metrics.add_result(success=False, response_time=response_time)
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        logger.warning(f"Circuit breaker '{self.name}' recorded failure: {exception}")
        
        if self._state == CircuitBreakerState.HALF_OPEN:
            # Return to open state on failure during recovery
            self._state = CircuitBreakerState.OPEN
            self.metrics.circuit_open_count += 1
            logger.warning(f"Circuit breaker '{self.name}' recovery failed, returning to OPEN")
        
        elif (self._state == CircuitBreakerState.CLOSED and 
              self._failure_count >= self.config.failure_threshold):
            # Transition to open state
            self._state = CircuitBreakerState.OPEN
            self.metrics.circuit_open_count += 1
            logger.error(f"Circuit breaker '{self.name}' OPENED after {self._failure_count} failures")
    
    def reset(self):
        """Manually reset circuit breaker to closed state"""
        with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")
    
    def force_open(self):
        """Manually force circuit breaker to open state"""
        with self._lock:
            self._state = CircuitBreakerState.OPEN
            self._last_failure_time = time.time()
            self.metrics.circuit_open_count += 1
            logger.warning(f"Circuit breaker '{self.name}' manually forced to OPEN")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information"""
        return {
            'name': self.name,
            'state': self._state.value,
            'failure_count': self._failure_count,
            'success_count': self._success_count,
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'recovery_timeout': self.config.recovery_timeout,
                'success_threshold': self.config.success_threshold,
                'timeout': self.config.timeout,
            },
            'metrics': {
                'total_requests': self.metrics.total_requests,
                'successful_requests': self.metrics.successful_requests,
                'failed_requests': self.metrics.failed_requests,
                'failure_rate': self.metrics.failure_rate,
                'recent_failure_rate': self.metrics.recent_failure_rate,
                'average_response_time': self.metrics.average_response_time,
                'circuit_open_count': self.metrics.circuit_open_count,
                'last_failure_time': self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
                'last_success_time': self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
            }
        }


def circuit_breaker(name: str, 
                   config: Optional[CircuitBreakerConfig] = None,
                   fallback_func: Optional[Callable] = None):
    """
    Decorator for applying circuit breaker pattern to functions
    
    Args:
        name: Unique identifier for this circuit breaker
        config: Configuration parameters
        fallback_func: Function to call when circuit is open
    """
    def decorator(func: Callable):
        breaker = CircuitBreaker(name, config, fallback_func)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        # Attach circuit breaker to function for external access
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator


# Global registry for circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """Get circuit breaker by name"""
    return _circuit_breakers.get(name)


def register_circuit_breaker(breaker: CircuitBreaker):
    """Register a circuit breaker in the global registry"""
    _circuit_breakers[breaker.name] = breaker


def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """Get all registered circuit breakers"""
    return _circuit_breakers.copy()


def get_circuit_breaker_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all circuit breakers"""
    return {name: breaker.get_status() for name, breaker in _circuit_breakers.items()}
