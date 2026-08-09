"""
Métricas e Monitoramento - Nex.spec.md Seção 4
Thread-safe metrics middleware
"""

import time
import threading
import asyncio
from typing import Dict, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


_psutil_available = False
try:
    import psutil
    _psutil_available = True
except ImportError:
    pass


class Metrics:
    """Thread-safe metrics collector"""
    
    def __init__(self):
        self._lock = threading.RLock()
        
        self._requests_total = 0
        self._active_connections = 0
        self._avg_latency_ms = 0.0
        self._peak_memory_mb = 0.0
        
        # Fallback metrics
        self._fallback_counts = {
            "openrouter_to_llama": 0,
            "openrouter_to_huggingface": 0,
            "llama_to_huggingface": 0,
        }
        self._llm_fallback_total = 0
        self._llm_fallback_reasons = {}
        
        self._alpha = 0.1  # Exponential moving average factor
    
    def increment_requests(self):
        """Increment total requests"""
        with self._lock:
            self._requests_total += 1
    
    def increment_connections(self):
        """Increment active connections"""
        with self._lock:
            self._active_connections += 1
    
    def decrement_connections(self):
        """Decrement active connections"""
        with self._lock:
            self._active_connections = max(0, self._active_connections - 1)
    
    def update_latency(self, latency_ms: float):
        """Update average latency (exponential moving average)"""
        with self._lock:
            if self._avg_latency_ms == 0:
                self._avg_latency_ms = latency_ms
            else:
                self._avg_latency_ms = (
                    self._alpha * latency_ms + 
                    (1 - self._alpha) * self._avg_latency_ms
                )
    
    def update_memory(self):
        """Update peak memory usage"""
        with self._lock:
            if _psutil_available:
                try:
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / (1024 ** 2)
                    self._peak_memory_mb = max(self._peak_memory_mb, memory_mb)
                except:
                    pass
    
    def get_metrics(self) -> Dict:
        """Get all metrics as dictionary"""
        with self._lock:
            return {
                "requests_total": self._requests_total,
                "active_connections": self._active_connections,
                "avg_latency_ms": round(self._avg_latency_ms, 2),
                "peak_memory_mb": round(self._peak_memory_mb, 2),
                "fallback_counts": dict(self._fallback_counts),
                "llm_fallback_total": self._llm_fallback_total,
                "llm_fallback_reasons": dict(self._llm_fallback_reasons),
            }
    
    def record_fallback(self, from_backend: str, to_backend: str, reason: Optional[str] = None):
        """Record a fallback event"""
        key = f"{from_backend}_to_{to_backend}"
        with self._lock:
            self._llm_fallback_total += 1
            if reason:
                self._llm_fallback_reasons[reason] = self._llm_fallback_reasons.get(reason, 0) + 1
            if key in self._fallback_counts:
                self._fallback_counts[key] += 1
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self._requests_total = 0
            self._active_connections = 0
            self._avg_latency_ms = 0.0
            self._peak_memory_mb = 0.0
            self._fallback_counts = {
                "openrouter_to_llama": 0,
                "openrouter_to_huggingface": 0,
                "llama_to_huggingface": 0,
            }
            self._llm_fallback_total = 0
            self._llm_fallback_reasons = {}


# Global metrics instance
metrics = Metrics()


class MetricsMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for collecting metrics"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        
        metrics.increment_requests()
        
        try:
            response = await call_next(request)
            return response
        finally:
            # Calculate latency
            latency_ms = (time.perf_counter() - start_time) * 1000
            metrics.update_latency(latency_ms)
            metrics.update_memory()


def get_metrics() -> Dict:
    """Get current metrics (exported for health endpoint)"""
    return metrics.get_metrics()


def reset_metrics():
    """Reset metrics (for testing)"""
    metrics.reset()
