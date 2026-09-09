from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class MemorizeRequest(BaseModel):
    text: str = Field(..., description="The raw text or fact to memorize.")
    user_id: Optional[str] = Field(default="default", description="Namespace/User for this memory.")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata.")

class MemorizeResponse(BaseModel):
    status: str = Field(..., description="Operation result (e.g. ADD, UPDATE, SUPERSEDE, NOOP)")
    memory_id: Optional[str] = Field(None, description="The ID of the new memory entry if created.")
    message: str = Field(..., description="Human readable result.")

class ResearchRequest(BaseModel):
    question: str = Field(..., description="The query to research.")
    user_id: Optional[str] = Field(default="default", description="Namespace/User context.")
    max_iters: int = Field(default=3, description="Maximum research loop iterations.")

class ResearchResponse(BaseModel):
    answer: str = Field(..., description="The final integrated answer.")
    sources: List[str] = Field(default_factory=list, description="List of source memory IDs used.")

class ExplainRequest(BaseModel):
    memory_id: str

class ExplainResponse(BaseModel):
    memory_id: str
    content: str
    provenance: List[Dict[str, Any]]
