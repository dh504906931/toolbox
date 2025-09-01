"""
TUI渲染器核心模块 - 负责美观的视觉呈现
专注于渲染组件，不处理交互逻辑
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from rich.table import Table

# 导入我们重构后的输入工具
from ..utils import input_utils

# 延迟导入Rich库以提高启动速度
def _import_rich():
    """延迟导入Rich库组件"""
    global Console, Panel, Table, Text, Layout, Align, Padding, box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.layout import Layout
    from rich.align import Align
    from rich.padding import Padding
    from rich import box

class Theme:
    """主题配置类"""
    PRIMARY = "#00d4aa"
    SECONDARY = "#0ea5e9"
    SUCCESS = "#22c55e"
    WARNING = "#f59e0b"
    DANGER = "#ef4444"
    INFO = "#6366f1"
    TEXT_PRIMARY = "#f8fafc"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"
    BG_DARK = "#0f172a"
    BG_CARD = "#1e293b"
    BG_SUBTLE = "#334155"
    BORDER = "#475569"

class UIHandlerBase(ABC):
    """Abstract base class defining the TUI handler interface"""

    @classmethod
    def from_type(cls, type: str):
        """Create a UI handler from a type string"""
        if type == "rich":
            from ddd.ui_handler.rich_handler_new import RichHandler

            return RichHandler()
        elif type == "flet":
            from ddd.ui_handler.flet_handler import FletUIHandler

            return FletUIHandler()
        else:
            raise ValueError(
                f"Invalid UI handler type: {type}. Supported types: 'rich', 'web'"
            )

    @abstractmethod
    def clear_screen(self):
        """Clear screen"""
        raise NotImplementedError

    @abstractmethod
    def print_text(
        self, text: Union[str, Any] = "", style: Optional[str] = None, end: str = "\n"
    ):
        """Print text with optional styling"""
        raise NotImplementedError

    @abstractmethod
    def print_panel(
        self,
        content: Union[str, Any],
        title: Optional[str] = None,
        style: Optional[str] = None,
        border_style: Optional[str] = None,
        box_type: Optional[str] = None,
        padding: tuple = (0, 1),
        title_align: str = "left",
    ) -> None:
        """Print content in a panel"""
        raise NotImplementedError

    @abstractmethod
    def print_table(
        self,
        title: Optional[str] = None,
        title_style: Optional[str] = None,
        columns: Optional[List[Dict[str, Any]]] = None,
        rows: Optional[List[List[str]]] = None,
        box_type: Optional[str] = None,
        border_style: Optional[str] = None,
        show_header: bool = True,
        **kwargs,
    ) -> None:
        """Create and print a table"""
        raise NotImplementedError

    @abstractmethod
    def get_input(
        self, prompt: Union[str, Any] = "", default: str = ""
    ) -> Optional[str]:
        """Get user input with optional prompt and default, returns None if interrupted"""
        raise NotImplementedError


_global_renderer = None


def get_ui_handler():
    """获取全局renderer实例"""
    global _global_renderer
    if _global_renderer is None:
        from ddd.ui_handler.handler_base import UIHandlerBase

        _global_renderer = UIHandlerBase.from_type("rich")
    return _global_renderer
