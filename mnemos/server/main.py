import uvicorn
from fastapi import FastAPI
from mnemos.server.routes import router
from mnemos.server.deps import init_services

app = FastAPI(
    title="MNEMOS API Server",
    description="Just-in-time temporal memory system for AI agents.",
    version="0.1.0",
)

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
