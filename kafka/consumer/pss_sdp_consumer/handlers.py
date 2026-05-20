from __future__ import annotations
import logging
from typing import Any, Callable, Mapping

# Handler protocol, deliberately a single callable, not a class hierarchy.
#
# Why: handlers will be plugged in over time (write-to-disk, forward-to-SDP,
# metrics fan-out). We do not yet know what lifecycle hooks they will need,
# so locking in an ABC with on_start/on_stop/on_error now would be guesswork.
# A class with __call__ already satisfies this protocol, so upgrading later
# is non-breaking.
Handler = Callable[[Mapping[str, Any], bytes], None]

_log = logging.getLogger(__name__)


def log_handler(envelope: Mapping[str, Any], payload: bytes) -> None:
    _log.debug(
        "received message_id=%s payload_bytes=%d",
        envelope.get("message_id"),
        len(payload),
    )
