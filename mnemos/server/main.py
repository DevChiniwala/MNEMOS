import uvicorn
from fastapi import FastAPI
from prometheus_client import make_asgi_app
from mnemos.server.routes import router
from mnemos.server.deps import init_services
from mnemos.server.metrics import MetricsMiddleware

app = FastAPI(
    title="MNEMOS API Server",
    description="Just-in-time temporal memory system for AI agents.",
    version="0.1.0",
)

# Add Metrics Middleware
app.add_middleware(MetricsMiddleware)

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.on_event("startup")
async def on_startup():
    init_services()

app.include_router(router, prefix="/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}

def run_server(host="0.0.0.0", port=8000):
    uvicorn.run("mnemos.server.main:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    run_server()
