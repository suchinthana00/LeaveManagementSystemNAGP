from pybreaker import CircuitBreaker


gateway_breaker = CircuitBreaker(fail_max=3, reset_timeout=30)
