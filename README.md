<div align="center">

<br/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/final_svgs/01_system_overview.svg"/>
  <img alt="MNEMOS System Overview" src="assets/readme/final_svgs/01_system_overview.svg" width="100%"/>
</picture>

<br/>

# MNEMOS

### Just-in-time memory system for AI agents

Self-editing bi-temporal memory · hybrid 6-signal retrieval fusion · temporal graph reasoning
Plan → Search → Integrate → Reflect loop for evidence-grounded answers

<br/>

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-22C55E.svg?style=for-the-badge)](LICENSE)
[![Status: Research](https://img.shields.io/badge/status-research-7C3AED.svg?style=for-the-badge)]()

[![Memory: Self-Editing](https://img.shields.io/badge/memory-self--editing-0EA5A0.svg?style=flat-square)](#self-editing-memory)
[![Time: Bi-Temporal](https://img.shields.io/badge/time-bi--temporal-F59E0B.svg?style=flat-square)](#bi-temporal-model)
[![Graph: Temporal Reasoning](https://img.shields.io/badge/graph-temporal%20reasoning-6366F1.svg?style=flat-square)](#graph-memory)
[![Retrieval: 6-Signal Hybrid](https://img.shields.io/badge/retrieval-6--signal%20hybrid-EF4444.svg?style=flat-square)](#hybrid-retriever)
[![Context: Adaptive Packing](https://img.shields.io/badge/context-adaptive%20packing-3B82F6.svg?style=flat-square)](#adaptive-context)
[![Ingestion: ECL Pipeline](https://img.shields.io/badge/ingestion-ECL%20pipeline-10B981.svg?style=flat-square)](#ecl-pipeline)
[![Loop: Plan-Search-Integrate-Reflect](https://img.shields.io/badge/loop-PSIR-0F172A.svg?style=flat-square)](#research-loop)

<br/>

**Author:** [Dev Chiniwala](https://github.com/DevChiniwala)

<br/>

</div>

---

## Why MNEMOS

Most AI memory systems fail gradually because they only append (stale facts persist), ignore temporal validity (wrong answers at the wrong time), or optimize one retrieval mode (fragile on diverse queries).

MNEMOS directly addresses all three:

| Failure Mode | MNEMOS Solution |
|:---|:---|
| Stale facts persist forever | **Self-editing lifecycle** — ADD, UPDATE, DELETE, NOOP on every write |
| No temporal validity | **Bi-temporal model** — `t_created`, `t_observed`, `t_valid`, `t_invalid`, `t_expired` |
| Single retrieval mode | **6-signal hybrid fusion** — semantic + lexical + graph + time decay + cognitive + tier |
| Context window waste | **Adaptive context packing** — tiktoken-precise budgets with trigram dedup |
| Raw ingestion | **ECL pipeline** — enriches memories with salience + FSRS at write-time |

---

## Visual Architecture

<p align="center">
  <img src="assets/readme/root_readme_images/01_mnemos_graph_memory_overview.png" alt="Graph Memory Overview" width="32%"/>
  <img src="assets/readme/root_readme_images/02_mnemos_temporal_validity_panel.png" alt="Temporal Validity" width="32%"/>
  <img src="assets/readme/root_readme_images/03_mnemos_retrieval_fusion_panel.png" alt="Retrieval Fusion" width="32%"/>
</p>

<p align="center">
  <img src="assets/readme/root_readme_images/04_mnemos_self_editing_lifecycle.png" alt="Self-Editing Lifecycle" width="32%"/>
  <img src="assets/readme/root_readme_images/05_mnemos_hierarchical_memory_tiers.png" alt="Hierarchical Tiers" width="32%"/>
  <img src="assets/readme/root_readme_images/06_mnemos_production_readiness_dashboard.png" alt="Production Readiness" width="32%"/>
</p>

---

## Table of Contents

- [Why MNEMOS](#why-mnemos)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
  - [Self-Editing Memory](#self-editing-memory)
  - [Bi-Temporal Model](#bi-temporal-model)
  - [Hierarchical Tiers & Decay](#hierarchical-tiers--decay)
- [Architecture](#architecture)
  - [Dual-Agent Design](#dual-agent-design)
  - [Research Loop](#research-loop)
  - [HybridRetriever — 6-Signal Scoring](#hybrid-retriever)
  - [AdaptiveContextManager](#adaptive-context)
  - [ECL Pipeline](#ecl-pipeline)
  - [Graph Memory](#graph-memory)
- [Interface Reference](#interface-reference)
- [Configuration](#configuration)
- [Repository Structure](#repository-structure)
- [Evaluation & Testing](#evaluation--testing)
- [Architecture SVGs](#architecture-svgs)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Quick Start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e . && pip install -r requirements.txt
```

```bash
export OPENROUTER_API_KEY="..."
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
export COHERE_API_KEY="..."
```

```python
from mnemos import (
    MemoryAgent, ResearchAgent, OpenAIGenerator,
    OpenAIGeneratorConfig, AdvancedMemoryStore, InMemoryPageStore,
    IndexRetriever, IndexRetrieverConfig,
)
import os

# Generator
generator = OpenAIGenerator.from_config(OpenAIGeneratorConfig(
    model_name="google/gemini-3-flash-preview",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
))

# Stores
memory_store = AdvancedMemoryStore()
page_store = InMemoryPageStore()

# Write memories
agent = MemoryAgent(generator=generator, memory_store=memory_store, page_store=page_store)
result = agent.memorize("The project deadline is March 15th.", memory_store, page_store)
memory_id = result.new_page.meta.get("memory_id")

# Research (retrieve + reason)
retriever = IndexRetriever(IndexRetrieverConfig(index_dir="./index").__dict__)
retriever.build(page_store)
researcher = ResearchAgent(
    page_store=page_store, memory_store=memory_store,
    retrievers={"idx": retriever}, generator=generator,
)
answer = researcher.research("When is the project deadline?")
print(answer.answer)
```

More examples in [`examples/quickstart/`](examples/quickstart/).

---

## Core Concepts

<a id="self-editing-memory"></a>
### Self-Editing Memory

Every `memorize()` call evaluates against existing state and picks one of four actions:

| Action | When | Effect |
|:---|:---|:---|
| **ADD** | New fact, no conflict | Creates a new memory entry |
| **UPDATE** | Same entity, newer information | Supersedes old version, preserves history |
| **DELETE** | Contradiction detected | Soft-deletes old entry, marks `t_invalid` |
| **NOOP** | Duplicate or irrelevant | No change to memory state |

This eliminates the "append-only rot" problem. Stale facts are actively retired.

<p align="center">
  <img src="assets/readme/final_svgs/03_memory_lifecycle.svg" alt="Memory Lifecycle" width="100%"/>
</p>

<a id="bi-temporal-model"></a>
### Bi-Temporal Model

Every memory carries five temporal coordinates:

```
t_created   — when the memory was first stored
t_observed  — when the underlying fact was observed in the world
t_valid     — start of the fact's validity window
t_invalid   — end of the fact's validity window (null = still valid)
t_expired   — when the memory was superseded or deleted
```

This enables **as-of queries**: "What did the system believe about X at time T?" — critical for auditing, debugging, and temporal consistency.

<p align="center">
  <img src="assets/readme/final_svgs/04_bitemporal_model.svg" alt="Bi-Temporal Model" width="100%"/>
</p>

### Hierarchical Tiers & Decay

Memories exist in three tiers, inspired by human memory consolidation:

| Tier | Retention | Boost | Promotion Trigger |
|:---|:---|:---|:---|
| **Short** | Hours–days | 1.0× | Auto on creation |
| **Mid** | Days–weeks | 1.2× | Repeated access / high salience |
| **Long** | Weeks–months | 1.4× | Consolidation job (sleep cycle) |

Decay follows `exp(-λ · days_old)` with configurable λ. The `SleepConsolidationJob` runs periodic maintenance to promote/demote memories and clean expired entries.

---

## Architecture

<a id="dual-agent-design"></a>
### Dual-Agent Design

MNEMOS uses two specialized agents:

```
┌─────────────────┐         ┌──────────────────┐
│   MemoryAgent   │         │  ResearchAgent   │
│                 │         │                  │
│ • memorize()    │────────▶│ • research()     │
│ • ADD/UPD/DEL   │ memory  │ • plan → search  │
│ • provenance    │  store  │ • integrate      │
│ • versioning    │◀────────│ • reflect loop   │
└─────────────────┘         └──────────────────┘
        │                           │
        ▼                           ▼
  AdvancedMemoryStore        HybridRetriever
  InMemoryPageStore          AdaptiveContextManager
  GraphMemoryStore           CohereReranker
```

- **MemoryAgent** — writes structured memories with self-editing lifecycle, version history, and provenance tracking.
- **ResearchAgent** — multi-iteration retrieval-augmented generation with plan → search → integrate → reflect loop.

<p align="center">
  <img src="assets/readme/final_svgs/02_request_lifecycle.svg" alt="Request Lifecycle" width="100%"/>
</p>

<a id="research-loop"></a>
### Research Loop

The ResearchAgent doesn't do one-shot retrieval. It runs an iterative loop:

```
 ┌──────────────────────────────────────────────┐
 │                                              │
 │    PLAN ──▶ SEARCH ──▶ INTEGRATE ──▶ REFLECT │
 │     ▲                                  │     │
 │     └──────── not enough? ◀────────────┘     │
 │                                              │
 │              enough? ──▶ ANSWER              │
 └──────────────────────────────────────────────┘
```

Each iteration refines the search plan based on what was found (or not found). Supports optional **HyDE** (hypothetical document embeddings) and **Self-RAG** (self-reflective retrieval).

---

<a id="hybrid-retriever"></a>
### HybridRetriever — 6-Signal Scoring

*Inspired by [MemTier (arXiv:2605.03675)](https://arxiv.org/abs/2605.03675)*

The HybridRetriever scores every memory against six normalized signals:

```
S(q, m) = 0.20·φ_sem + 0.30·φ_bm25 + 0.15·φ_graph + 0.15·φ_decay + 0.10·φ_cw + 0.10·φ_tier
```

| Signal | Weight | Source | Description |
|:---|:---:|:---|:---|
| **φ_sem** | 0.20 | Dense embeddings | Cosine similarity via Cohere/BGEM3, min-max normalized |
| **φ_bm25** | 0.30 | Lexical index | BM25 keyword scoring — highest weight for precision |
| **φ_graph** | 0.15 | Neo4j PPR | Personalized PageRank over entity-relation neighborhoods |
| **φ_decay** | 0.15 | Temporal | `exp(-λ·days)` with BM25 bypass for high-scoring lexical hits |
| **φ_cw** | 0.10 | Cognitive | `0.6×salience + 0.4×FSRS_strength` (emotional + spaced rep.) |
| **φ_tier** | 0.10 | Memory tier | Short=1.0×, Mid=1.2×, Long=1.4× (rewards consolidation) |

All weights are configurable via `HybridRetrieverConfig`. The retriever implements `AbsRetriever` and is a drop-in replacement anywhere retrievers are used.

<p align="center">
  <img src="assets/readme/final_svgs/09_hybrid_6signal_scoring.svg" alt="6-Signal Hybrid Scoring Engine" width="100%"/>
</p>

<a id="adaptive-context"></a>
### AdaptiveContextManager

*MemTier shows k=2 entries at 300-600 tokens outperforms larger retrieval budgets.*

The AdaptiveContextManager packs the highest-scored memories into a strict token budget:

| Stage | What It Does |
|:---|:---|
| **Measure** | Exact token count via tiktoken (`cl100k_base`) — replaces naive `len//4` |
| **Dedup** | Character trigram Jaccard similarity (threshold 0.60) skips near-duplicates |
| **Pack** | Greedy best-first by retrieval score until budget exhausted |
| **Compress** | LLM distillation fallback when candidates exceed 1.5× budget |

```python
from mnemos import AdaptiveContextManager, ContextManagerConfig

ctx = AdaptiveContextManager(
    max_tokens=2000,               # token budget
    tiktoken_model="cl100k_base",  # precise counting
    generator=generator,           # for compression fallback
    dedup_threshold=0.60,          # trigram Jaccard threshold
)
context_str = ctx.pack(hits, memory_store, profile_context="Senior engineer")
```

<p align="center">
  <img src="assets/readme/final_svgs/10_adaptive_context_manager.svg" alt="Adaptive Context Manager" width="100%"/>
</p>

<a id="ecl-pipeline"></a>
### ECL Pipeline — Extract, Cognify, Load

*Inspired by [Cognee](https://github.com/topoteretes/cognee)'s ECL architecture.*

The ECLPipeline enriches every memory at write-time with cognitive metadata:

| Phase | What Happens |
|:---|:---|
| **Extract** | Parse raw input via loaders (Text, URL, S3, Notion, GDrive...) + chunking with SHA-256 dedup |
| **Cognify** | Score emotional salience (0.0–1.0), initialize FSRS baselines (stability, difficulty, next_review) |
| **Load** | Commit enriched chunks to memory via `memorize()` — atomic write to all stores |

```python
from mnemos import ECLPipeline, EmotionalSalienceScorer, SpacedRepetitionScheduler

pipeline = ECLPipeline(
    salience_scorer=EmotionalSalienceScorer(generator=generator),
    scheduler=SpacedRepetitionScheduler(),
)
results = pipeline.ingest(loader=my_loader, agent=memory_agent,
                          memory_store=memory_store, page_store=page_store)
```

Both cognitive enrichments are optional — omit them for backward-compatible basic ingestion.

<p align="center">
  <img src="assets/readme/final_svgs/11_ecl_pipeline.svg" alt="ECL Pipeline" width="100%"/>
</p>

<a id="graph-memory"></a>
### Graph Memory

Neo4j-backed knowledge graph with three entity tiers:

| Tier | What It Stores | Traversal |
|:---|:---|:---|
| **Episode** | Raw observations with temporal bounds | Direct lookup |
| **Semantic Fact** | Extracted entity-relation-entity triples | Neighborhood expansion |
| **Community** | Summarized clusters of related facts | PPR (Personalized PageRank) |

The `GraphRetriever` performs entity-seeded neighborhood expansion with configurable depth and max nodes. Provenance edges link every fact back to its source episode.

<p align="center">
  <img src="assets/readme/final_svgs/06_graph_memory_3tier.svg" alt="3-Tier Graph Memory" width="100%"/>
</p>

---

## Interface Reference

### MemoryAgent

| Method | Signature | Returns |
|:---|:---|:---|
| `memorize` | `(text, memory_store, page_store) → MemoryUpdate` | `.new_state`, `.new_page`, `.debug` |

Access the memory ID via `result.new_page.meta.get("memory_id")`.

### ResearchAgent

| Method | Signature | Returns |
|:---|:---|:---|
| `research` | `(query) → ResearchOutput` | `.answer`, `.evidence`, `.iterations` |

### AdvancedMemoryStore

| Method | Description |
|:---|:---|
| `get_entries()` | All active memory entries |
| `get_entry_by_id(id)` | Single entry lookup |
| `add_entry(entry)` | Append new entry |
| `delete_entry(id)` | Soft delete (sets `t_expired`) |
| `hard_delete_entry(id)` | GDPR Article 17 permanent erasure |
| `get_version_history(id)` | Full version chain |
| `query_as_of(timestamp)` | Bi-temporal point-in-time query |
| `touch(id)` | Update access time (affects decay) |
| `cleanup_expired()` | Remove entries past retention window |
| `promote_demote()` | Tier transitions based on access patterns |

### HybridRetriever (AbsRetriever)

| Method | Description |
|:---|:---|
| `search(query_list, top_k)` | 6-signal scored retrieval → `List[List[Hit]]` |
| `build(page_store)` | Initialize sub-retrievers |
| `load(page_store)` | Load from persisted indexes |
| `update(page_store)` | Incremental index update |

### Hit Schema

```python
Hit(page_id, snippet, source, meta)
# meta dict contains per-signal scores:
# {"sem_score": 0.87, "bm25_score": 1.4, "graph_score": 0.5, ...}
```

---

## Configuration

MNEMOS is environment-first. Minimum setup:

| Variable | Purpose |
|:---|:---|
| `OPENROUTER_API_KEY` | LLM generation (required) |
| `OPENROUTER_BASE_URL` | API endpoint (default: openrouter.ai) |
| `COHERE_API_KEY` | Embeddings + reranking |
| `NEO4J_URI` | Graph memory (optional) |
| `NEO4J_USERNAME` / `NEO4J_PASSWORD` | Neo4j auth |

### Config Dataclasses

All configuration lives in `mnemos/config/`:

| Config | Key Parameters |
|:---|:---|
| `OpenAIGeneratorConfig` | `model_name`, `api_key`, `base_url`, `temperature`, `max_tokens` |
| `HybridRetrieverConfig` | `weights` (6-signal dict), `decay_lambda`, `decay_bypass_threshold`, `top_k` |
| `ContextManagerConfig` | `max_tokens`, `tiktoken_model`, `dedup_threshold` |
| `IndexRetrieverConfig` | `index_dir` |
| `CohereEmbedRetrieverConfig` | `model_name`, `api_key` |
| `CohereRerankerConfig` | `model_name`, `top_n` |
| `DenseRetrieverConfig` | `model_name`, `batch_size` |
| `BM25RetrieverConfig` | `index_dir`, `k1`, `b` |

---

## Repository Structure

```
mnemos/
├── agents/              # MemoryAgent + ResearchAgent
├── affect/              # EmotionalSalienceScorer, FadingAffectModel
├── cloud/               # Multi-tenant support
├── config/              # All config dataclasses
├── evaluation/          # RAGAS evaluator integration
├── generator/           # OpenAI, vLLM generator backends
├── graph/               # Neo4j GraphMemoryStore, ontology
├── ingestion/           # Loaders, chunkers, IngestionPipeline, ECLPipeline
├── integrations/        # LangChain adapter
├── learning/            # Experience replay buffer
├── maintenance/         # SleepConsolidationJob, MemoryConsolidator
├── mcp/                 # Model Context Protocol server
├── modalities/          # Image memory processing
├── multi_agent/         # Multi-agent coordination
├── privacy/             # GDPR erasure engine, audit logging
├── profile/             # UserProfile modeling + agent
├── prompts/             # Prompt templates
├── reinforcement/       # FSRS spaced repetition scheduler
├── retriever/           # Index, BM25, Dense, Graph, Hybrid, ContextManager
├── schemas/             # MemoryEntry, Page, Hit, AdvancedMemoryStore
├── server/              # FastAPI server + Prometheus metrics
├── summarization/       # Hierarchical summarizer
└── utils/               # Checkpoint manager, helpers

examples/quickstart/     # basic_usage.py, model_usage.py, ttl_usage.py
eval/                    # Evaluation entrypoints
tests/                   # Unit + integration tests
scripts/                 # run_maintenance.py, e2e_stress, neo4j_local_up
dashboard/               # Streamlit observability dashboard
assets/readme/           # SVG architecture diagrams + PNG frames
```

---

## Evaluation & Testing

```bash
# Unit tests
python3 -m pytest -q

# Full test suite (unit + optional live E2E)
./scripts/test_all.sh

# Stress test (requires API keys)
python3 scripts/e2e_stress_live_test.py

# Install dev + eval extras
pip install -e ".[dev,eval]"
```

Optional Neo4j for graph memory testing:
```bash
./scripts/neo4j_local_up.sh
```

---

## Architecture SVGs

Full animated architecture diagrams (1600×900, Inter font, teal/amber theme):

<details>
<summary><b>System Overview</b></summary>
<p align="center"><img src="assets/readme/final_svgs/01_system_overview.svg" alt="System Overview" width="100%"/></p>
</details>

<details>
<summary><b>Request Lifecycle</b></summary>
<p align="center"><img src="assets/readme/final_svgs/02_request_lifecycle.svg" alt="Request Lifecycle" width="100%"/></p>
</details>

<details>
<summary><b>Memory Lifecycle</b></summary>
<p align="center"><img src="assets/readme/final_svgs/03_memory_lifecycle.svg" alt="Memory Lifecycle" width="100%"/></p>
</details>

<details>
<summary><b>Bi-Temporal Model</b></summary>
<p align="center"><img src="assets/readme/final_svgs/04_bitemporal_model.svg" alt="Bi-Temporal Model" width="100%"/></p>
</details>

<details>
<summary><b>Retrieval Fusion Pipeline</b></summary>
<p align="center"><img src="assets/readme/final_svgs/05_retrieval_fusion.svg" alt="Retrieval Fusion" width="100%"/></p>
</details>

<details>
<summary><b>3-Tier Graph Memory</b></summary>
<p align="center"><img src="assets/readme/final_svgs/06_graph_memory_3tier.svg" alt="Graph Memory" width="100%"/></p>
</details>

<details>
<summary><b>Ingestion Pipeline</b></summary>
<p align="center"><img src="assets/readme/final_svgs/07_ingestion_pipeline.svg" alt="Ingestion Pipeline" width="100%"/></p>
</details>

<details>
<summary><b>Repository Capabilities Map</b></summary>
<p align="center"><img src="assets/readme/final_svgs/08_repo_capabilities_map.svg" alt="Capabilities Map" width="100%"/></p>
</details>

<details>
<summary><b>HybridRetriever — 6-Signal Scoring</b></summary>
<p align="center"><img src="assets/readme/final_svgs/09_hybrid_6signal_scoring.svg" alt="6-Signal Scoring" width="100%"/></p>
</details>

<details>
<summary><b>AdaptiveContextManager</b></summary>
<p align="center"><img src="assets/readme/final_svgs/10_adaptive_context_manager.svg" alt="Context Manager" width="100%"/></p>
</details>

<details>
<summary><b>ECL Pipeline</b></summary>
<p align="center"><img src="assets/readme/final_svgs/11_ecl_pipeline.svg" alt="ECL Pipeline" width="100%"/></p>
</details>

<details>
<summary><b>Package Architecture (mnemos/ internals)</b></summary>
<p align="center"><img src="assets/readme/mnemos_package_svgs/01_package_architecture.svg" alt="Package Architecture" width="100%"/></p>
</details>

<details>
<summary><b>Memory Write Sequence</b></summary>
<p align="center"><img src="assets/readme/mnemos_package_svgs/02_memory_write_sequence.svg" alt="Write Sequence" width="100%"/></p>
</details>

<details>
<summary><b>Research Runtime Sequence</b></summary>
<p align="center"><img src="assets/readme/mnemos_package_svgs/03_research_runtime_sequence.svg" alt="Research Sequence" width="100%"/></p>
</details>

<details>
<summary><b>Schema Relations</b></summary>
<p align="center"><img src="assets/readme/mnemos_package_svgs/04_schema_relations.svg" alt="Schema Relations" width="100%"/></p>
</details>

<details>
<summary><b>Retrieval Scoring Engine</b></summary>
<p align="center"><img src="assets/readme/mnemos_package_svgs/05_retrieval_scoring_engine.svg" alt="Scoring Engine" width="100%"/></p>
</details>

<details>
<summary><b>Graph Semantics CRUD</b></summary>
<p align="center"><img src="assets/readme/mnemos_package_svgs/06_graph_semantics_crud.svg" alt="Graph CRUD" width="100%"/></p>
</details>

---

## Additional Capabilities

| Capability | Module | Description |
|:---|:---|:---|
| **GDPR Erasure** | `mnemos.privacy` | `hard_delete_entry()` for Article 17 compliance + audit logging |
| **MCP Server** | `mnemos.mcp` | Model Context Protocol for tool-use agents |
| **Prometheus Metrics** | `mnemos.server.metrics` | Request latency, memory count, error rate |
| **Streamlit Dashboard** | `dashboard/` | Real-time memory observability |
| **LangChain Integration** | `mnemos.integrations` | Drop-in `MnemosLangchainMemory` adapter |
| **Multi-Tenant** | `mnemos.cloud` | Tenant isolation for SaaS deployments |
| **Image Memory** | `mnemos.modalities` | Visual content processing and storage |
| **Experience Replay** | `mnemos.learning` | Replay buffer for reinforcement-style memory training |
| **Hierarchical Summarization** | `mnemos.summarization` | Multi-level compression for long memory chains |
| **User Profiling** | `mnemos.profile` | Adaptive user modeling with profile agent |
| **Checkpointing** | `mnemos.utils` | Save/restore memory state snapshots |

---

## Research Foundations

MNEMOS draws from recent advances in agent memory systems:

- **MemTier** ([arXiv:2605.03675](https://arxiv.org/abs/2605.03675)) — Multi-signal retrieval fusion, tiered memory architecture, token-budget optimization
- **Cognee** ([github](https://github.com/topoteretes/cognee)) — ECL (Extract, Cognify, Load) ingestion pattern
- **Mem0** ([github](https://github.com/mem0ai/mem0)) — Developer experience patterns for memory APIs
- **FSRS** — Free Spaced Repetition Scheduler for memory strength modeling
- **Bi-temporal databases** — Temporal validity and point-in-time query semantics

---

## License

[MIT](LICENSE)

---

## Acknowledgments

- Built on: [OpenAI API](https://platform.openai.com/), [Cohere](https://cohere.com/), [Neo4j](https://neo4j.com/), [FastAPI](https://fastapi.tiangolo.com/), [tiktoken](https://github.com/openai/tiktoken)
- Research: MemTier, Cognee, Mem0
- Originally forked from [JITMIND](https://github.com/DivyamTalwar/JITMIND), fully rebranded and extended with 6 phases of architectural improvements

<div align="center">
<br/>

**MNEMOS** — Memory that edits itself, retrieves with precision, and improves over time.

<br/>
</div>
