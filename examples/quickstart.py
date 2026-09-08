import os
from mnemos import Mnemos
from mnemos.providers.base import MockGenerator

def run_demo():
    print("Initializing Mnemos with Mock Generator...")
    mnemos = Mnemos(generator=MockGenerator())

    print("\n[1] Agent learns a fact in 2023...")
    id1 = mnemos.remember(
        "Project Alpha is codenamed 'Titan'.",
        valid_from="2023-01-01T00:00:00Z"
    )
    print(f"Stored -> {id1}")

    print("\n[2] Agent learns a conflicting fact in 2024...")
    id2 = mnemos.remember(
        "Project Alpha has been renamed to 'Atlas'.",
        valid_from="2024-03-01T00:00:00Z"
    )
    print(f"Stored -> {id2}")

    print("\n[3] Current active memory state:")
    for entry in mnemos.history():
        print(f"  - [{entry.status.value.upper()}] {entry.content} (Valid From: {entry.temporal.valid_from})")

    print("\n[4] Requesting explanation for the latest fact...")
    explanation = mnemos.explain(id2)
    print("Provenance Chain:")
    print(explanation.summary())
    print("\nLineage:")
    for rec in explanation.lineage:
        print(f"  - [{rec.mutation_type}] {rec.source_content} (supersedes: {rec.supersedes})")

if __name__ == "__main__":
    run_demo()
