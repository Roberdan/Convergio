"""Compatibility shim for legacy tests expecting VectorSearchService.

Real vector search is exposed via tools in src.agents.tools.vector_search_tool.
This minimal service offers embed() and search() no-op behaviors suitable for tests.
"""

from __future__ import annotations
from typing import Any, Dict


class VectorSearchService:
    def __init__(self) -> None:
        pass

    async def embed(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": doc.get("id"), "ok": True}

    async def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        return {"results": []}
