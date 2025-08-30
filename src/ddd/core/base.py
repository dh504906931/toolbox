"""
DDD架构基础类定义
包含Page基类、Plugin基类等核心抽象
"""

import os
import sys
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass


@dataclass
class Option:
    """选项数据类"""
    key: str                    # 按键标识
    name: str                   # 显示名称
    description: str            # 描述信息
    icon: str = "🔧"           # 显示图标
    target: Union[str, Callable] = None  # 目标对象
    option_type: str = "page"   # 类型: page/plugin


class PageBase(ABC):
    """页面基类 - 处理交互逻辑"""
    
    def __init__(self, short_name: str, display_name: str, 
                 description: str, summary: str = "", icon: str = "📄"):
        self.short_name = short_name      # CLI标识
        self.display_name = display_name  # 显示名称
        self.description = description    # 详细描述
        self.summary = summary or description  # 简要介绍
        self.icon = icon                  # 显示图标
        self.path = ""                    # 在结构树中的路径
        self.options: List[Option] = []   # 选项列表
        
    @abstractmethod
    def initialize(self) -> None:
        """初始化页面 - 子类实现"""
        pass
        
    @abstractmethod
    def get_options(self) -> List[Option]:
        """获取当前页面的选项列表"""
        pass
        
    def run(self) -> None:
        """运行页面主循环"""
        from .renderer import Renderer
        renderer = Renderer()
        
        while True:
            try:
                # 渲染界面
                self.render_page(renderer)
                
                # 获取用户输入
                choice = self.get_user_choice(renderer)
                
                # 处理选择
                if not self.handle_choice(choice, renderer):
                    break
                    
            except KeyboardInterrupt:
                renderer.print_info("感谢使用 DDD 工具箱！")
                break
            except Exception as e:
                renderer.print_error(f"页面运行错误: {e}")
                self.wait_for_continue(renderer)
                
    def render_page(self, renderer) -> None:
        """渲染页面界面"""
        renderer.clear_screen()
        
        # 显示页面标题
        renderer.print_banner(
            title=self.display_name,
            subtitle=self.description,
            version="1.0.0"
        )
        
        # 获取并显示选项
        options = self.get_options()
        if options:
            # 转换为renderer期望的格式
            display_options = []
            for opt in options:
                display_options.append({
                    'key': opt.key,
                    'name': opt.name,
                    'description': opt.description,
                    'icon': opt.icon
                })
                
            table = renderer.print_menu(
                title="功能选项",
                options=display_options,
                show_help=True
            )
            renderer.console.print(table)
            renderer.console.print()
            
    def get_user_choice(self, renderer) -> str:
        """获取用户输入 - 支持单键输入"""
        from ..utils.input_utils import get_single_key_input
        return get_single_key_input("❯ 请选择功能 (数字键进入, - 返回, q 退出): ")
            
    def handle_choice(self, choice: str, renderer) -> bool:
        """处理用户选择"""
        # 退出命令
        if choice == 'q' or choice == 'quit':
            return False
            
        # 返回上级命令
        if choice == '-':
            return False  # 返回上级（退出当前页面）
        
        # 特殊处理双击*进入设置
        if choice == '*':
            return self._handle_page_settings(renderer)
            
        # 查找对应选项
        options = self.get_options()
        option = next((opt for opt in options if opt.key == choice), None)
        
        if not option:
            renderer.print_warning(f"无效的选择 '{choice}'，请重新输入")
            renderer.console.print("💡 提示: 按数字键选择功能，按 - 返回，按 q 退出，按 * 进入设置")
            self.wait_for_continue(renderer)
            return True
            
        # 根据选项类型处理
        if option.option_type == "page":
            # 跳转到子页面
            if isinstance(option.target, str):
                # 通过StructureManager获取页面实例
                from .structure import StructureManager
                structure = StructureManager()
                child_page = structure.get_page(option.target)
                if child_page:
                    child_page.run()
                else:
                    renderer.print_error(f"页面 {option.target} 未找到")
                    self.wait_for_continue(renderer)
            elif isinstance(option.target, PageBase):
                option.target.run()
                
        elif option.option_type == "plugin":
            # 处理页面设置特殊情况
            if option.target == "page_settings":
                return self._handle_page_settings(renderer)
            
            # 调用普通插件
            try:
                renderer.clear_screen()
                if callable(option.target):
                    option.target()
                elif hasattr(option.target, 'run'):
                    # 传递当前页面的节点ID给插件
                    node_id = self._get_current_node_id()
                    option.target.run(node_id=node_id)
                else:
                    renderer.print_warning("插件暂未实现")
                self.wait_for_continue(renderer)
            except Exception as e:
                renderer.print_error(f"执行插件时出错: {e}")
                self.wait_for_continue(renderer)
                
        return True
    
    def _handle_page_settings(self, renderer) -> bool:
        """处理页面设置功能"""
        from .structure import StructureManager
        structure = StructureManager()
        
        # 获取设置插件
        set_plugin = structure.get_plugin("set")
        if set_plugin:
            try:
                renderer.clear_screen()
                node_id = self._get_current_node_id()
                set_plugin.run(operation="interactive", node_id=node_id)
                self.wait_for_continue(renderer)
            except Exception as e:
                renderer.print_error(f"打开页面设置失败: {e}")
                self.wait_for_continue(renderer)
        else:
            renderer.print_error("设置插件未找到")
            self.wait_for_continue(renderer)
        
        return True
    
    def _get_current_node_id(self) -> str:
        """获取当前页面在结构树中的节点ID"""
        # 默认实现：返回页面的短名
        # 子类可以重写此方法提供更准确的节点ID
        return getattr(self, 'short_name', 'unknown')
        
    def wait_for_continue(self, renderer) -> None:
        """等待用户按键继续"""
        from ..utils.input_utils import get_single_key_input
        get_single_key_input("\n按任意键继续...")


class PluginBase(ABC):
    """插件基类 - 独立功能模块"""
    
    def __init__(self, name: str, summary: str, category: str = "general"):
        self.name = name           # 插件名称
        self.summary = summary     # 简要说明
        self.category = category   # 功能分类
        
    @abstractmethod
    def run(self, **kwargs) -> Any:
        """执行插件功能 - 接收参数，返回结果"""
        pass
        
    def get_help(self) -> str:
        """获取插件帮助信息"""
        return f"{self.name}: {self.summary}"
        
    def validate_params(self, **kwargs) -> bool:
        """验证参数有效性 - 子类可重写"""
        return True
