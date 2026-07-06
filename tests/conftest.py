import pytest
import os
import sys
import importlib.machinery

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "memory")
NEXO_GRAPH_PATH = os.path.join(MEMORY_DIR, "nexo-graph")

loader = importlib.machinery.SourceFileLoader("nexo_graph", NEXO_GRAPH_PATH)
nexo_graph = loader.load_module()
sys.modules["nexo_graph"] = nexo_graph

@pytest.fixture
def graph_store(tmp_path):
    db = tmp_path / "test_graph.db"
    store = nexo_graph.GraphStore(str(db))
    yield store
    store.close()
