"""
插件基类和插件管理器的实现
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import importlib
import pkgutil
import yaml
from pathlib import Path


class Plugin(ABC):
    """插件基类"""
    
    def __init__(self):
        self.subplugins: Dict[str, 'Plugin'] = {}
    
    @abstractmethod
    def run(self) -> None:
        """运行插件主要功能"""
        pass


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        
    def register_plugin(self, name: str, plugin: Plugin) -> None:
        """注册插件"""
        self.plugins[name] = plugin
        
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """获取指定名称的插件"""
        return self.plugins.get(name)
        
    def run_plugin(self, name: str) -> None:
        """运行指定插件"""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.run()
        else:
            raise Exception(f"插件 '{name}' 未找到")
