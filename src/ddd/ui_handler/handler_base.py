"""
TUI渲染器核心模块 - 负责美观的视觉呈现
专注于渲染组件，不处理交互逻辑
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from rich.table import Table


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
            from ddd.ui_handler.rich_handler import RichHandler

            return RichHandler()
        elif type == "flet":
            from ddd.ui_handler.flet_handler import FletUIHandler

            return FletUIHandler()
        else:
            raise ValueError(
                f"Invalid UI handler type: {type}. Supported types: 'rich', 'flet'"
            )

    # === 原有接口（保持向后兼容）===

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

    # === 新的语义接口 ===

    # 基础内容语义接口
    @abstractmethod
    def print_text_semantic(self, text: str):
        """打印纯文本 - 语义接口"""
        raise NotImplementedError

    @abstractmethod
    def print_panel_semantic(self, content: str, title: str = None):
        """显示面板内容 - 语义接口"""
        raise NotImplementedError

    @abstractmethod
    def print_table_semantic(
        self, data: List[List[str]], headers: List[str] = None, title: str = None
    ):
        """显示表格数据 - 语义接口"""
        raise NotImplementedError

    @abstractmethod
    def get_input_semantic(
        self, prompt: str, default: str = "", exit_message: str = "再见!"
    ) -> str:
        """获取用户输入 - 语义接口"""
        raise NotImplementedError

    @abstractmethod
    def get_choice(self, prompt: str, target_key: str = "*") -> str:
        """获取选择输入"""
        raise NotImplementedError

    @abstractmethod
    def wait_for_key(self, prompt: str = "\n按任意键继续..."):
        """等待按键"""
        raise NotImplementedError

    @abstractmethod
    def confirm(
        self,
        message: str,
        default: bool = False,
        yes_text: str = "Y",
        no_text: str = "n",
    ) -> bool:
        """确认对话框"""
        raise NotImplementedError

    @abstractmethod
    def show_progress(self, description: str):
        """显示进度"""
        raise NotImplementedError

    # 特定语义接口
    @abstractmethod
    def print_success(self, message: str):
        """成功消息语义"""
        raise NotImplementedError

    @abstractmethod
    def print_error(self, message: str):
        """错误消息语义"""
        raise NotImplementedError

    @abstractmethod
    def print_warning(self, message: str):
        """警告消息语义"""
        raise NotImplementedError

    @abstractmethod
    def print_info(self, message: str):
        """信息消息语义"""
        raise NotImplementedError

    @abstractmethod
    def print_banner(self, title: str, subtitle: str = "", version: str = ""):
        """横幅语义"""
        raise NotImplementedError

    @abstractmethod
    def print_section(self, title: str, content: str):
        """章节语义"""
        raise NotImplementedError

    @abstractmethod
    def print_menu_table(self, title: str, options: List[Dict[str, Any]]):
        """菜单表格语义"""
        raise NotImplementedError

    @abstractmethod
    def print_help_panel(
        self, help_items: List[Dict[str, str]], title: str = "操作说明"
    ):
        """帮助信息语义"""
        raise NotImplementedError

    @abstractmethod
    def select_from_list(
        self,
        title: str,
        options: List[str],
        allow_multiple: bool = False,
        single_prompt: str = "请选择选项",
        multiple_prompt: str = "请选择选项 (多选用逗号分隔)",
        range_error: str = "选择超出范围，请重新选择",
        invalid_error: str = "输入无效，请输入数字",
    ) -> List[int]:
        """列表选择语义"""
        raise NotImplementedError


_global_renderer = None


def get_ui_handler():
    """获取全局renderer实例"""
    global _global_renderer
    if _global_renderer is None:
        from ddd.ui_handler.handler_base import UIHandlerBase

        _global_renderer = UIHandlerBase.from_type("rich")
    return _global_renderer
