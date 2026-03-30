class SayouCoreError(Exception):
    """Base exception for all Sayou Core errors."""

    pass


class InitializationError(SayouCoreError):
    """Raised when a component fails to initialise."""

    pass


class RegistryError(SayouCoreError):
    """Raised when a registry operation is invalid (e.g. unknown role)."""

    pass
