"""
日志管理核心模块
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler


class Logger:
    """日志管理类"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self, log_dir: Optional[Path] = None, level: str = "INFO"):
        if hasattr(self, '_initialized'):
            return
            
        self.log_dir = log_dir or Path.home() / '.ddd' / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志级别
        self.level = getattr(logging, level.upper(), logging.INFO)
        
        # 创建logger
        self.logger = logging.getLogger('ddd')
        self.logger.setLevel(self.level)
        
        # 避免重复添加handler
        if not self.logger.handlers:
            self._setup_handlers()
            
        self._initialized = True
        
    def _setup_handlers(self):
        """设置日志处理器"""
        # 控制台处理器 (使用Rich)
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_time=False,
            show_path=False
        )
        console_handler.setLevel(self.level)
        
        # 文件处理器
        log_file = self.log_dir / 'ddd.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 设置格式
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # 添加处理器
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
    def debug(self, message: str):
        """调试日志"""
        self.logger.debug(message)
        
    def info(self, message: str):
        """信息日志"""
        self.logger.info(message)
        
    def warning(self, message: str):
        """警告日志"""
        self.logger.warning(message)
        
    def error(self, message: str):
        """错误日志"""
        self.logger.error(message)
        
    def critical(self, message: str):
        """严重错误日志"""
        self.logger.critical(message)
        
    def exception(self, message: str):
        """异常日志"""
        self.logger.exception(message)
