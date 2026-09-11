# -*- coding: utf-8 -*-
"""
Mnemos Framework

A dual-agent architecture for building long-term memory with deep research capabilities.

Key Components:
- MemoryAgent: Builds structured memory from raw messages
- ResearchAgent: Performs multi-iteration research with reflection
"""

from __future__ import annotations

# Core agents
from mnemos.agents import MemoryAgent, ResearchAgent

# Generators
from mnemos.generator import AbsGenerator, OpenAIGenerator, VLLMGenerator

# Retrievers
from mnemos.retriever import AbsRetriever, IndexRetriever, GraphRetriever, HybridRetriever, AdaptiveContextManager

# Try to import optional retrievers
try:
    from mnemos.retriever import BM25Retriever
except ImportError:
    BM25Retriever = None  # type: ignore

try:
    from mnemos.retriever import DenseRetriever
except ImportError:
    DenseRetriever = None  # type: ignore

try:
    from mnemos.retriever import CohereDenseRetriever, CohereReranker
except ImportError:
    CohereDenseRetriever = None  # type: ignore
    CohereReranker = None  # type: ignore

# Configurations
from mnemos.config import (
    OpenAIGeneratorConfig,
    VLLMGeneratorConfig,
    DenseRetrieverConfig,
    BM25RetrieverConfig,
    IndexRetrieverConfig,
    CohereEmbedRetrieverConfig,
    CohereRerankerConfig,
    HybridRetrieverConfig,
    ContextManagerConfig,
)

# Schemas
from mnemos.schemas import (
    MemoryState,
    AdvancedMemoryStore,
    AdvancedMemoryState,
    MemoryEntry,
    Page,
    MemoryUpdate,
    SearchPlan,
    Hit,
    Result,
    EnoughDecision,
    ReflectionDecision,
    ResearchOutput,
    InMemoryMemoryStore,
    InMemoryPageStore,
    TTLMemoryStore,
    TTLMemoryState,
    TTLMemoryEntry,
    TTLPageStore,
)
try:
    from mnemos.graph import GraphMemoryStore, GraphOntology
except ImportError:
    GraphMemoryStore = None  # type: ignore
    GraphOntology = None  # type: ignore
from mnemos.ingestion import (
    Document,
    Chunk,
    BaseChunker,
    SimpleChunker,
    ChunkingConfig,
    BaseLoader,
    TextFileLoader,
    DirectoryLoader,
    URLLoader,
    JSONLLoader,
    S3Loader,
    NotionLoader,
    GDriveLoader,
    IngestionPipeline,
    ECLPipeline,
)
from mnemos.profile import UserProfile, UserProfileStore, UserProfileAgent
try:
    from mnemos.summarization import HierarchicalSummarizer
except ImportError:
    HierarchicalSummarizer = None  # type: ignore
try:
    from mnemos.maintenance import MemoryConsolidator
except ImportError:
    MemoryConsolidator = None  # type: ignore

try:
    from mnemos.maintenance import SleepConsolidationJob
except ImportError:
    SleepConsolidationJob = None  # type: ignore

try:
    from mnemos.affect.salience import EmotionalSalienceScorer, FadingAffectModel
except ImportError:
    EmotionalSalienceScorer = None  # type: ignore
    FadingAffectModel = None  # type: ignore

try:
    from mnemos.reinforcement.fsrs import SpacedRepetitionScheduler
except ImportError:
    SpacedRepetitionScheduler = None  # type: ignore

try:
    from mnemos.modalities.images import ImageMemoryProcessor
except ImportError:
    ImageMemoryProcessor = None  # type: ignore

from mnemos.utils import CheckpointManager
from mnemos.learning import ExperienceReplayBuffer
try:
    from mnemos.evaluation import RAGASEvaluator
except Exception:
    RAGASEvaluator = None  # type: ignore

__version__ = "0.1.0"
__all__ = [
    # Core agents
    "MemoryAgent",
    "ResearchAgent",
    
    # Generators
    "AbsGenerator",
    "OpenAIGenerator",
    "VLLMGenerator",
    
    # Retrievers
    "AbsRetriever",
    "IndexRetriever",
    "BM25Retriever",
    "DenseRetriever",
    "CohereDenseRetriever",
    "CohereReranker",
    "GraphRetriever",
    
    # Configurations
    "OpenAIGeneratorConfig",
    "VLLMGeneratorConfig",
    "DenseRetrieverConfig",
    "BM25RetrieverConfig",
    "IndexRetrieverConfig",
    "CohereEmbedRetrieverConfig",
    "CohereRerankerConfig",
    "HybridRetrieverConfig",
    "ContextManagerConfig",
    "HybridRetriever",
    "AdaptiveContextManager",
    "ECLPipeline",

    # Schemas
    "MemoryState",
    "AdvancedMemoryStore",
    "AdvancedMemoryState",
    "MemoryEntry",
    "Page",
    "MemoryUpdate",
    "SearchPlan",
    "Hit",
    "Result",
    "EnoughDecision",
    "ReflectionDecision",
    "ResearchOutput",
    "InMemoryMemoryStore",
    "InMemoryPageStore",
    "TTLMemoryStore",
    "TTLMemoryState",
    "TTLMemoryEntry",
    "TTLPageStore",
    "GraphMemoryStore",
    "GraphOntology",
    "Document",
    "Chunk",
    "BaseChunker",
    "SimpleChunker",
    "ChunkingConfig",
    "BaseLoader",
    "TextFileLoader",
    "DirectoryLoader",
    "URLLoader",
    "JSONLLoader",
    "S3Loader",
    "NotionLoader",
    "GDriveLoader",
    "IngestionPipeline",
    "UserProfile",
    "UserProfileStore",
    "UserProfileAgent",
    "HierarchicalSummarizer",
    "MemoryConsolidator",
    "SleepConsolidationJob",
    "EmotionalSalienceScorer",
    "FadingAffectModel",
    "SpacedRepetitionScheduler",
    "ImageMemoryProcessor",
    "CheckpointManager",
    "ExperienceReplayBuffer",
    "RAGASEvaluator",
]
