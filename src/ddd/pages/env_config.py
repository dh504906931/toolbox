"""
环境配置页面 - 演示不同的类命名约定
"""

from typing import List, Dict
from ..core.base import PageBase, Option


class EnvironmentConfigPage(PageBase):
    """环境配置页面 - 使用完整的类名而不是约定的后缀"""
    
    def __init__(self):
        super().__init__(
            name="env_config",
            display_name="环境配置",
            description="管理开发环境配置",
            summary="环境变量和配置管理",
            icon="🌍"
        )
        
    def initialize(self) -> None:
        """初始化环境配置页面"""
        pass
    
    def get_default_children(self) -> List[Dict]:
        """定义此页面的默认子项"""
        return []
        
    def get_options(self) -> List[Option]:
        """获取环境配置选项列表"""
        return [
            Option(
                key="1",
                name="查看环境变量",
                description="显示当前环境变量",
                short_name="查看",
                icon="👁️",
                target="view_env",
                option_type="action"
            ),
            Option(
                key="2",
                name="设置环境变量",
                description="设置新的环境变量",
                short_name="设置",
                icon="⚙️",
                target="set_env",
                option_type="action"
            )
        ]
