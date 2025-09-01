import os
import sys
from typing import Any, List, Dict

from rich.align import Align

from ddd.ui_handler.handler_base import _import_rich, Theme
from ddd.ui_handler.utils import (
    Console,
    Panel,
    Table,
    Text,
    box,
    get_single_key_input,
    get_choice_with_double_click,
)


class RichHandler:
    """TUI渲染器类 - 提供内容语义接口"""

    _instance = None

    def __new__(cls):
        """单例模式 - 避免重复创建和导入开销"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._console = None
        self.theme = Theme()
        self._rich_imported = False
        self._initialized = True

        # 语义风格配置 - 内部使用，不暴露给外部
        self.semantic_styles = {
            "success": {"style": self.theme.SUCCESS, "icon": "✅"},
            "error": {"style": self.theme.DANGER, "icon": "❌"},
            "warning": {"style": self.theme.WARNING, "icon": "⚠️"},
            "info": {"style": self.theme.INFO, "icon": "ℹ️"},
            "banner": {"icon": "🚀", "box": "double"},
            "section": {"icon": "📝"},
            "table": {"icon": "📋"},
            "prompt": {"icon": "❯", "style": f"bold {self.theme.PRIMARY}"},
            "help": {"icon": "💡", "title": "操作说明"},
        }

    def _ensure_rich(self):
        """确保Rich库已导入"""
        if not self._rich_imported:
            _import_rich()
            self._rich_imported = True
            self._console = Console()

    @property
    def console(self):
        """延迟创建console对象"""
        if self._console is None:
            self._ensure_rich()
        return self._console

    def clear_screen(self):
        """清屏"""
        os.system("cls" if os.name == "nt" else "clear")

    # === 基础内容语义接口 ===

    def print_text(self, text: str):
        """打印纯文本"""
        self._ensure_rich()
        self.console.print(text)

    def print_panel(self, content: str, title: str = None):
        """显示面板内容"""
        self._ensure_rich()
        panel = Panel(
            content,
            title=title,
            title_align="left",
            style=self.theme.BG_CARD,
            border_style=self.theme.BORDER,
            box=box.ROUNDED,
            padding=(0, 1),
        )
        self.console.print(panel)

    def print_table(
        self, data: List[List[str]], headers: List[str] = None, title: str = None
    ):
        """显示表格数据"""
        self._ensure_rich()

        table = Table(
            title=title,
            title_style=f"bold {self.theme.SECONDARY}",
            box=box.ROUNDED,
            border_style=self.theme.BORDER,
            show_header=bool(headers),
            header_style=f"bold {self.theme.TEXT_PRIMARY}",
            title_justify="left",
            expand=True,
            padding=(0, 1),
        )

        # 添加列
        if headers:
            for header in headers:
                table.add_column(header, style=self.theme.TEXT_PRIMARY)
        else:
            # 如果没有headers，根据第一行数据创建空列
            if data:
                for i in range(len(data[0])):
                    table.add_column("", style=self.theme.TEXT_PRIMARY)

        # 添加行
        for row in data:
            table.add_row(*[str(cell) for cell in row])

        return table

    def get_input(
        self, prompt: str, default: str = "", exit_message: str = "再见!"
    ) -> str:
        """获取用户输入"""
        self._ensure_rich()

        config = self.semantic_styles["prompt"]
        prompt_text = Text()
        prompt_text.append(f"{config['icon']} ", style=config["style"])
        prompt_text.append(prompt, style=self.theme.TEXT_PRIMARY)
        if default:
            prompt_text.append(f" [{default}]", style=self.theme.TEXT_SECONDARY)
        prompt_text.append(": ", style=self.theme.TEXT_PRIMARY)

        try:
            user_input = self.console.input(prompt_text).strip()
            return user_input if user_input else default
        except (KeyboardInterrupt, EOFError):
            self.console.print(f"\n{exit_message}")
            sys.exit(0)

    def get_choice(self, prompt: str, target_key: str = "*") -> str:
        """获取选择输入"""
        self._ensure_rich()

        config = self.semantic_styles["prompt"]
        prompt_text = Text()
        prompt_text.append(f"\n{config['icon']} ", style=config["style"])
        prompt_text.append(prompt, style=self.theme.TEXT_PRIMARY)

        choice = get_choice_with_double_click(str(prompt_text), target_key=target_key)
        return choice

    def wait_for_key(self, prompt: str = "\n按任意键继续..."):
        """等待按键"""
        get_single_key_input(prompt)

    def confirm(
        self,
        message: str,
        default: bool = False,
        yes_text: str = "Y",
        no_text: str = "n",
    ) -> bool:
        """确认对话框"""

        default_text = (
            f"{yes_text}/{no_text}"
            if default
            else f"{yes_text.lower()}/{no_text.upper()}"
        )
        response = get_single_key_input(f"{message} ({default_text}): ")
        if response == "":
            return default
        return response.lower() == yes_text.lower()

    def show_progress(self, description: str):
        """显示进度"""
        self._ensure_rich()
        with self.console.status(f"[bold green]{description}...") as status:
            return status

    # === 特定语义接口 ===

    def print_success(self, message: str):
        """成功消息语义"""
        config = self.semantic_styles["success"]
        content = f"{config['icon']} {message}"
        panel = Panel(
            content,
            style=config["style"],
            border_style=self.theme.BORDER,
            box=box.ROUNDED,
        )
        self.console.print(panel)

    def print_error(self, message: str):
        """错误消息语义"""
        config = self.semantic_styles["error"]
        content = f"{config['icon']} {message}"
        panel = Panel(
            content,
            style=config["style"],
            border_style=self.theme.BORDER,
            box=box.ROUNDED,
        )
        self.console.print(panel)

    def print_warning(self, message: str):
        """警告消息语义"""
        config = self.semantic_styles["warning"]
        content = f"{config['icon']} {message}"
        panel = Panel(
            content,
            style=config["style"],
            border_style=self.theme.BORDER,
            box=box.ROUNDED,
        )
        self.console.print(panel)

    def print_info(self, message: str):
        """信息消息语义"""
        config = self.semantic_styles["info"]
        content = f"{config['icon']} {message}"
        panel = Panel(
            content,
            style=config["style"],
            border_style=self.theme.BORDER,
            box=box.ROUNDED,
        )
        self.console.print(panel)

    def print_banner(self, title: str, subtitle: str = "", version: str = ""):
        """横幅语义"""
        self._ensure_rich()
        config = self.semantic_styles["banner"]

        banner_text = Text()
        banner_text.append(f"{config['icon']} ", style="bold cyan")
        banner_text.append(title, style=f"bold {self.theme.PRIMARY}")
        if version:
            banner_text.append(f" v{version}", style=f"{self.theme.TEXT_SECONDARY}")
        if subtitle:
            banner_text.append(f"\n{subtitle}", style=f"{self.theme.TEXT_MUTED}")

        panel = Panel(
            Align.center(banner_text),
            box=getattr(box, config["box"].upper(), box.DOUBLE),
            style=self.theme.PRIMARY,
            padding=(1, 2),
        )
        self.console.print()
        self.console.print(panel)
        self.console.print()

    def print_section(self, title: str, content: str):
        """章节语义"""
        config = self.semantic_styles["section"]
        display_title = f"{config['icon']} {title}"
        self.print_panel(content, title=display_title)

    def print_menu_table(self, title: str, options: List[Dict[str, Any]]) -> "Table":
        """菜单表格语义 - 将选项数据转换为表格格式"""
        config = self.semantic_styles["table"]
        display_title = f"{config['icon']} {title}"

        headers = ["序号", "功能", "描述"]
        data = []

        for option in options or []:
            key = option.get("key", "")
            icon_opt = option.get("icon", "")
            name = option.get("name", "")
            desc = option.get("description", "")
            name_with_icon = f"{icon_opt} {name}" if icon_opt else name
            data.append([f"[{key}]", name_with_icon, desc])

        # 创建表格但不直接打印，返回给调用者
        table = Table(
            title=display_title,
            title_style=f"bold {self.theme.SECONDARY}",
            box=box.ROUNDED,
            border_style=self.theme.BORDER,
            show_header=True,
            header_style=f"bold {self.theme.TEXT_PRIMARY}",
            title_justify="left",
            expand=True,
            padding=(0, 1),
        )

        # 添加列，菜单表格有特定的列配置
        table.add_column("序号", style=f"bold {self.theme.PRIMARY}", width=6)
        table.add_column("功能", style=self.theme.TEXT_PRIMARY, min_width=25)
        table.add_column("描述", style=self.theme.TEXT_SECONDARY, min_width=35)

        # 添加行
        for row in data:
            table.add_row(*row)

        return table

    def print_help_panel(
        self, help_items: List[Dict[str, str]], title: str = "操作说明"
    ):
        """帮助信息语义"""
        self._ensure_rich()

        config = self.semantic_styles["help"]

        help_text = Text()
        help_text.append(f"{config['icon']} {title}: ", style=f"bold {self.theme.INFO}")

        for item in help_items:
            key = item.get("key", "")
            desc = item.get("description", "")
            help_text.append(f"[{key}] {desc}  ", style=self.theme.TEXT_PRIMARY)

        panel = Panel(
            help_text,
            style=self.theme.BG_SUBTLE,
            border_style=self.theme.BORDER,
            box=box.SIMPLE,
            padding=(0, 1),
        )
        self.console.print()
        self.console.print(panel)

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
        self.print_section(title, "")

        # 使用基础表格接口
        data = [[f"{i}.", option] for i, option in enumerate(options, 1)]
        table = self.print_table(data)
        self.console.print(table)

        prompt = multiple_prompt if allow_multiple else single_prompt
        while True:
            try:
                selection = self.get_input(prompt)
                indices = (
                    [int(x.strip()) - 1 for x in selection.split(",")]
                    if "," in selection and allow_multiple
                    else [int(selection) - 1]
                )
                if all(0 <= i < len(options) for i in indices):
                    return indices
                else:
                    self.print_error(range_error)
            except (ValueError, IndexError):
                self.print_error(invalid_error)

    # === 兼容性方法 ===

    def get_line_input(
        self, prompt: str, default: str = "", exit_message: str = "👋 再见!"
    ) -> str:
        """[DEPRECATED] 使用 get_input 替代"""
        return self.get_input(prompt, default, exit_message)

    def get_menu_input(self, prompt: str) -> str:
        """[DEPRECATED] 使用 get_choice 替代"""
        return self.get_choice(prompt, target_key="*")

    def wait_for_any_key(self, prompt: str = "\n按任意键继续..."):
        """[DEPRECATED] 使用 wait_for_key 替代"""
        self.wait_for_key(prompt)

    def print_menu(
        self, title: str, options: List[Dict[str, Any]], show_help: bool = True
    ) -> "Table":
        """[DEPRECATED] 使用 print_menu_table 替代"""
        return self.print_menu_table(title, options)

    def print_help_info(self, help_items: List[Dict[str, str]] = None):
        """[DEPRECATED] 使用 print_help_panel 替代"""
        default_items = [
            {"key": "q", "description": "退出程序"},
            {"key": "-", "description": "返回上级"},
            {"key": "数字", "description": "选择功能"},
            {"key": "双击*", "description": "页面设置"},
        ]
        self.print_help_panel(help_items or default_items)
