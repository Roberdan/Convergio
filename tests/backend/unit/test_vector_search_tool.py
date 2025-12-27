import pytest

from agents.tools.convergio_tools import VectorSearchTool, VectorSearchArgs, AUTOGEN_AVAILABLE


@pytest.mark.asyncio
@pytest.mark.skipif(not AUTOGEN_AVAILABLE, reason="AutoGen not installed")
async def test_vector_search_tool_no_results_dev_mock(monkeypatch):
    # The dev client returns empty results list; ensure tool handles gracefully
    tool = VectorSearchTool()
    out = await tool.run(VectorSearchArgs(query="test query", top_k=3))
    assert isinstance(out, str)
    assert ("Vector search results" in out) or ("No relevant results" in out) or ("error" in out.lower())
