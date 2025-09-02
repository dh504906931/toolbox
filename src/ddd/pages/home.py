"""
主页 - DDD工具箱的首页
"""

from typing import List, Dict
from ddd.core.base import PageBase, Option
from ddd.ui_handler.handler_base import get_ui_handler
from ddd.core.structure import StructureManager


class HomePage(PageBase):
    """主页面 - 应用程序入口"""

    def __init__(self):
        super().__init__(
            name="home",
            display_name="DDD 开发工具箱",
            description="可拓展工具集合",
            summary="主页面，显示所有可用的工具和功能",
            icon="🏠",
        )

    def initialize(self) -> None:
        """初始化主页 - 不再用于注册，仅用于运行时初始化"""
        pass

    def get_default_children(self) -> List[Dict]:
        """定义此页面的默认子项 - 仅在构建结构树时使用"""
        return [
            {"type": "plugin", "name": "cd", "description": "管理常用路径的短名映射"},
        ]

    def get_options(self) -> List[Option]:
        """获取主页的选项列表"""
        structure = StructureManager()
        options = []

        # 从结构管理器获取启用的子项
        children = structure.get_enabled_children("home")

        # 转换为选项格式
        for i, child in enumerate(children):
            if child.get('type') == 'page':
                options.append(Option(
                    key=str(i + 1),  # 数字键
                    name=child.get('display_name', child.get('name')),
                    description="快速跳转到页面",
                    icon=child.get('icon', '📄'),
                    target=child.get('name'),
                    option_type='page'
                ))
            elif child.get('type') == 'plugin':
                # 从插件实例获取目标
                plugin_instance = structure.get_plugin(child.get('name'))
                options.append(Option(
                    key=str(i + 1),  # 数字键
                    name=child.get('name'),
                    description="快速跳转到常用路径",
                    icon="🔌",
                    target=plugin_instance,  # 直接传递插件实例
                    option_type='plugin'
                ))

        # 不再在选项列表中添加设置选项，设置通过双击*进入（在帮助信息中说明）
        return options
