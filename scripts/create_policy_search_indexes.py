import asyncio
import sys

# Must run before importing/creating the PGEngine.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

from app.rag.vector_store import get_hybrid_vector_store


def main() -> None:
    hybrid_store = get_hybrid_vector_store()

    hybrid_store.apply_hybrid_search_index()

    print("Hybrid text-search index created.")


if __name__ == "__main__":
    main()
