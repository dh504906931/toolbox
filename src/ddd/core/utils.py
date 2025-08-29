"""
通用工具核心模块
"""

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Union


class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def ensure_dir(path: Union[str, Path]) -> Path:
        """确保目录存在"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
        
    @staticmethod
    def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """复制文件"""
        try:
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False
            
    @staticmethod
    def move_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """移动文件"""
        try:
            shutil.move(str(src), str(dst))
            return True
        except Exception:
            return False
            
    @staticmethod
    def delete_file(path: Union[str, Path]) -> bool:
        """删除文件"""
        try:
            Path(path).unlink()
            return True
        except Exception:
            return False
            
    @staticmethod
    def delete_dir(path: Union[str, Path]) -> bool:
        """删除目录"""
        try:
            shutil.rmtree(path)
            return True
        except Exception:
            return False
            
    @staticmethod
    def get_file_size(path: Union[str, Path]) -> int:
        """获取文件大小"""
        try:
            return Path(path).stat().st_size
        except Exception:
            return 0
            
    @staticmethod
    def format_size(size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
        
    @staticmethod
    def find_files(directory: Union[str, Path], pattern: str = "*", 
                  recursive: bool = True) -> List[Path]:
        """查找文件"""
        directory = Path(directory)
        if recursive:
            return list(directory.rglob(pattern))
        else:
            return list(directory.glob(pattern))


class SystemUtils:
    """系统操作工具类"""
    
    @staticmethod
    def get_platform_info() -> Dict[str, str]:
        """获取平台信息"""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
        }
        
    @staticmethod
    def is_windows() -> bool:
        """是否为Windows系统"""
        return platform.system().lower() == 'windows'
        
    @staticmethod
    def is_linux() -> bool:
        """是否为Linux系统"""
        return platform.system().lower() == 'linux'
        
    @staticmethod
    def is_macos() -> bool:
        """是否为macOS系统"""
        return platform.system().lower() == 'darwin'
        
    @staticmethod
    def run_command(command: Union[str, List[str]], 
                   cwd: Optional[Union[str, Path]] = None,
                   capture_output: bool = True,
                   timeout: Optional[int] = None) -> Dict[str, Any]:
        """运行系统命令"""
        try:
            if isinstance(command, str):
                shell = True
            else:
                shell = False
                
            result = subprocess.run(
                command,
                cwd=cwd,
                shell=shell,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }
            
    @staticmethod
    def get_env_var(name: str, default: str = "") -> str:
        """获取环境变量"""
        return os.environ.get(name, default)
        
    @staticmethod
    def set_env_var(name: str, value: str):
        """设置环境变量"""
        os.environ[name] = value
        
    @staticmethod
    def which(command: str) -> Optional[str]:
        """查找命令路径"""
        return shutil.which(command)
        
    @staticmethod
    def get_available_port(start_port: int = 8000) -> int:
        """获取可用端口"""
        import socket
        
        for port in range(start_port, start_port + 1000):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
                
        raise Exception("没有找到可用端口")
        
    @staticmethod
    def open_file_or_url(path: Union[str, Path]):
        """打开文件或URL"""
        if SystemUtils.is_windows():
            os.startfile(path)
        elif SystemUtils.is_macos():
            subprocess.run(['open', str(path)])
        else:  # Linux
            subprocess.run(['xdg-open', str(path)])
