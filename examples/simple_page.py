"""
简单页面示例
演示基本的页面开发模式
"""

from ddd.core.base import PageBase
from typing import List, Dict


class SimplePage(PageBase):
    """简单页面示例"""
    
    def get_title(self) -> str:
        return "简单页面示例"
    
    def get_description(self) -> str:
        return "演示基本页面功能"
    
    def get_default_children(self) -> List[Dict]:
        """定义默认子项"""
        return [
            {
                "type": "plugin",
                "name": "simple_plugin",
                "description": "简单插件"
            },
            {
                "type": "plugin", 
                "name": "calculator_plugin",
                "description": "计算器"
            }
        ]
    
    def get_content(self) -> str:
        """页面内容"""
        return """
🎯 这是一个简单页面示例

功能:
  • 演示页面基本结构
  • 展示插件集成方式
  • 提供开发参考

使用说明:
  • 选择下面的选项来使用插件
  • 按 * 键进入页面设置
  • 按 0 键返回上级
"""


class DynamicPage(PageBase):
    """动态页面示例"""
    
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.items = []
    
    def get_title(self) -> str:
        return f"动态页面 (计数: {self.counter})"
    
    def get_description(self) -> str:
        return "演示动态内容更新"
    
    def get_default_children(self) -> List[Dict]:
        return [
            {
                "type": "plugin",
                "name": "add_item_plugin", 
                "description": "添加项目"
            },
            {
                "type": "plugin",
                "name": "clear_items_plugin",
                "description": "清空项目"
            }
        ]
    
    def get_content(self) -> str:
        """动态内容"""
        content = [
            "🔄 动态页面示例",
            f"📊 当前计数: {self.counter}",
            f"📝 项目数量: {len(self.items)}"
        ]
        
        if self.items:
            content.append("\n📋 项目列表:")
            for i, item in enumerate(self.items, 1):
                content.append(f"  {i}. {item}")
        else:
            content.append("\n📝 暂无项目")
        
        return "\n".join(content)
    
    def refresh_data(self):
        """刷新数据"""
        self.counter += 1
    
    def add_item(self, item: str):
        """添加项目"""
        self.items.append(item)
        self.refresh_data()
    
    def clear_items(self):
        """清空项目"""
        self.items.clear()
        self.refresh_data()


class MenuPage(PageBase):
    """菜单页面示例"""
    
    def get_title(self) -> str:
        return "菜单页面示例"
    
    def get_description(self) -> str:
        return "演示复杂菜单结构"
    
    def get_default_children(self) -> List[Dict]:
        return [
            {
                "type": "page",
                "name": "sub_page_1",
                "description": "子页面 1"
            },
            {
                "type": "page", 
                "name": "sub_page_2",
                "description": "子页面 2"
            },
            {
                "type": "plugin",
                "name": "utility_plugin",
                "description": "工具插件"
            }
        ]
    
    def get_content(self) -> str:
        return """
📚 菜单页面示例

结构:
  📄 子页面 1 - 基础功能演示
  📄 子页面 2 - 高级功能演示  
  🔧 工具插件 - 实用工具集合

导航:
  • 使用数字键选择选项
  • 按 * 键管理页面设置
  • 按 0 键返回上级菜单
"""


class ConfigurablePage(PageBase):
    """可配置页面示例"""
    
    def __init__(self):
        super().__init__()
        self.load_config()
    
    def get_title(self) -> str:
        title = self.config.get("title", "可配置页面")
        return f"{title} (v{self.config.get('version', '1.0')})"
    
    def get_description(self) -> str:
        return self.config.get("description", "演示配置系统")
    
    def get_default_children(self) -> List[Dict]:
        return [
            {
                "type": "plugin",
                "name": "config_plugin",
                "description": "配置管理"
            },
            {
                "type": "plugin",
                "name": "theme_plugin", 
                "description": "主题设置"
            }
        ]
    
    def load_config(self):
        """加载配置"""
        import json
        from pathlib import Path
        
        config_file = Path.home() / ".ddd_toolbox" / "configurable_page.json"
        
        if config_file.exists():
            try:
                self.config = json.loads(config_file.read_text())
            except:
                self.config = self.get_default_config()
        else:
            self.config = self.get_default_config()
    
    def get_default_config(self) -> dict:
        """默认配置"""
        return {
            "title": "可配置页面",
            "description": "演示配置系统",
            "version": "1.0",
            "theme": "default",
            "max_items": 10
        }
    
    def save_config(self):
        """保存配置"""
        import json
        from pathlib import Path
        
        config_dir = Path.home() / ".ddd_toolbox"
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / "configurable_page.json"
        config_file.write_text(json.dumps(self.config, indent=2))
    
    def get_content(self) -> str:
        """显示配置信息"""
        content = [
            "⚙️ 可配置页面示例",
            "",
            "📋 当前配置:"
        ]
        
        for key, value in self.config.items():
            content.append(f"  • {key}: {value}")
        
        content.extend([
            "",
            "💡 使用配置管理插件修改设置",
            "💡 设置会自动保存到用户目录"
        ])
        
        return "\n".join(content)
