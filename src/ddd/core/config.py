"""
配置管理核心模块
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """配置管理类"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / '.ddd'
        self.config_file = self.config_dir / 'config.yaml'
        self.plugins_dir = self.config_dir / 'plugins'
        
        # 确保配置目录存在
        self.config_dir.mkdir(exist_ok=True)
        self.plugins_dir.mkdir(exist_ok=True)
        
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                return {}
        return {}
        
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, 
                         ensure_ascii=False, indent=2)
        except Exception as e:
            raise Exception(f"保存配置失败: {e}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        
        # 创建嵌套字典结构
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """获取插件配置"""
        return self.get(f'plugins.{plugin_name}', {})
        
    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]):
        """设置插件配置"""
        self.set(f'plugins.{plugin_name}', config)
        
    @property
    def theme(self) -> str:
        """获取主题"""
        return self.get('ui.theme', 'dark')
        
    @theme.setter
    def theme(self, value: str):
        """设置主题"""
        self.set('ui.theme', value)
        
    @property
    def language(self) -> str:
        """获取语言"""
        return self.get('ui.language', 'zh')
        
    @language.setter  
    def language(self, value: str):
        """设置语言"""
        self.set('ui.language', value)
