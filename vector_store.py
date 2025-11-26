"""Vector store management for recipe retrieval."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import faiss
import numpy as np
import yaml
from sentence_transformers import SentenceTransformer

LOGGER = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, recipe_dir: str | Path = "recipes", index_path: str | Path = "vector_store.index"):
        self.recipe_dir = Path(recipe_dir)
        self.index_path = Path(index_path)
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.cwe_index: faiss.Index | None = None
        self.full_text_index: faiss.Index | None = None
        self.documents: List[Dict[str, Any]] = []
        self._load_or_build()

    def _load_or_build(self):
        if self.index_path.exists() and self.index_path.is_dir():
            LOGGER.info("Loading existing vector store from %s", self.index_path)
            self.cwe_index = faiss.read_index(str(self.index_path / "cwe.index"))
            self.full_text_index = faiss.read_index(str(self.index_path / "full_text.index"))
            self.documents = np.load(self.index_path / "documents.npy", allow_pickle=True).tolist()
        else:
            LOGGER.info("Building new vector store.")
            self._build_indexes()

    def _build_indexes(self):
        self.documents = self._parse_recipes()
        if not self.documents:
            LOGGER.warning("No recipes found to build vector store.")
            return

        cwe_embeddings = self.embedding_model.encode([doc["metadata"]["cwe"] for doc in self.documents])
        full_text_embeddings = self.embedding_model.encode([doc["content"] for doc in self.documents])

        self.cwe_index = self._create_index(cwe_embeddings)
        self.full_text_index = self._create_index(full_text_embeddings)

        self.index_path.mkdir(exist_ok=True)
        faiss.write_index(self.cwe_index, str(self.index_path / "cwe.index"))
        faiss.write_index(self.full_text_index, str(self.index_path / "full_text.index"))
        np.save(self.index_path / "documents.npy", self.documents)

    def _create_index(self, embeddings: np.ndarray) -> faiss.Index:
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index = faiss.IndexIDMap(index)
        index.add_with_ids(embeddings, np.arange(len(embeddings)))
        return index

    def _parse_recipes(self) -> List[Dict[str, Any]]:
        docs = []
        recipe_files = list(self.recipe_dir.glob("*.txt"))
        LOGGER.info(f"Found {len(recipe_files)} recipe files in '{self.recipe_dir}'.")

        for recipe_path in recipe_files:
            LOGGER.info(f"  - Processing: {recipe_path.name}")
            with open(recipe_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if not first_line.startswith("cwe:"):
                    LOGGER.warning(f"    - Skipping {recipe_path.name}: First line is not a CWE ID.")
                    continue
                
                cwe_id = first_line.split(":", 1)[1].strip()
                content = f.read()
                
                metadata = {"cwe": cwe_id, "tags": [], "languages": []} # Create minimal metadata
                docs.append({"metadata": metadata, "content": content})
        return docs

    def search_cwe(self, cwe_id: str, k: int = 1) -> List[Dict[str, Any]]:
        if not self.cwe_index:
            return []
        query_vector = self.embedding_model.encode([cwe_id])
        _, indices = self.cwe_index.search(query_vector, k)
        return [self.documents[i] for i in indices[0] if i != -1]

    def search_full_text(self, query: str, k: int = 1, filter_metadata: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        if not self.full_text_index:
            return []
        
        query_vector = self.embedding_model.encode([query])
        
        # This is a simplified filter. For large scale, you'd use a more sophisticated approach.
        candidate_indices = list(range(len(self.documents)))
        if filter_metadata:
            if "language" in filter_metadata:
                candidate_indices = [
                    i for i in candidate_indices 
                    if filter_metadata["language"] in self.documents[i]["metadata"].get("languages", [])
                ]

        if not candidate_indices:
            return []

        # This is inefficient for large datasets. FAISS supports metadata filtering with some effort.
        # For this project, we'll search and then filter.
        _, indices = self.full_text_index.search(query_vector, len(candidate_indices))
        
        results = []
        for i in indices[0]:
            if i in candidate_indices:
                results.append(self.documents[i])
                if len(results) == k:
                    break
        return results
