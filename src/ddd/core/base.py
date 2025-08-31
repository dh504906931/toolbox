"""
DDD架构基础类定义
包含Page基类、Plugin基类等核心抽象
"""

import sys
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Callable, TYPE_CHECKING
from dataclasses import dataclass

# 使用TYPE_CHECKING来避免循环导入，同时为IDE提供类型提示
if TYPE_CHECKING:
    from .renderer import Renderer

@dataclass
class Option:
    """选项数据类"""
    key: str
    name: str
    description: str
    icon: str = "🔧"
    target: Union[str, Callable] = None
    option_type: str = "page"

class PageBase(ABC):
    """页面基类 - 处理交互逻辑"""
    
    def __init__(self, name: str, display_name: str, description: str, summary: str = "", icon: str = "📄"):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.summary = summary or description
        self.icon = icon
        self.options: List[Option] = []
        
    @abstractmethod
    def initialize(self) -> None:
        """初始化页面 - 子类实现"""
        pass
        
    @abstractmethod
    def get_options(self) -> List[Option]:
        """获取当前页面的选项列表"""
        pass
        
    def run(self, is_cli_launch: bool = False, cli_args: List[str] = None) -> None:
        """
        运行页面主循环
        :param is_cli_launch: 标记是否由CLI直接启动，如果是，则返回上一级时应直接退出程序
        :param cli_args: 从CLI传入的额外参数
        """
        renderer = get_renderer()
        
        while True:
            try:
                self.render_page(renderer)
                choice = self.get_user_choice(renderer)
                
                # 修改 handle_choice 的返回逻辑
                should_continue = self.handle_choice(choice, renderer, is_cli_launch=is_cli_launch)
                
                if not should_continue:
                    break
                    
            except KeyboardInterrupt:
                renderer.print_info("感谢使用 DDD 工具箱！")
                break
            except Exception as e:
                renderer.print_error(f"页面运行错误: {e}")
                self.wait_for_continue(renderer)
                
    def render_page(self, renderer: 'Renderer') -> None:
        """渲染页面界面"""
        renderer.clear_screen()
        renderer.print_banner(title=self.display_name, subtitle=self.description, version="1.0.0")
        options = self.get_options()
        if options:
            display_options = [{'key': o.key, 'name': o.name, 'description': o.description,  'icon': o.icon} for o in options]
            table = renderer.print_menu(title="选项列表", options=display_options, show_help=True)
            renderer.console.print(table)
        renderer.print_help_info()
            
    def get_user_choice(self, renderer: 'Renderer') -> str:
        """
        【已修改】获取用户输入 - 完全委托给Renderer处理
        """
        # 页面层不再关心输入的实现细节（如双击）
        return renderer.get_menu_input("请选择功能: ")
            
    def handle_choice(self, choice: str, renderer: 'Renderer', is_cli_launch: bool = False) -> bool:
        """
        处理用户选择
        :param is_cli_launch: 如果是由CLI直接启动的页面，按'-'返回应该直接退出
        :return: bool, 是否继续当前页面的循环
        """
        if choice == 'q' or choice == 'quit':
            sys.exit(0) # 任何地方按q都直接退出程序
            
        if choice == '-':
            if is_cli_launch:
                # 如果是CLI直接启动的，返回就意味着退出
                sys.exit(0)
            return False  # 返回上级（退出当前页面循环）
        
        # 直接处理renderer返回的特殊命令
        if choice == '*double':
            return self._handle_page_settings(renderer)
            
        options = self.get_options()
        option = next((opt for opt in options if opt.key == choice), None)
        
        if not option:
            if choice and choice != '*': # 避免单击*时也报无效
                renderer.print_warning(f"无效的选择 '{choice}'，请重新输入")
                self.wait_for_continue(renderer)
            elif choice == '*':
                # 单击*号给出提示
                renderer.print_info("💡 提示：双击 * 号可以进入页面设置")
                self.wait_for_continue(renderer)
            return True
        if option.option_type == "page":
            from .structure import StructureManager
            structure = StructureManager()
            child_page = structure.get_page(option.target) if isinstance(option.target, str) else option.target
            if child_page:
                child_page.run()
            else:
                renderer.print_error(f"页面 {option.target} 未找到")
                self.wait_for_continue(renderer)
        elif option.option_type == "plugin":
            try:
                renderer.clear_screen()
                if callable(option.target):
                    option.target()
                elif hasattr(option.target, 'run'):
                    node_id = self._get_current_node_id()
                    option.target.run(node_id=node_id)
                else:
                    renderer.print_warning("插件暂未实现")
                    self.wait_for_continue(renderer)
                # 移除强制等待 - 让插件自己决定是否需要等待
            except Exception as e:
                renderer.print_error(f"执行插件时出错: {e}")
                self.wait_for_continue(renderer)
                
        return True
    
    def _handle_page_settings(self, renderer: 'Renderer') -> bool:
        """处理页面设置功能"""
        from .structure import StructureManager
        structure = StructureManager()
        set_plugin = structure.get_plugin("setting")
        if set_plugin:
            try:
                renderer.clear_screen()
                node_id = self._get_current_node_id()
                set_plugin.run(operation="interactive", node_id=node_id)
                # 移除强制等待 - 让插件自己决定是否需要等待
            except Exception as e:
                renderer.print_error(f"打开页面设置失败: {e}")
                self.wait_for_continue(renderer)
        else:
            renderer.print_error("设置插件未找到")
            self.wait_for_continue(renderer)
        return True
    
    def _get_current_node_id(self) -> str:
        return getattr(self, 'name', 'unknown')
        
    def wait_for_continue(self, renderer: 'Renderer') -> None:
        """
        【已修改】等待用户按键继续 - 使用Renderer的新方法
        """
        renderer.wait_for_any_key()

class PluginBase(ABC):
    """插件基类 - 独立功能模块"""
    def __init__(self, name: str, summary: str, category: str = "general"):
        self.name = name
        self.summary = summary
        self.category = category
        
    @abstractmethod
    def run(self, operation: str = "interactive", args: List[str] = None, **kwargs) -> Any:
        """
        执行插件功能
        :param operation: 操作模式 ("interactive", "cli", "api")
        :param args: 命令行传入的位置参数列表  
        :param kwargs: 其他上下文信息，例如 node_id
        """
        pass
    
    def get_help(self) -> str:
        return f"{self.name}: {self.summary}"
        
    def validate_params(self, **kwargs) -> bool:
        return True


# 全局renderer实例，所有page共用
_global_renderer = None

def get_renderer():
    """获取全局renderer实例"""
    global _global_renderer
    if _global_renderer is None:
        from .renderer import Renderer
        _global_renderer = Renderer()
    return _global_renderer