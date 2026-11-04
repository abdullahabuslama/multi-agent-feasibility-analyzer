"""Logging for agent runs.

`get_logger` gives every module the same log format. `trace_node` wraps a
graph node so each agent run logs when it starts, how long it took, and
any error. The graph wraps every node with it, so no agent needs its own
timing code.
"""

import functools
import logging
import time
from collections.abc import Callable
from typing import Any

from config.settings import get_settings

LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def get_logger(name: str) -> logging.Logger:
    _configure_once()
    return logging.getLogger(name)


def trace_node(agent_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator: log start, duration, and errors of one agent node."""
    logger = get_logger("agents.trace")

    def decorator(node: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(node)
        def traced(*args: Any, **kwargs: Any) -> Any:
            logger.info("%s started", agent_name)
            started = time.perf_counter()
            try:
                result = node(*args, **kwargs)
            except Exception:
                logger.exception("%s failed after %.2fs", agent_name, time.perf_counter() - started)
                raise
            logger.info("%s finished in %.2fs", agent_name, time.perf_counter() - started)
            return result

        return traced

    return decorator


@functools.cache
def _configure_once() -> None:
    logging.basicConfig(level=get_settings().log_level.upper(), format=LOG_FORMAT)
    # The HTTP client logs every request at INFO, which hides the agent trace.
    logging.getLogger("httpx").setLevel(logging.WARNING)
