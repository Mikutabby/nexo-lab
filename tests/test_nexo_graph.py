import pytest

class TestGraphStore:
    def test_init_creates_root_and_branches(self, graph_store):
        root = graph_store.get_node("root")
        assert root is not None
        assert root["name"] == "Root"
        for bid in ("user", "directives", "world"):
            node = graph_store.get_node(bid)
            assert node is not None
            assert node["parent_id"] == "root"

    def test_create_node(self, graph_store):
        nid = graph_store.create_node(name="test", data="hello", branch="user")
        node = graph_store.get_node(nid)
        assert node["name"] == "test"
        assert node["data"] == "hello"
        assert node["branch"] == "user"

    def test_create_node_defaults_to_user_branch(self, graph_store):
        nid = graph_store.create_node(name="default")
        node = graph_store.get_node(nid)
        assert node["branch"] == "user"

    def test_create_node_empty_branch(self, graph_store):
        nid = graph_store.create_node(name="test", branch="world")
        node = graph_store.get_node(nid)
        assert node["branch"] == "world"
        assert node["parent_id"] == "world"

    def test_get_children(self, graph_store):
        user_id = graph_store.create_node(name="user fact", data="likes pizza", branch="user")
        kids = graph_store.get_children("user")
        assert any(k["id"] == user_id for k in kids)

    def test_search(self, graph_store):
        graph_store.create_node(name="color", data="blue", branch="user")
        graph_store.create_node(name="color", data="red", branch="user")
        results = graph_store.search("blue")
        assert len(results) >= 1
        assert any("blue" in r["data"] for r in results)

    def test_search_no_results(self, graph_store):
        results = graph_store.search("xyznonexistent")
        assert results == []

    def test_search_excludes_root_branches(self, graph_store):
        results = graph_store.search("Root")
        for r in results:
            assert r["id"] not in ("root", "user", "directives", "world")

    def test_touch_node_increments_count(self, graph_store):
        nid = graph_store.create_node(name="counter", data="test")
        before = graph_store.get_node(nid)["access_count"]
        graph_store.touch_node(nid)
        after = graph_store.get_node(nid)["access_count"]
        assert after == before + 1

    def test_update_node(self, graph_store):
        nid = graph_store.create_node(name="old", data="old data")
        assert graph_store.update_node(nid, name="new", data="new data")
        node = graph_store.get_node(nid)
        assert node["name"] == "new"
        assert node["data"] == "new data"

    def test_update_node_no_changes(self, graph_store):
        nid = graph_store.create_node(name="test")
        assert not graph_store.update_node(nid)

    def test_delete_node(self, graph_store):
        nid = graph_store.create_node(name="delete me", data="bye")
        assert graph_store.delete_node(nid)
        assert graph_store.get_node(nid) is None

    def test_cannot_delete_root(self, graph_store):
        assert not graph_store.delete_node("root")
        assert not graph_store.delete_node("user")
        assert not graph_store.delete_node("directives")
        assert not graph_store.delete_node("world")

    def test_jaccard_similarity(self, graph_store):
        sim = graph_store.jaccard_similarity("hello world", "hello there")
        assert 0.0 < sim < 1.0

    def test_jaccard_identical(self, graph_store):
        sim = graph_store.jaccard_similarity("hello world", "hello world")
        assert sim == 1.0

    def test_jaccard_empty(self, graph_store):
        assert graph_store.jaccard_similarity("", "hello") == 0.0
        assert graph_store.jaccard_similarity("hello", "") == 0.0
        assert graph_store.jaccard_similarity("", "") == 0.0

    def test_recall_search(self, graph_store):
        graph_store.create_node(name="food", data="pizza pasta tiramisu", branch="world")
        graph_store.create_node(name="unrelated", data="quantum physics", branch="world")
        results = graph_store.recall_search("pizza pasta", threshold=0.2)
        assert len(results) >= 1
        assert results[0]["_jaccard"] >= 0.2

    def test_get_recent(self, graph_store):
        nid = graph_store.create_node(name="recent", data="fresh")
        recent = graph_store.get_recent()
        ids = [r["id"] for r in recent]
        assert nid in ids

    def test_get_top(self, graph_store):
        nid = graph_store.create_node(name="popular", data="trending")
        for _ in range(3):
            graph_store.touch_node(nid)
        top = graph_store.get_top()
        assert top[0]["id"] == nid

    def test_stats(self, graph_store):
        s = graph_store.get_stats()
        assert s["total_nodes"] >= 4
        assert s["fact_nodes"] >= 0

    def test_warm_profile_empty(self, graph_store):
        profile = graph_store.warm_profile()
        assert "user" in profile
        assert "directives" in profile

    def test_warm_profile_with_data(self, graph_store):
        graph_store.create_node(name="my name", data="The user is called TestUser", branch="user")
        profile = graph_store.warm_profile()
        assert "TestUser" in profile["user"]

    def test_tree(self, graph_store):
        tree = graph_store.get_tree()
        assert "Root" in tree
        assert "User" in tree
        assert "Directives" in tree
        assert "World" in tree

    def test_find_by_data_exact(self, graph_store):
        graph_store.create_node(name="exact", data="unique_data_xyz", branch="user")
        found = graph_store.find_by_data_exact("unique_data_xyz")
        assert found is not None
        not_found = graph_store.find_by_data_exact("nonexistent")
        assert not_found is None

    def test_fts_search_fallback(self, graph_store):
        graph_store.create_node(name="ftstest", data="fts specific content", branch="world")
        results = graph_store.fts_search("specific")
        assert len(results) >= 1

    def test_cosine_similarity(self, graph_store):
        a = [1.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        assert graph_store.cosine_similarity(a, b) == 1.0
        c = [0.0, 1.0, 0.0]
        assert graph_store.cosine_similarity(a, c) == 0.0
        assert graph_store.cosine_similarity([], []) == 0.0
        assert graph_store.cosine_similarity([1.0], [1.0, 2.0]) == 0.0
