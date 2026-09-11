import os
from fastapi import Request

from mnemos.agents import MemoryAgent, ResearchAgent
from mnemos.generator import OpenAIGenerator
from mnemos.config import OpenAIGeneratorConfig, IndexRetrieverConfig, HybridRetrieverConfig, ContextManagerConfig
from mnemos.schemas import AdvancedMemoryStore, InMemoryPageStore
from mnemos.retriever import IndexRetriever, HybridRetriever, AdaptiveContextManager

_memory_store = AdvancedMemoryStore()
_page_store = InMemoryPageStore()

_generator = None
_memory_agent = None
_research_agent = None
_context_manager = None


def init_services():
    global _generator, _memory_agent, _research_agent, _context_manager

    api_key = os.getenv("MNEMOS_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("No API key configured. Set MNEMOS_API_KEY, OPENROUTER_API_KEY, or OPENAI_API_KEY.")
    base_url = os.getenv("MNEMOS_BASE_URL") or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("MNEMOS_MODEL", "google/gemini-3-flash-preview")

    _generator = OpenAIGenerator.from_config(
        OpenAIGeneratorConfig(
            model_name=model_name,
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

    sub_retrievers = {"page_index": index_retriever}

    hybrid_cfg = HybridRetrieverConfig()
    hybrid_retriever = HybridRetriever(
        config={"hybrid": {
            "weights": hybrid_cfg.weights,
            "decay_lambda": hybrid_cfg.decay_lambda,
            "decay_bypass_threshold": hybrid_cfg.decay_bypass_threshold,
            "top_k": hybrid_cfg.top_k,
        }},
        retrievers=sub_retrievers,
        memory_store=_memory_store,
        page_store=_page_store,
    )

    ctx_cfg = ContextManagerConfig()
    _context_manager = AdaptiveContextManager(
        max_tokens=ctx_cfg.max_tokens,
        tiktoken_model=ctx_cfg.tiktoken_model,
        generator=_generator,
        dedup_threshold=ctx_cfg.dedup_threshold,
    )

    retrievers = {"page_index": index_retriever, "hybrid": hybrid_retriever}

    _research_agent = ResearchAgent(
        page_store=_page_store,
        memory_store=_memory_store,
        retrievers=retrievers,
        generator=_generator,
        reranker=None,
        max_iters=3,
        enable_hyde=False,
        enable_self_rag=True,
        context_manager=_context_manager,
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
