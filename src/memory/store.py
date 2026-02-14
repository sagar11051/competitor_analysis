"""Memory store implementation using LangGraph's InMemoryStore.

Provides namespaced storage for:
- User profiles and preferences
- Session summaries
- Competitor profile cache

Namespace schema:
    ("users", user_id) / "profile"      → {role, company, industry}
    ("users", user_id) / "preferences"  → {focus_areas, depth, format}
    ("sessions", session_id) / "summary" → {query, key_findings, decisions}
    ("competitors", name) / "profile"   → {website, model, market, ...}
"""

from typing import Any, Optional

from langgraph.store.memory import InMemoryStore

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level store singleton (shared across the application)
_memory_store: Optional["MemoryStore"] = None


class MemoryStore:
    """Domain-specific wrapper around LangGraph's InMemoryStore.

    Provides typed methods for accessing user, session, and competitor data
    with proper namespacing.
    """

    def __init__(self, store: Optional[InMemoryStore] = None):
        """Initialize MemoryStore with an optional backing store.

        Args:
            store: An existing InMemoryStore instance. If None, creates a new one.
        """
        self._store = store if store is not None else InMemoryStore()

    @property
    def raw_store(self) -> InMemoryStore:
        """Return the underlying InMemoryStore for direct graph integration."""
        return self._store

    # -------------------------------------------------------------------------
    # User Profile Methods
    # -------------------------------------------------------------------------

    def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Get a user's profile data.

        Args:
            user_id: Unique user identifier

        Returns:
            User profile dict or None if not found
        """
        namespace = ("users", user_id)
        try:
            item = self._store.get(namespace, "profile")
            if item and hasattr(item, "value"):
                return item.value
            return None
        except Exception as e:
            logger.debug(f"User profile not found for {user_id}: {e}")
            return None

    def put_user_profile(self, user_id: str, profile: dict) -> None:
        """Store a user's profile data.

        Args:
            user_id: Unique user identifier
            profile: Profile dict with keys like {role, company, industry}
        """
        namespace = ("users", user_id)
        self._store.put(namespace, "profile", profile)
        logger.debug(f"Stored user profile for {user_id}")

    # -------------------------------------------------------------------------
    # User Preferences Methods
    # -------------------------------------------------------------------------

    def get_user_preferences(self, user_id: str) -> Optional[dict]:
        """Get a user's preferences.

        Args:
            user_id: Unique user identifier

        Returns:
            Preferences dict or None if not found
        """
        namespace = ("users", user_id)
        try:
            item = self._store.get(namespace, "preferences")
            if item and hasattr(item, "value"):
                return item.value
            return None
        except Exception as e:
            logger.debug(f"User preferences not found for {user_id}: {e}")
            return None

    def put_user_preferences(self, user_id: str, prefs: dict) -> None:
        """Store a user's preferences.

        Args:
            user_id: Unique user identifier
            prefs: Preferences dict with keys like {focus_areas, depth, format}
        """
        namespace = ("users", user_id)
        self._store.put(namespace, "preferences", prefs)
        logger.debug(f"Stored user preferences for {user_id}")

    # -------------------------------------------------------------------------
    # Session Summary Methods
    # -------------------------------------------------------------------------

    def get_session_summary(self, session_id: str) -> Optional[dict]:
        """Get a session's summary.

        Args:
            session_id: Unique session identifier

        Returns:
            Session summary dict or None if not found
        """
        namespace = ("sessions", session_id)
        try:
            item = self._store.get(namespace, "summary")
            if item and hasattr(item, "value"):
                return item.value
            return None
        except Exception as e:
            logger.debug(f"Session summary not found for {session_id}: {e}")
            return None

    def put_session_summary(self, session_id: str, summary: dict) -> None:
        """Store a session's summary.

        Args:
            session_id: Unique session identifier
            summary: Summary dict with keys like {query, key_findings, decisions}
        """
        namespace = ("sessions", session_id)
        self._store.put(namespace, "summary", summary)
        logger.debug(f"Stored session summary for {session_id}")

    # -------------------------------------------------------------------------
    # Competitor Profile Methods
    # -------------------------------------------------------------------------

    def get_competitor_profile(self, name: str) -> Optional[dict]:
        """Get a cached competitor profile.

        Args:
            name: Competitor name (normalized to lowercase)

        Returns:
            Competitor profile dict or None if not found
        """
        normalized_name = name.lower().strip()
        namespace = ("competitors", normalized_name)
        try:
            item = self._store.get(namespace, "profile")
            if item and hasattr(item, "value"):
                logger.debug(f"Cache hit for competitor: {name}")
                return item.value
            return None
        except Exception as e:
            logger.debug(f"Competitor profile not found for {name}: {e}")
            return None

    def put_competitor_profile(self, name: str, profile: dict) -> None:
        """Store a competitor profile in the cache.

        Args:
            name: Competitor name (will be normalized to lowercase)
            profile: Profile dict with keys like {website, model, market, ...}
        """
        normalized_name = name.lower().strip()
        namespace = ("competitors", normalized_name)
        self._store.put(namespace, "profile", profile)
        logger.debug(f"Cached competitor profile for {name}")

    def search_competitors(self, query: str, limit: int = 10) -> list[dict]:
        """Search for competitor profiles matching a query.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching competitor profile dicts
        """
        results = []
        query_lower = query.lower()

        try:
            # Search through all competitor namespace items
            # InMemoryStore.search returns items matching namespace prefix
            items = self._store.search(("competitors",))

            for item in items:
                if len(results) >= limit:
                    break

                profile = item.value if hasattr(item, "value") else {}
                name = profile.get("name", "")
                website = profile.get("website", "")
                market = profile.get("market", "")

                # Simple text matching on name, website, or market
                searchable = f"{name} {website} {market}".lower()
                if query_lower in searchable:
                    results.append(profile)

        except Exception as e:
            logger.debug(f"Competitor search failed: {e}")

        return results


def get_memory_store() -> MemoryStore:
    """Get the global MemoryStore singleton.

    Returns:
        The shared MemoryStore instance
    """
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
        logger.info("Initialized global MemoryStore")
    return _memory_store


def _get_store_from_context() -> Optional[MemoryStore]:
    """Attempt to get the store from LangGraph runtime context.

    This is used within graph nodes to access the store passed during compilation.

    Returns:
        MemoryStore wrapper or None if not running in graph context
    """
    try:
        from langgraph.store.base import get_store
        raw_store = get_store()
        if raw_store is not None:
            return MemoryStore(raw_store)
    except (ImportError, RuntimeError):
        pass
    return None
