class TargetBlocked(Exception):
    """The target resolves to an address the proxy refuses to reach (loopback, private network, ...)."""
