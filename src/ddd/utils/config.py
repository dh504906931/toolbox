"""
配置路径管理工具
支持开发期间使用代码仓库路径，生产环境使用用户目录
"""

import os
import sys
from pathlib import Path
from typing import Optional


class ConfigManager:
    """配置路径管理器"""
    
    def __init__(self, custom_config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            custom_config_dir: 自定义配置目录路径
        """
        self._custom_config_dir = custom_config_dir
        self._config_dir = None
        self._ensure_config_dir()
    
    def _ensure_config_dir(self) -> None:
        """确保配置目录存在"""
        config_dir = self.get_config_dir()
        os.makedirs(config_dir, exist_ok=True)
    
    def get_config_dir(self) -> str:
        """
        获取配置目录路径
        
        优先级:
        1. 自定义路径 (custom_config_dir)
        2. 环境变量 DDD_CONFIG_DIR
        3. 开发模式: 代码仓库中的 .ddd_config/
        4. 生产模式: 用户主目录 ~/.ddd_toolbox/
        """
        if self._config_dir:
            return self._config_dir
        
        # 1. 自定义路径
        if self._custom_config_dir:
            self._config_dir = os.path.expanduser(self._custom_config_dir)
            return self._config_dir
        
        # 2. 环境变量
        env_config_dir = os.environ.get('DDD_CONFIG_DIR')
        if env_config_dir:
            self._config_dir = os.path.expanduser(env_config_dir)
            return self._config_dir
        
        # 3. 检测是否在开发模式
        if self._is_development_mode():
            # 开发模式：使用代码仓库中的配置目录
            project_root = self._get_project_root()
            self._config_dir = os.path.join(project_root, '.ddd_config')
            return self._config_dir
        
        # 4. 生产模式：使用用户主目录
        self._config_dir = os.path.expanduser("~/.ddd_toolbox")
        return self._config_dir
    
    def _is_development_mode(self) -> bool:
        """
        检测是否处于开发模式
        
        判断条件:
        1. 能找到项目根目录且包含 pyproject.toml
        2. 运行的 Python 文件在项目目录内
        """
        try:
            project_root = self._get_project_root()
            if not project_root:
                return False
            
            # 检查是否有 pyproject.toml
            pyproject_file = os.path.join(project_root, 'pyproject.toml')
            if not os.path.exists(pyproject_file):
                return False
            
            # 检查当前运行的脚本是否在项目目录内
            current_script = os.path.abspath(sys.argv[0])
            return current_script.startswith(project_root)
            
        except Exception:
            return False
    
    def _get_project_root(self) -> Optional[str]:
        """
        获取项目根目录路径
        
        从当前文件位置向上查找，直到找到包含 pyproject.toml 的目录
        """
        try:
            # 从当前文件开始向上查找
            current_path = Path(__file__).resolve()
            
            for parent in current_path.parents:
                pyproject_file = parent / 'pyproject.toml'
                if pyproject_file.exists():
                    return str(parent)
            
            return None
        except Exception:
            return None
    
    def get_structure_file(self) -> str:
        """获取结构树文件路径"""
        return os.path.join(self.get_config_dir(), "structure.json")
    
    def get_paths_file(self) -> str:
        """获取路径配置文件路径"""
        return os.path.join(self.get_config_dir(), "paths.json")
    
    def get_plugins_config_file(self) -> str:
        """获取插件配置文件路径"""
        return os.path.join(self.get_config_dir(), "plugins.json")
    
    def is_development_mode(self) -> bool:
        """公开的开发模式检测方法"""
        return self._is_development_mode()
    
    def get_project_root(self) -> Optional[str]:
        """公开的项目根目录获取方法"""
        return self._get_project_root()
    
    def set_custom_config_dir(self, config_dir: str) -> None:
        """设置自定义配置目录"""
        self._custom_config_dir = config_dir
        self._config_dir = None  # 重置缓存
        self._ensure_config_dir()
    
    def get_info(self) -> dict:
        """获取配置信息（调试用）"""
        return {
            "config_dir": self.get_config_dir(),
            "is_development_mode": self.is_development_mode(),
            "project_root": self.get_project_root(),
            "custom_config_dir": self._custom_config_dir,
            "structure_file": self.get_structure_file(),
            "paths_file": self.get_paths_file(),
            "plugins_config_file": self.get_plugins_config_file()
        }


# 全局配置管理器实例
_config_manager = None


def get_config_manager(custom_config_dir: Optional[str] = None) -> ConfigManager:
    """
    获取全局配置管理器实例
    
    Args:
        custom_config_dir: 自定义配置目录（仅在首次调用时有效）
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(custom_config_dir)
    return _config_manager


def set_config_dir(config_dir: str) -> None:
    """设置全局配置目录"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_dir)
    else:
        _config_manager.set_custom_config_dir(config_dir)


def get_config_dir() -> str:
    """获取当前配置目录"""
    return get_config_manager().get_config_dir()


def get_structure_file() -> str:
    """获取结构树文件路径"""
    return get_config_manager().get_structure_file()


def get_paths_file() -> str:
    """获取路径配置文件路径"""
    return get_config_manager().get_paths_file()


def is_development_mode() -> bool:
    """检测是否处于开发模式"""
    return get_config_manager().is_development_mode()
