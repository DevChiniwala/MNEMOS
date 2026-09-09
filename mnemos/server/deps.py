import os
from fastapi import Request

from mnemos.agents import MemoryAgent, ResearchAgent
from mnemos.generator import OpenAIGenerator
from mnemos.config import OpenAIGeneratorConfig, IndexRetrieverConfig
from mnemos.schemas import AdvancedMemoryStore, InMemoryPageStore
from mnemos.retriever import IndexRetriever

# Simple global state for the single-node server instance
_memory_store = AdvancedMemoryStore()
_page_store = InMemoryPageStore()

_generator = None
_memory_agent = None
_research_agent = None

def init_services():
    global _generator, _memory_agent, _research_agent
    
    api_key = os.getenv("OPENROUTER_API_KEY", os.getenv("OPENAI_API_KEY", "mock-key"))
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    _generator = OpenAIGenerator.from_config(
        OpenAIGeneratorConfig(
            model_name="google/gemini-3-flash-preview",
            api_key=api_key,
            base_url=base_url,
            temperature=0.0,
            max_tokens=1024,
        )
    )
    
    _memory_agent = MemoryAgent(
        generator=_generator,
        memory_store=_memory_store,
        page_store=_page_store,
    )
    
    index_retriever = IndexRetriever(IndexRetrieverConfig(index_dir="./index/index").__dict__)
    index_retriever.build(_page_store)
    
    retrievers = {"page_index": index_retriever}
    
    _research_agent = ResearchAgent(
        page_store=_page_store,
        memory_store=_memory_store,
        retrievers=retrievers,
        generator=_generator,
        reranker=None,
        max_iters=3,
        enable_hyde=False,
        enable_self_rag=True,
    )

def get_memory_agent() -> MemoryAgent:
    if _memory_agent is None:
        init_services()
    return _memory_agent

def get_research_agent() -> ResearchAgent:
    if _research_agent is None:
        init_services()
    return _research_agent

def get_memory_store() -> AdvancedMemoryStore:
    return _memory_store
