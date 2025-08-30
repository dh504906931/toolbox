"""
DDD 领域驱动设计工具箱

一个美观、易用的TUI界面工具箱，专为DDD开发者打造。
基于全新的Page-Plugin架构，提供灵活的功能扩展。

特色：
- 🎨 精美的TUI界面，支持彩色输出  
- 🏗️ Page-Plugin分离架构，职责清晰
- 📱 直观的交互体验，支持单键操作
- ⚡ 模块化设计，易于扩展
- 🌳 树状结构管理，层次清晰

Author: DH
Version: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "DH"

# 导入核心模块
from .core.renderer import Renderer, Theme
from .core.base import PageBase, PluginBase
from .core.structure import StructureManager

# 延迟导入cli模块以避免依赖问题
def get_main():
    from .cli import cli_main
    return cli_main

main = get_main
