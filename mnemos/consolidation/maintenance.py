# -*- coding: utf-8 -*-
"""Memory maintenance and consolidation routines."""

from __future__ import annotations

import json
from typing import Dict, List, Optional

from mnemos.core.interfaces import Generator, MemoryStore
from mnemos.memory.models import MemoryEntry, MemoryStatus


class MemoryConsolidator:
    """Consolidates redundant or highly related memories into single robust entries.
    
    Preserves lineage by marking the source entries as MERGED and linking them.
    """

    def __init__(self, generator: Generator, store: MemoryStore) -> None:
        self._generator = generator
        self._store = store

    def run_consolidation(self, batch_size: int = 50) -> int:
        """Scan active memory and consolidate highly overlapping facts."""
        if not hasattr(self._store, "get_active_entries"):
            return 0
            
        active = self._store.get_active_entries()
        if len(active) < 2:
            return 0

        # Heuristic: group by common entities
        clusters: Dict[str, List[MemoryEntry]] = {}
        for e in active:
            ents = [ent.get("name", "") for ent in e.meta.get("entities", []) if isinstance(ent, dict)]
            if not ents:
                continue
            # Pick primary entity
            primary = ents[0].lower()
            clusters.setdefault(primary, []).append(e)

        merged_count = 0
        for cluster_id, entries in list(clusters.items())[:batch_size]:
            if len(entries) < 2:
                continue
            
            # Simple heuristic: if we have more than 3 facts about the same entity, summarize
            if len(entries) >= 3:
                success = self._summarize_cluster(entries)
                if success:
                    merged_count += len(entries)
                    
        return merged_count

    def _summarize_cluster(self, entries: List[MemoryEntry]) -> bool:
        """Use LLM to summarize a cluster of facts into one or more consolidated facts."""
        facts = [f"- {e.content} (Valid: {e.temporal.valid_from or 'Unknown'} to {e.temporal.valid_until or 'Present'})" for e in entries]
        facts_text = "\n".join(facts)
        
        prompt = (
            "You are a memory consolidation engine. Consolidate these related facts into a single, "
            "comprehensive summary fact. Preserve temporal details if they differ.\n\n"
            f"Facts:\n{facts_text}\n\n"
            "Return JSON:\n"
            '{"consolidated_fact": "the summary text", "is_meaningful": true/false}'
        )
        
        try:
            resp = self._generator.generate(prompt, temperature=0.1)
            text = resp.get("text", "")
            data = json.loads(text[text.find("{"): text.rfind("}") + 1])
            
            if data.get("is_meaningful") and data.get("consolidated_fact"):
                new_content = data["consolidated_fact"]
                entry_ids = [e.id for e in entries]
                
                # Create merged entry
                merged = MemoryEntry(content=new_content)
                merged.merged_from = entry_ids
                
                # The memory store merge handles setting old to MERGED
                if hasattr(self._store, "merge_entries"):
                    self._store.merge_entries(entry_ids, merged)
                return True
        except Exception as e:
            print(f"[Consolidation Error] {e}")
            pass
            
        return False
