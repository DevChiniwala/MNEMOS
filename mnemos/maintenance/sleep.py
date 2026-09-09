import time
import logging
from typing import Optional
from datetime import datetime
from mnemos.schemas.advanced_memory import AdvancedMemoryStore
from mnemos.reinforcement.fsrs import SpacedRepetitionScheduler
from mnemos.maintenance.consolidation import consolidate_memories

logger = logging.getLogger("mnemos_sleep")

class SleepConsolidationJob:
    """
    Executes 'sleep mode' maintenance on the memory store.
    Mimics biological sleep: consolidates redundant facts, prunes dead connections,
    and recalculates spaced repetition intervals.
    """
    
    def __init__(self, memory_store: AdvancedMemoryStore, generator=None):
        self.memory_store = memory_store
        self.scheduler = SpacedRepetitionScheduler()
        self.generator = generator

    def run_sleep_cycle(self):
        logger.info("Initiating MNEMOS sleep cycle consolidation...")
        
        start_time = time.time()
        
        # Step 1: Cleanup obviously expired entries
        expired_count = self.memory_store.cleanup_expired()
        logger.info(f"Purged {expired_count} expired entries.")
        
        # Step 2: Reinforcement check (find memories due for review)
        active = self.memory_store.get_active_entries()
        now = datetime.utcnow().isoformat()
        
        due_for_review = []
        for entry in active:
            next_review = entry.meta.get("fsrs_next_review")
            if next_review and next_review < now:
                due_for_review.append(entry)
                
        # In a full system, due_for_review might trigger background "dreams" (replays)
        # For now, we passively reinforce them if they are still relevant
        for entry in due_for_review:
            self.scheduler.apply_reinforcement(entry.meta)
        
        if due_for_review:
            self.memory_store._persist()
            logger.info(f"Reinforced {len(due_for_review)} memories during sleep.")
            
        # Step 3: Semantic consolidation (RAPTOR-style or basic clustering)
        # The legacy maintenance module has consolidate_memories which we can call if a generator is present
        if self.generator:
            try:
                # Assuming the existing consolidation function accepts store and generator
                consolidated = consolidate_memories(self.memory_store, self.generator)
                logger.info(f"Consolidated {consolidated} memory clusters.")
            except Exception as e:
                logger.warning(f"Semantic consolidation failed: {e}")
                
        elapsed = time.time() - start_time
        logger.info(f"Sleep cycle complete in {elapsed:.2f}s.")
