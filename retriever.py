"""Retrieval pipeline for fetching context from the vector store."""

from __future__ import annotations
import re
from vector_store import VectorStore


class Retriever:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def _extract_focused_context(self, content: str) -> str:
        """Extracts title, description, checklist, and fix idea from recipe content."""
        name_match = re.search(r"name: (.*)", content)
        description_match = re.search(
            r"Short Description:(.*?)(?:\n\n[A-Z]|\Z)", content, re.DOTALL
        )
        checklist_match = re.search(
            r"Secure Coding Checklist:(.*?)(?:\n\n[A-Z]|\Z)", content, re.DOTALL
        )
        fix_idea_match = re.search(r"Sample Fix Idea.*", content, re.DOTALL)

        name = name_match.group(1).strip() if name_match else ""
        description = description_match.group(1).strip() if description_match else ""
        checklist = checklist_match.group(1).strip() if checklist_match else ""
        fix_idea = fix_idea_match.group(0).strip() if fix_idea_match else ""

        parts = []
        if name:
            parts.append(f"**{name}**")
        if description:
            parts.append(description)
        if checklist:
            parts.append(f"**Checklist:**\n{checklist}")
        if fix_idea:
            parts.append(f"**Fix Idea:**\n{fix_idea}")

        if not parts:
            return "No specific guidance found."

        return "\n\n".join(parts)

    def retrieve(self, cwe: str, language: str, code: str) -> str:
        """
        Retrieve and parse context using a hybrid approach.
        1. Try to find a direct match for the CWE ID.
        2. If not found, fall back to a full-text semantic search.
        3. Parse the retrieved content to return only the most relevant sections.
        """
        raw_content = ""
        cwe_results = self.vector_store.search_cwe(cwe)
        if cwe_results:
            raw_content = cwe_results[0]["content"]
        else:
            query = f"{language} {cwe} {code[:500]}"
            full_text_results = self.vector_store.search_full_text(
                query, filter_metadata={"language": language}
            )
            if full_text_results:
                raw_content = full_text_results[0]["content"]

        if not raw_content:
            return "No specific guidance found."

        return self._extract_focused_context(raw_content)
