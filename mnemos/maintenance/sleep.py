import time
import logging
from datetime import datetime, timezone
from mnemos.schemas.advanced_memory import AdvancedMemoryStore
from mnemos.reinforcement.fsrs import SpacedRepetitionScheduler

logger = logging.getLogger("mnemos_sleep")


class SleepConsolidationJob:
    """
    Executes 'sleep mode' maintenance on the memory store.
    Consolidates redundant facts, prunes expired entries,
    and recalculates spaced repetition intervals.
    """

    def __init__(self, memory_store: AdvancedMemoryStore, generator=None):
        self.memory_store = memory_store
        self.scheduler = SpacedRepetitionScheduler()
        self.generator = generator

    def run_sleep_cycle(self):
        logger.info("Initiating MNEMOS sleep cycle consolidation...")

        start_time = time.time()

        expired_count = self.memory_store.cleanup_expired()
        logger.info(f"Purged {expired_count} expired entries.")

        active = self.memory_store.get_entries(include_inactive=False)
        now = datetime.now(timezone.utc).isoformat()

        due_for_review = [
            entry for entry in active
            if entry.meta.get("fsrs_next_review") and entry.meta["fsrs_next_review"] < now
        ]

        for entry in due_for_review:
            self.scheduler.apply_reinforcement(entry.meta)

        if due_for_review:
            entry_ids = [e.id for e in due_for_review]
            self.memory_store.touch(entry_ids)
            logger.info(f"Reinforced {len(due_for_review)} memories during sleep.")

        if self.generator:
            try:
                from mnemos.maintenance.consolidation import MemoryConsolidator
                consolidator = MemoryConsolidator(
                    memory_store=self.memory_store,
                    generator=self.generator,
                )
                consolidated = consolidator.consolidate()
                logger.info(f"Consolidated {len(consolidated)} memory clusters.")
            except Exception as e:
                logger.warning(f"Semantic consolidation failed: {e}")

        elapsed = time.time() - start_time
        logger.info(f"Sleep cycle complete in {elapsed:.2f}s.")
