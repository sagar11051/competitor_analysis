"""Tests for the memory store implementation."""

import pytest

from src.memory.store import MemoryStore, get_memory_store


# -----------------------------------------------------------------------------
# MemoryStore Unit Tests
# -----------------------------------------------------------------------------


class TestMemoryStoreUserProfile:
    """Tests for user profile methods."""

    def test_put_and_get_user_profile(self):
        store = MemoryStore()
        profile = {"role": "analyst", "company": "TestCorp", "industry": "tech"}

        store.put_user_profile("user-123", profile)
        result = store.get_user_profile("user-123")

        assert result == profile

    def test_get_user_profile_not_found(self):
        store = MemoryStore()
        result = store.get_user_profile("nonexistent-user")
        assert result is None

    def test_put_user_profile_overwrites(self):
        store = MemoryStore()

        store.put_user_profile("user-1", {"role": "analyst"})
        store.put_user_profile("user-1", {"role": "manager"})

        result = store.get_user_profile("user-1")
        assert result == {"role": "manager"}

    def test_user_profile_namespace_isolation(self):
        store = MemoryStore()

        store.put_user_profile("user-a", {"role": "analyst"})
        store.put_user_profile("user-b", {"role": "manager"})

        assert store.get_user_profile("user-a") == {"role": "analyst"}
        assert store.get_user_profile("user-b") == {"role": "manager"}


class TestMemoryStoreUserPreferences:
    """Tests for user preferences methods."""

    def test_put_and_get_user_preferences(self):
        store = MemoryStore()
        prefs = {"focus_areas": ["pricing", "features"], "depth": "deep", "format": "json"}

        store.put_user_preferences("user-123", prefs)
        result = store.get_user_preferences("user-123")

        assert result == prefs

    def test_get_user_preferences_not_found(self):
        store = MemoryStore()
        result = store.get_user_preferences("nonexistent-user")
        assert result is None

    def test_preferences_separate_from_profile(self):
        store = MemoryStore()

        store.put_user_profile("user-1", {"role": "analyst"})
        store.put_user_preferences("user-1", {"depth": "shallow"})

        profile = store.get_user_profile("user-1")
        prefs = store.get_user_preferences("user-1")

        assert profile == {"role": "analyst"}
        assert prefs == {"depth": "shallow"}


class TestMemoryStoreSessionSummary:
    """Tests for session summary methods."""

    def test_put_and_get_session_summary(self):
        store = MemoryStore()
        summary = {
            "query": "https://example.com",
            "key_findings": ["finding1", "finding2"],
            "decisions": ["approved"],
        }

        store.put_session_summary("session-abc", summary)
        result = store.get_session_summary("session-abc")

        assert result == summary

    def test_get_session_summary_not_found(self):
        store = MemoryStore()
        result = store.get_session_summary("nonexistent-session")
        assert result is None

    def test_session_namespace_isolation(self):
        store = MemoryStore()

        store.put_session_summary("session-1", {"query": "url1"})
        store.put_session_summary("session-2", {"query": "url2"})

        assert store.get_session_summary("session-1") == {"query": "url1"}
        assert store.get_session_summary("session-2") == {"query": "url2"}


class TestMemoryStoreCompetitorProfile:
    """Tests for competitor profile methods."""

    def test_put_and_get_competitor_profile(self):
        store = MemoryStore()
        profile = {
            "name": "Competitor Inc",
            "website": "https://competitor.com",
            "model": "SaaS",
            "market": "enterprise",
        }

        store.put_competitor_profile("Competitor Inc", profile)
        result = store.get_competitor_profile("Competitor Inc")

        assert result == profile

    def test_get_competitor_profile_not_found(self):
        store = MemoryStore()
        result = store.get_competitor_profile("nonexistent-competitor")
        assert result is None

    def test_competitor_name_normalized(self):
        """Competitor names should be case-insensitive."""
        store = MemoryStore()
        profile = {"name": "TestCo", "website": "https://testco.com"}

        store.put_competitor_profile("TestCo", profile)

        # Should find with different case
        assert store.get_competitor_profile("testco") == profile
        assert store.get_competitor_profile("TESTCO") == profile
        assert store.get_competitor_profile("  TestCo  ") == profile

    def test_competitor_namespace_isolation(self):
        store = MemoryStore()

        store.put_competitor_profile("comp-a", {"name": "A"})
        store.put_competitor_profile("comp-b", {"name": "B"})

        assert store.get_competitor_profile("comp-a") == {"name": "A"}
        assert store.get_competitor_profile("comp-b") == {"name": "B"}


class TestMemoryStoreSearchCompetitors:
    """Tests for competitor search method."""

    def test_search_competitors_by_name(self):
        store = MemoryStore()

        store.put_competitor_profile("acme-corp", {"name": "Acme Corp", "website": "https://acme.com", "market": "retail"})
        store.put_competitor_profile("beta-inc", {"name": "Beta Inc", "website": "https://beta.io", "market": "tech"})

        results = store.search_competitors("acme")
        assert len(results) == 1
        assert results[0]["name"] == "Acme Corp"

    def test_search_competitors_by_market(self):
        store = MemoryStore()

        store.put_competitor_profile("tech-1", {"name": "Tech One", "website": "https://tech1.com", "market": "fintech"})
        store.put_competitor_profile("tech-2", {"name": "Tech Two", "website": "https://tech2.com", "market": "fintech"})
        store.put_competitor_profile("other", {"name": "Other", "website": "https://other.com", "market": "retail"})

        results = store.search_competitors("fintech")
        assert len(results) == 2

    def test_search_competitors_limit(self):
        store = MemoryStore()

        for i in range(10):
            store.put_competitor_profile(f"test-{i}", {"name": f"Test {i}", "website": f"https://test{i}.com", "market": "test"})

        results = store.search_competitors("test", limit=3)
        assert len(results) <= 3

    def test_search_competitors_no_results(self):
        store = MemoryStore()
        store.put_competitor_profile("acme", {"name": "Acme", "website": "https://acme.com", "market": "retail"})

        results = store.search_competitors("xyz123nonexistent")
        assert results == []

    def test_search_competitors_empty_store(self):
        store = MemoryStore()
        results = store.search_competitors("anything")
        assert results == []


class TestMemoryStoreRawStore:
    """Tests for raw_store property."""

    def test_raw_store_returns_inmemorystore(self):
        from langgraph.store.memory import InMemoryStore

        store = MemoryStore()
        raw = store.raw_store

        assert isinstance(raw, InMemoryStore)

    def test_raw_store_shared_with_wrapper(self):
        """Operations on raw_store should be visible in wrapper."""
        from langgraph.store.memory import InMemoryStore

        raw = InMemoryStore()
        store = MemoryStore(raw)

        # Put via wrapper
        store.put_user_profile("user-1", {"role": "admin"})

        # Get via raw store
        item = raw.get(("users", "user-1"), "profile")
        assert item.value == {"role": "admin"}


# -----------------------------------------------------------------------------
# Singleton Tests
# -----------------------------------------------------------------------------


class TestGetMemoryStore:
    """Tests for the get_memory_store singleton function."""

    def test_get_memory_store_returns_memory_store(self):
        store = get_memory_store()
        assert isinstance(store, MemoryStore)

    def test_get_memory_store_returns_singleton(self):
        store1 = get_memory_store()
        store2 = get_memory_store()
        assert store1 is store2

    def test_singleton_shares_data(self):
        store1 = get_memory_store()
        store1.put_user_profile("singleton-test", {"role": "tester"})

        store2 = get_memory_store()
        result = store2.get_user_profile("singleton-test")
        assert result == {"role": "tester"}


# -----------------------------------------------------------------------------
# Namespace Isolation Tests
# -----------------------------------------------------------------------------


class TestNamespaceIsolation:
    """Tests for namespace isolation between different data types."""

    def test_user_session_competitor_isolation(self):
        """User, session, and competitor namespaces should not interfere."""
        store = MemoryStore()

        # Same key "test-123" in different namespaces
        store.put_user_profile("test-123", {"type": "user"})
        store.put_session_summary("test-123", {"type": "session"})
        store.put_competitor_profile("test-123", {"type": "competitor"})

        assert store.get_user_profile("test-123") == {"type": "user"}
        assert store.get_session_summary("test-123") == {"type": "session"}
        assert store.get_competitor_profile("test-123") == {"type": "competitor"}

    def test_profile_vs_preferences_isolation(self):
        """User profile and preferences should be separate keys."""
        store = MemoryStore()

        store.put_user_profile("user-1", {"role": "analyst"})
        store.put_user_preferences("user-1", {"depth": "deep"})

        # Updating one should not affect the other
        store.put_user_profile("user-1", {"role": "manager"})

        assert store.get_user_profile("user-1") == {"role": "manager"}
        assert store.get_user_preferences("user-1") == {"depth": "deep"}


# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------


class TestGraphIntegration:
    """Tests for graph compilation with store."""

    def test_compiled_graph_has_store(self):
        """Compiled graph should have store attribute when store is passed."""
        from src.agents.graph import get_compiled_graph

        compiled = get_compiled_graph()

        # The compiled graph should have the store
        assert hasattr(compiled, "store")

    def test_graph_compiles_with_memory_store(self):
        """Main graph should compile successfully with memory store."""
        from src.agents.graph import build_main_graph, get_memory_store

        graph = build_main_graph()
        memory_store = get_memory_store()

        # Should compile without error
        compiled = graph.compile(
            store=memory_store.raw_store,
        )

        assert compiled is not None
        assert hasattr(compiled, "invoke")
