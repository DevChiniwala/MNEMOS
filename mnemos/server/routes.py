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
        # Our memory agent's memorize method
        result = agent.memorize(req.text, user_id=req.user_id)
        # We need to map the result
        # Assuming memorize returns a MemoryEntry or similar.
        return MemorizeResponse(
            status="SUCCESS",
            memory_id=getattr(result, "id", None) if result else None,
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
            sources=list(out.raw_memory.keys())
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memories", response_model=dict)
async def list_memories(
    store: AdvancedMemoryStore = Depends(get_memory_store)
):
    # Returns all active memories
    active = store.get_active_entries()
    return {"memories": [m.model_dump() for m in active]}

@router.get("/memories/{memory_id}")
async def explain_memory(
    memory_id: str,
    store: AdvancedMemoryStore = Depends(get_memory_store)
):
    entry = store.get_entry(memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Memory not found.")
    
    history = store.get_version_history(memory_id)
    return {
        "memory_id": memory_id,
        "content": entry.content,
        "status": entry.status.value,
        "history": [h.model_dump() for h in history]
    }
