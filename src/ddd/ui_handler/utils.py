
import json
import time
import uuid
from typing import Any, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)



"""
Import utilities for optional UI dependencies
"""

# Rich library (optional)
try:
    import rich
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
    logger.debug("Rich库导入成功")
except ImportError:
    rich = None
    Console = Panel = Table = Text = box = None
    RICH_AVAILABLE = False
    logger.debug("Rich库不可用")

# Flet library (optional)
try:
    import flet as ft
    FLET_AVAILABLE = True
    logger.debug("Flet库导入成功")
except ImportError:
    ft = None
    FLET_AVAILABLE = False
    logger.debug("Flet库不可用")


def check_rich_available():
    """Check if Rich library is available"""
    if not RICH_AVAILABLE:
        raise ImportError("Rich is not available. Please install it with: uv add rich")
    return True


def check_flet_available():
    """Check if Flet library is available"""
    if not FLET_AVAILABLE:
        raise ImportError("Flet is not available. Please install it with: uv add flet")
    return True


"""
RPC utilities for ZMQ communication
"""


class RPCMessage:
    """RPC message wrapper for ZMQ communication"""

    def __init__(
        self,
        method: str | Callable,
        args: list = None,
        kwargs: dict = None,
        request_id: str = None,
    ):
        self.method = method
        self.args = args or []
        self.kwargs = kwargs or {}
        self.request_id = request_id or str(uuid.uuid4())
        self.timestamp = time.time()

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(
            {
                "method": self.method,
                "args": self.args,
                "kwargs": self.kwargs,
                "request_id": self.request_id,
                "timestamp": self.timestamp,
            }
        )

    @classmethod
    def from_json(cls, json_str: str) -> "RPCMessage":
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls(
            method=data["method"],
            args=data.get("args", []),
            kwargs=data.get("kwargs", {}),
            request_id=data.get("request_id"),
        )


class RPCResponse:
    """RPC response wrapper"""

    def __init__(self, result: Any = None, error: str = None, request_id: str = None):
        self.result = result
        self.error = error
        self.request_id = request_id
        self.timestamp = time.time()

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(
            {
                "result": self.result,
                "error": self.error,
                "request_id": self.request_id,
                "timestamp": self.timestamp,
            }
        )

    @classmethod
    def from_json(cls, json_str: str) -> "RPCResponse":
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls(
            result=data.get("result"),
            error=data.get("error"),
            request_id=data.get("request_id"),
        )


@dataclass
class RPCExecResult:
    result: Any = None
    error: str = None
