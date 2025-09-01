
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
跨平台输入工具模块
解决Windows/WSL/Linux下终端输入的兼容性问题
"""

import sys
import platform
import time
import threading
import queue


def get_single_key_input(prompt: str = "") -> str:
    """
    跨平台获取单个按键输入（阻塞式）

    Args:
        prompt: 提示信息

    Returns:
        str: 用户输入的单个字符（转为小写）
    """
    if prompt:
        print(prompt, end="", flush=True)

    system = platform.system().lower()

    if system == "windows":
        try:
            import msvcrt

            while True:
                # 在Windows上，getch()会立即返回一个字节
                key = msvcrt.getch()
                try:
                    decoded_key = key.decode("utf-8")
                    if decoded_key.isprintable():
                        print(decoded_key, end="", flush=True)  # 回显输入
                        return decoded_key.lower()
                    elif decoded_key in ["\r", "\n"]:  # 处理回车键
                        print()  # 换行
                        return "enter"  # 返回特殊标识
                    elif ord(decoded_key) == 27:  # ESC键
                        print()  # 换行
                        return "esc"
                    else:
                        # 对于其他不可打印字符（如功能键），返回一个通用标识
                        print()  # 换行
                        return "other"
                except UnicodeDecodeError:
                    # 可能是功能键，返回通用标识而不是继续循环
                    print()  # 换行
                    return "other"
        except ImportError:
            return _fallback_input(prompt)

    else:  # Unix/Linux/WSL
        try:
            import termios
            import tty

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.cbreak(fd)
                key = sys.stdin.read(1)
                # 读取后立即恢复终端，避免影响后续输出
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

                if key in ["\r", "\n"]:  # 处理回车键
                    print()  # 换行
                    return "enter"  # 返回特殊标识
                elif ord(key) == 27:  # ESC键
                    print()  # 换行
                    return "esc"
                elif key.isprintable():
                    print(key, end="", flush=True)  # 回显输入
                    print()  # 回显后换行
                    return key.lower()
                else:
                    # 其他不可打印字符
                    print()  # 换行
                    return "other"
            except Exception:
                # 确保在任何错误情况下都能恢复终端设置
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                return _fallback_input()

        except (ImportError, OSError):
            return _fallback_input(prompt)


def get_choice_with_double_click(
    prompt: str, target_key: str = "*", timeout: float = 0.4
) -> str:
    """
    获取用户选择，同时检测特定按键的双击。
    这是实现双击功能的核心。

    Args:
        prompt (str): 显示给用户的提示语.
        target_key (str, optional): 需要检测双击的目标按键. Defaults to '*'.
        timeout (float, optional): 双击的有效时间窗口（秒）. Defaults to 0.4.

    Returns:
        str: 如果是普通按键，返回按键字符。如果是双击，返回 "keydouble" (例如 "*double").
    """
    first_key = get_single_key_input(prompt)

    if first_key != target_key:
        return first_key

    # 如果第一个按键是目标键，则在超时内等待第二个按键
    key_queue = queue.Queue()

    def key_reader():
        # 在后台线程中获取下一个按键，不显示提示语
        key = get_single_key_input("")
        key_queue.put(key)

    reader_thread = threading.Thread(target=key_reader, daemon=True)
    reader_thread.start()

    try:
        # 等待后台线程的结果，带有超时
        second_key = key_queue.get(timeout=timeout)
        if second_key == target_key:
            print()  # 第二个键回显后换行
            return f"{target_key}double"
        else:
            # 按下了其他键，视为单击*
            return first_key
    except queue.Empty:
        # 超时，没有第二个按键，视为单击*
        return first_key


def _fallback_input(prompt: str = "") -> str:
    """
    回退输入方法，使用标准的行输入。
    """
    try:
        if prompt:
            print(prompt, end="")
        key = input().strip()
        return key.lower() if key else ""
    except (KeyboardInterrupt, EOFError):
        print("\n👋 取消操作。")
        return "q"


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
