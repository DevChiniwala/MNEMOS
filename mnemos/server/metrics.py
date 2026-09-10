import time
from prometheus_client import Counter, Histogram, Gauge
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Metrics
REQUEST_COUNT = Counter("mnemos_api_requests_total", "Total API requests", ["method", "endpoint", "status_code"])
REQUEST_LATENCY = Histogram("mnemos_api_latency_seconds", "API request latency", ["endpoint"])
MEMORY_COUNT = Gauge("mnemos_active_memories", "Number of active memories in the system")

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        route_path = request.url.path
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            raise e
        finally:
            elapsed = time.time() - start_time
            REQUEST_COUNT.labels(method=request.method, endpoint=route_path, status_code=status_code).inc()
            REQUEST_LATENCY.labels(endpoint=route_path).observe(elapsed)
            
        return response

def update_memory_gauge(count: int):
    """Updates the active memory count gauge."""
    MEMORY_COUNT.set(count)
