"""
主页 - DDD工具箱的首页
"""

from typing import List, Dict
from ..core.base import PageBase, Option
from ..core.structure import StructureManager


class HomePage(PageBase):
    """主页面 - 应用程序入口"""
    
    def __init__(self):
        super().__init__(
            short_name="home",
            display_name="DDD 开发工具箱",
            description="领域驱动设计开发者工具集合",
            summary="主页面，显示所有可用的工具和功能",
            icon="🏠"
        )
        
    def initialize(self) -> None:
        """初始化主页 - 不再用于注册，仅用于运行时初始化"""
        # 新设计下，页面初始化不再负责注册子项
        # 子项关系由结构管理器从get_default_children方法获取
        pass
    
    def get_default_children(self) -> List[Dict]:
        """定义此页面的默认子项 - 仅在构建结构树时使用"""
        return [
            {
                "type": "plugin",
                "name": "path", 
                "description": "管理常用路径的短名映射"
            },
            # 可以在这里添加更多默认子项
            # {
            #     "type": "page", 
            #     "name": "dev_tools",
            #     "description": "开发工具集合"
            # }
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
                    description=child.get('description', ''),
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
                    description=child.get('summary', ''),
                    icon="🔌",
                    target=plugin_instance,  # 直接传递插件实例
                    option_type='plugin'
                ))
        
        # 添加特殊的设置功能（双击*进入）
        if options:  # 只有当有其他选项时才添加
            options.append(Option(
                key="*",
                name="页面设置",
                description="双击*进入页面结构设置",
                icon="⚙️",
                target="page_settings",
                option_type="plugin"
            ))
            
        return options
