"""
美观的UI界面核心模块
"""

import os
import sys
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.align import Align
from rich.padding import Padding
from rich import box
from colorama import init, Fore, Back, Style

# 初始化colorama以支持Windows彩色输出
init()

class Theme:
    """主题配置类"""
    
    # 主色调
    PRIMARY = "#00d4aa"      # 青绿色
    SECONDARY = "#0ea5e9"    # 蓝色
    SUCCESS = "#22c55e"      # 绿色
    WARNING = "#f59e0b"      # 橙色
    DANGER = "#ef4444"       # 红色
    INFO = "#6366f1"         # 紫色
    
    # 文本颜色
    TEXT_PRIMARY = "#f8fafc"    # 白色
    TEXT_SECONDARY = "#94a3b8"  # 灰色
    TEXT_MUTED = "#64748b"      # 暗灰色
    
    # 背景色
    BG_DARK = "#0f172a"      # 深色背景
    BG_CARD = "#1e293b"      # 卡片背景
    BG_SUBTLE = "#334155"    # 微妙背景
    
    # 边框
    BORDER = "#475569"       # 边框色


class UI:
    """统一的UI界面类"""
    
    def __init__(self):
        self.console = Console()
        self.theme = Theme()
        
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_banner(self, title: str, subtitle: str = "", version: str = ""):
        """显示标题横幅"""
        banner_text = Text()
        banner_text.append("🚀 ", style="bold cyan")
        banner_text.append(title, style=f"bold {self.theme.PRIMARY}")
        
        if version:
            banner_text.append(f" v{version}", style=f"{self.theme.TEXT_SECONDARY}")
            
        if subtitle:
            banner_text.append(f"\n{subtitle}", style=f"{self.theme.TEXT_MUTED}")
            
        panel = Panel(
            Align.center(banner_text),
            box=box.DOUBLE,
            style=self.theme.PRIMARY,
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
        
    def print_menu(self, title: str, options: List[Dict[str, Any]], 
                   show_help: bool = True) -> Table:
        """显示美观的菜单"""
        table = Table(
            title=f"📋 {title}",
            title_style=f"bold {self.theme.SECONDARY}",
            box=box.ROUNDED,
            border_style=self.theme.BORDER,
            show_header=True,
            header_style=f"bold {self.theme.TEXT_PRIMARY}",
            title_justify="left",
            expand=True,
            padding=(0, 1)
        )
        
        table.add_column("选项", style=f"bold {self.theme.PRIMARY}", width=8)
        table.add_column("功能", style=self.theme.TEXT_PRIMARY, min_width=20)
        table.add_column("描述", style=self.theme.TEXT_SECONDARY, min_width=30)
        
        for option in options:
            key = option.get('key', '')
            name = option.get('name', '')
            desc = option.get('description', '')
            
            # 添加图标
            icon = option.get('icon', '🔧')
            name_with_icon = f"{icon} {name}"
            
            table.add_row(
                f"[{key}]",
                name_with_icon,
                desc
            )
            
        if show_help:
            table.add_row(
                "[q]",
                "🚪 退出",
                "退出程序"
            )
            
        return table
        
    def print_success(self, message: str):
        """显示成功消息"""
        panel = Panel(
            f"✅ {message}",
            style=self.theme.SUCCESS,
            box=box.ROUNDED
        )
        self.console.print(panel)
        
    def print_error(self, message: str):
        """显示错误消息"""
        panel = Panel(
            f"❌ {message}",
            style=self.theme.DANGER,
            box=box.ROUNDED
        )
        self.console.print(panel)
        
    def print_warning(self, message: str):
        """显示警告消息"""
        panel = Panel(
            f"⚠️ {message}",
            style=self.theme.WARNING,
            box=box.ROUNDED
        )
        self.console.print(panel)
        
    def print_info(self, message: str):
        """显示信息消息"""
        panel = Panel(
            f"ℹ️ {message}",
            style=self.theme.INFO,
            box=box.ROUNDED
        )
        self.console.print(panel)
        
    def print_section(self, title: str, content: str):
        """显示章节内容"""
        panel = Panel(
            content,
            title=f"📝 {title}",
            title_align="left",
            style=self.theme.BG_CARD,
            border_style=self.theme.BORDER,
            box=box.ROUNDED
        )
        self.console.print(panel)
        
    def get_input(self, prompt: str, default: str = "") -> str:
        """获取用户输入"""
        prompt_text = Text()
        prompt_text.append("❯ ", style=f"bold {self.theme.PRIMARY}")
        prompt_text.append(prompt, style=self.theme.TEXT_PRIMARY)
        
        if default:
            prompt_text.append(f" [{default}]", style=self.theme.TEXT_SECONDARY)
            
        prompt_text.append(": ", style=self.theme.TEXT_PRIMARY)
        
        self.console.print(prompt_text, end="")
        
        try:
            user_input = input().strip()
            return user_input if user_input else default
        except KeyboardInterrupt:
            self.console.print("\n👋 再见!")
            sys.exit(0)
            
    def confirm(self, message: str, default: bool = False) -> bool:
        """确认对话框"""
        default_text = "Y/n" if default else "y/N"
        response = self.get_input(f"{message} ({default_text})", 
                                 "y" if default else "n")
        return response.lower().startswith('y')
        
    def select_from_list(self, title: str, options: List[str], 
                        allow_multiple: bool = False) -> List[int]:
        """从列表中选择选项"""
        self.print_section(title, "")
        
        table = Table(
            box=box.SIMPLE,
            show_header=False,
            padding=(0, 1)
        )
        table.add_column("", style=f"bold {self.theme.PRIMARY}")
        table.add_column("", style=self.theme.TEXT_PRIMARY)
        
        for i, option in enumerate(options, 1):
            table.add_row(f"{i}.", option)
            
        self.console.print(table)
        
        if allow_multiple:
            prompt = "请选择选项 (多选用逗号分隔)"
        else:
            prompt = "请选择选项"
            
        while True:
            try:
                selection = self.get_input(prompt)
                
                if ',' in selection and allow_multiple:
                    indices = [int(x.strip()) - 1 for x in selection.split(',')]
                else:
                    indices = [int(selection) - 1]
                    
                # 验证选择
                if all(0 <= i < len(options) for i in indices):
                    return indices
                else:
                    self.print_error("选择超出范围，请重新选择")
                    
            except (ValueError, IndexError):
                self.print_error("输入无效，请输入数字")
                
    def show_progress(self, description: str):
        """显示进度信息"""
        with self.console.status(f"[bold green]{description}...") as status:
            return status
