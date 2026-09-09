from fastapi import APIRouter, Depends, HTTPException
from mnemos.server.models import (
    MemorizeRequest, MemorizeResponse,
    ResearchRequest, ResearchResponse,
    ExplainResponse
)
from mnemos.server.deps import get_memory_agent, get_research_agent, get_memory_store
from mnemos.agents import MemoryAgent, ResearchAgent
from mnemos.schemas.advanced_memory import AdvancedMemoryStore

router = APIRouter()

@router.post("/memories", response_model=MemorizeResponse)
async def memorize_fact(
    req: MemorizeRequest,
    agent: MemoryAgent = Depends(get_memory_agent)
):
    try:
        result = agent.memorize(req.text, meta=req.metadata, user_id=req.user_id)
        memory_id = None
        if result and result.new_page:
            memory_id = result.new_page.meta.get("memory_id")
        op = result.debug.get("operation", "NOOP") if result and result.debug else "NOOP"
        return MemorizeResponse(
            status=op,
            memory_id=memory_id,
            message="Fact processed successfully."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/research", response_model=ResearchResponse)
async def research_topic(
    req: ResearchRequest,
    agent: ResearchAgent = Depends(get_research_agent)
):
    try:
        out = agent.research(request=req.question, user_id=req.user_id)
        return ResearchResponse(
            answer=out.integrated_memory,
            sources=list(out.raw_memory.keys()) if isinstance(out.raw_memory, dict) else []
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memories", response_model=dict)
async def list_memories(
    store: AdvancedMemoryStore = Depends(get_memory_store)
):
    active = store.get_entries(include_inactive=False)
    return {"memories": [m.model_dump() for m in active]}

@router.get("/memories/{memory_id}")
async def explain_memory(
    memory_id: str,
    store: AdvancedMemoryStore = Depends(get_memory_store)
):
    entry = store.get_entry_by_id(memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Memory not found.")

    history = store.get_version_history(memory_id)
    return {
        "memory_id": memory_id,
        "content": entry.content,
        "status": entry.status,
        "history": [h.model_dump() for h in history]
    }

@router.delete("/users/{user_id}/erase")
async def erase_user_data(
    user_id: str,
    store: AdvancedMemoryStore = Depends(get_memory_store)
):
    try:
        from mnemos.privacy.erasure import ErasureEngine
        engine = ErasureEngine(store)
        deleted = engine.erase_user_data("admin", user_id)
        return {
            "status": "SUCCESS",
            "target_user_id": user_id,
            "items_deleted": deleted
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
