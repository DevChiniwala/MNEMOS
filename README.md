# Mnemos

**Temporal Memory Infrastructure for Autonomous AI**

Mnemos is a robust, production-ready memory infrastructure designed for autonomous agents. It provides versioned, bi-temporal memory storage, contradiction resolution, multi-channel retrieval, and full provenance tracking.

*Author: Dev Chiniwala*  
*(Based on the original JITMIND architecture by Divyam Talwar)*

---

## Key Features

- **Bi-Temporal Memory Model**: Tracks both system time (when observed) and valid time (when true in the world).
- **Contradiction Resolution**: Detects conflicts, versions memories, and maintains an explicit lineage of fact evolution.
- **Provenance Chains**: Every memory is backed by raw source pages and can explicitly explain its origins and version history.
- **Tiered Decay**: Memories smoothly decay in strength and demote from Long → Mid → Short term tiers over time.
- **Hybrid Retrieval**: Interfaces for Sparse (BM25), Dense (Vector), and Graph traversal search, combined with Reciprocal Rank Fusion.
- **Strictly Typed Configuration**: Fail-fast validation and clean dependency injection via protocols.

## Installation

```bash
pip install mnemos
```

## Quick Start

```python
from mnemos import Mnemos, MnemosConfig
from mnemos.providers.llm import OpenAICompatibleGenerator

# 1. Setup the generator
generator = OpenAICompatibleGenerator()

# 2. Initialize Mnemos
mnemos = Mnemos(generator=generator)

# 3. Store facts (contradictions are handled automatically)
id1 = mnemos.remember("Alice lives in New York.", valid_from="2023-01-01T00:00:00Z")
id2 = mnemos.remember("Alice moved to London.", valid_from="2024-06-01T00:00:00Z")

# 4. Recall
results = mnemos.recall("Where does Alice live?")
print(results[0].content)  # "Alice moved to London."

# 5. Explain provenance
explanation = mnemos.explain(id2)
print(explanation.summary())
```

## Architecture

Mnemos is divided into highly decoupled modules:

- `mnemos.core`: Interfaces, Configuration, Exceptions
- `mnemos.temporal`: Bi-temporal logic, Interval semantics
- `mnemos.memory`: Thread-safe stores, MemoryEntry models
- `mnemos.evolution`: Contradiction resolution pipeline
- `mnemos.provenance`: Source tracking and explanation chains
- `mnemos.retrieval`: RRF fusion, Temporal gating, Re-ranking
- `mnemos.graph`: Optional semantic graph backend

## License

MIT License. See `LICENSE` for details.
