"""Shared GUI exception groups.

These tuples describe expected failures for best-effort UI operations and
hardware state reads/writes.  Keeping them centralized avoids broad
generic exception handlers and keeps GUI mixins consistent.
"""

BEST_EFFORT_ERRORS = (AttributeError, RuntimeError, OSError, IOError)
HARDWARE_STATE_ERRORS = (AttributeError, RuntimeError, OSError, IOError, ValueError, TypeError)
