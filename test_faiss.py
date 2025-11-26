"""Interactive test script for managing and querying the FAISS vector store."""

import logging
import shutil
from pathlib import Path

from vector_store import VectorStore

# Configure logging to see output from the vector store
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

def rebuild_store(index_path: Path) -> VectorStore:
    """Remove the old vector store and build a new one."""
    if index_path.exists():
        LOGGER.info("Removing old vector store at %s...", index_path)
        shutil.rmtree(index_path)
    LOGGER.info("Rebuilding vector store...")
    store = VectorStore(index_path=index_path)
    LOGGER.info("Vector store rebuilt successfully.")
    return store

def main():
    """Run an interactive loop to test the vector store."""
    index_path = Path("vector_store.index")
    vector_store = VectorStore(index_path=index_path)

    print("\n--- FAISS DB Control Script ---")
    print("Commands:")
    print("  <CWE-ID>   - Perform a similarity search (e.g., CWE-89)")
    print("  !rebuild   - Delete and rebuild the vector store")
    print("  !exit      - Exit the script")
    print("---------------------------------")

    while True:
        try:
            command = input("\nEnter command > ").strip()

            if command.lower() == "!exit":
                break
            
            if command.lower() == "!rebuild":
                vector_store = rebuild_store(index_path)
                continue

            # Perform similarity search
            results = vector_store.search_cwe(command)
            
            if not results:
                print(f"No results found for '{command}'.")
            else:
                print(f"\n--- Search Results for '{command}' ---")
                for i, doc in enumerate(results):
                    print(f"\n--- Result {i+1} ---")
                    print(f"Metadata: {doc['metadata']}")
                    print("--- Content ---")
                    print(doc['content'])
                print("------------------------------------")

        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as e:
            LOGGER.error("An error occurred: %s", e)

if __name__ == "__main__":
    main()
