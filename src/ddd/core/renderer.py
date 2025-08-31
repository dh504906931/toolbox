"""
TUI渲染器核心模块 - 负责美观的视觉呈现
专注于渲染组件，不处理交互逻辑
"""

import os
import sys
from typing import List, Dict, Any, Optional, TYPE_CHECKING

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

class Renderer:
    """TUI渲染器类 - 专注视觉呈现"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式 - 避免重复创建和导入开销"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if getattr(self, '_initialized', False):
            return
            
        self._console = None
        self.theme = Theme()
        self._rich_imported = False
        self._initialized = True
    
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
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_banner(self, title: str, subtitle: str = "", version: str = ""):
        """显示标题横幅"""
        self._ensure_rich()
        banner_text = Text()
        banner_text.append("🚀 ", style="bold cyan")
        banner_text.append(title, style=f"bold {self.theme.PRIMARY}")
        if version:
            banner_text.append(f" v{version}", style=f"{self.theme.TEXT_SECONDARY}")
        if subtitle:
            banner_text.append(f"\n{subtitle}", style=f"{self.theme.TEXT_MUTED}")
        panel = Panel(Align.center(banner_text), box=box.DOUBLE, style=self.theme.PRIMARY, padding=(1, 2))
        self.console.print()
        self.console.print(panel)
        self.console.print()
        
    def print_menu(self, title: str, options: List[Dict[str, Any]], show_help: bool = True) -> "Table":
        """显示美观的菜单 - 支持选项、功能、描述"""
        self._ensure_rich()
        table = Table(title=f"📋 {title}", title_style=f"bold {self.theme.SECONDARY}", box=box.ROUNDED, border_style=self.theme.BORDER, show_header=True, header_style=f"bold {self.theme.TEXT_PRIMARY}", title_justify="left", expand=True, padding=(0, 1))
        table.add_column("序号", style=f"bold {self.theme.PRIMARY}", width=3)
        table.add_column("功能", style=self.theme.TEXT_PRIMARY, min_width=25)
        table.add_column("描述", style=self.theme.TEXT_SECONDARY, min_width=35)
        for option in options:
            key, icon, name, desc = option.get('key', ''), option.get('icon', ''), option.get('name', ''), option.get('description', '')
            name_with_icon = f"{icon} {name}"
            table.add_row(f"[{key}]", name_with_icon, desc)
        # 不再在table中添加退出和返回选项，它们会在帮助信息中显示
        return table
        
    def print_help_info(self):
        """在界面底部显示帮助信息"""
        self._ensure_rich()
        help_text = Text()
        help_text.append("💡 操作说明: ", style=f"bold {self.theme.INFO}")
        help_text.append("[q] 退出程序  ", style=self.theme.TEXT_PRIMARY)
        help_text.append("[-] 返回上级  ", style=self.theme.TEXT_PRIMARY)
        help_text.append("[数字] 选择功能  ", style=self.theme.TEXT_PRIMARY)
        help_text.append("[双击*] 页面设置", style=self.theme.TEXT_PRIMARY)
        panel = Panel(help_text, style=self.theme.BG_SUBTLE, border_style=self.theme.BORDER, box=box.SIMPLE, padding=(0, 1))
        self.console.print()
        self.console.print(panel)
        
    def print_success(self, message: str):
        self._ensure_rich()
        self.console.print(Panel(f"✅ {message}", style=self.theme.SUCCESS, box=box.ROUNDED))
        
    def print_error(self, message: str):
        self._ensure_rich()
        self.console.print(Panel(f"❌ {message}", style=self.theme.DANGER, box=box.ROUNDED))
        
    def print_warning(self, message: str):
        self._ensure_rich()
        self.console.print(Panel(f"⚠️ {message}", style=self.theme.WARNING, box=box.ROUNDED))
        
    def print_info(self, message: str):
        self._ensure_rich()
        self.console.print(Panel(f"ℹ️ {message}", style=self.theme.INFO, box=box.ROUNDED))
        
    def print_section(self, title: str, content: str):
        self._ensure_rich()
        self.console.print(Panel(content, title=f"📝 {title}", title_align="left", style=self.theme.BG_CARD, border_style=self.theme.BORDER, box=box.ROUNDED))
        
    def get_line_input(self, prompt: str, default: str = "") -> str:
        """获取用户的一行输入 (按回车结束)"""
        prompt_text = Text()
        prompt_text.append("❯ ", style=f"bold {self.theme.PRIMARY}")
        prompt_text.append(prompt, style=self.theme.TEXT_PRIMARY)
        if default:
            prompt_text.append(f" [{default}]", style=self.theme.TEXT_SECONDARY)
        prompt_text.append(": ", style=self.theme.TEXT_PRIMARY)
        
        try:
            user_input = self.console.input(prompt_text).strip()
            return user_input if user_input else default
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n👋 再见!")
            sys.exit(0)

    def get_menu_input(self, prompt: str) -> str:
        """
        【新增】获取菜单单键输入，并处理双击逻辑。
        Page层应该调用此方法来获取用户命令。
        """
        prompt_text = Text()
        prompt_text.append("\n❯ ", style=f"bold {self.theme.PRIMARY}")
        prompt_text.append(prompt, style=self.theme.TEXT_PRIMARY)
        
        # 调用重构后的工具函数
        choice = input_utils.get_choice_with_double_click(str(prompt_text), target_key='*')
        
        return choice

    def wait_for_any_key(self, prompt: str = "\n按任意键继续..."):
        """【新增】等待用户按下任意键"""
        input_utils.get_single_key_input(prompt)

    def confirm(self, message: str, default: bool = False) -> bool:
        """确认对话框 - 使用y/n单键确认"""
        from ..utils import input_utils
        default_text = "Y/n" if default else "y/N"
        response = input_utils.get_single_key_input(f"{message} ({default_text}): ")
        if response == '':
            return default
        return response.lower() == 'y'

    # select_from_list 和 show_progress 方法保持不变...
    def select_from_list(self, title: str, options: List[str], allow_multiple: bool = False) -> List[int]:
        """从列表中选择选项"""
        self.print_section(title, "")
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("", style=f"bold {self.theme.PRIMARY}")
        table.add_column("", style=self.theme.TEXT_PRIMARY)
        for i, option in enumerate(options, 1):
            table.add_row(f"{i}.", option)
        self.console.print(table)
        prompt = "请选择选项 (多选用逗号分隔)" if allow_multiple else "请选择选项"
        while True:
            try:
                selection = self.get_line_input(prompt)
                indices = [int(x.strip()) - 1 for x in selection.split(',')] if ',' in selection and allow_multiple else [int(selection) - 1]
                if all(0 <= i < len(options) for i in indices):
                    return indices
                else:
                    self.print_error("选择超出范围，请重新选择")
            except (ValueError, IndexError):
                self.print_error("输入无效，请输入数字")
                
    def show_progress(self, description: str):
        """显示进度信息"""
        self._ensure_rich()
        with self.console.status(f"[bold green]{description}...") as status:
            return status