from typing import Dict, Type

from .exceptions import RegistryError

# ---------------------------------------------------------------------------
# Global component registry
#
# Populated at import time by @register_component decorators.
#
# NOTE: Because this is a module-level mutable dict, it is shared across
# all code in the same Python process.  In production this is intentional —
# all pipelines discover the same set of installed components.
#
# In tests, use the ``isolated_registry`` context manager (below) to avoid
# cross-test pollution.
# ---------------------------------------------------------------------------
COMPONENT_REGISTRY: Dict[str, Dict[str, Type]] = {
    # Connector group
    "generator": {},
    "fetcher": {},
    # Document group
    "parser": {},
    "converter": {},
    "ocr": {},
    # Refinery group
    "normalizer": {},
    "processor": {},
    # Chunking group
    "splitter": {},
    # Wrapper group
    "adapter": {},
    # Assembler group
    "builder": {},
    # Loader group
    "writer": {},
    # Future groups (reserved slots)
    "tracer": {},
    "renderer": {},
}


def register_component(role: str):
    """
    Class decorator — register a component into the global registry.

    The decorated class must have a ``component_name`` class attribute which
    is used as the unique key within the given ``role`` bucket.

    Args:
        role: The component category (e.g. ``"fetcher"``, ``"writer"``).
              Must be one of the pre-defined keys in ``COMPONENT_REGISTRY``.

    Raises:
        RegistryError: If ``role`` is not a recognised registry key.

    Example::

        @register_component("writer")
        class FileWriter(BaseWriter):
            component_name = "FileWriter"
    """

    def decorator(cls):
        if role not in COMPONENT_REGISTRY:
            raise RegistryError(
                f"Unknown component role: {role!r}. "
                f"Valid roles: {sorted(COMPONENT_REGISTRY)}"
            )
        if hasattr(cls, "component_name"):
            COMPONENT_REGISTRY[role][cls.component_name] = cls
        return cls

    return decorator


def clear_registry(role: str | None = None) -> None:
    """
    Remove all entries from the registry (optionally scoped to one role).

    Primarily intended for use in tests — call from a fixture or
    ``setup_method`` to prevent cross-test pollution caused by the shared
    global state.

    Args:
        role: If supplied, clear only that role's bucket.
              If ``None``, clear every bucket.
    """
    if role is not None:
        if role not in COMPONENT_REGISTRY:
            raise RegistryError(f"Unknown component role: {role!r}.")
        COMPONENT_REGISTRY[role].clear()
    else:
        for bucket in COMPONENT_REGISTRY.values():
            bucket.clear()
