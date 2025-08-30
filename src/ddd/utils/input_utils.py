"""
跨平台输入工具模块
解决Windows/WSL/Linux下终端输入的兼容性问题
"""

import sys
import platform


def get_single_key_input(prompt: str = "") -> str:
    """
    跨平台单键输入函数
    
    Args:
        prompt: 提示信息
        
    Returns:
        str: 用户输入的单个字符（转为小写）
    """
    if prompt:
        print(prompt, end="", flush=True)
    
    system = platform.system().lower()
    
    if system == "windows":
        # Windows系统使用msvcrt
        try:
            import msvcrt
            while True:
                try:
                    key = msvcrt.getch()
                    if isinstance(key, bytes):
                        key = key.decode('utf-8', errors='ignore')
                    if key and key.isprintable():
                        print(key)  # 显示用户输入
                        return key.lower()
                except (UnicodeDecodeError, AttributeError):
                    continue
        except ImportError:
            # 如果msvcrt不可用，回退到普通输入
            return _fallback_input()
    
    else:
        # Unix/Linux/WSL系统
        try:
            import termios
            import tty
            
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            try:
                # 尝试使用cbreak模式
                if hasattr(tty, 'cbreak'):
                    tty.cbreak(fd)
                elif hasattr(tty, 'setcbreak'):
                    tty.setcbreak(fd)
                else:
                    # 如果没有cbreak方法，回退到普通输入
                    return _fallback_input()
                    
                key = sys.stdin.read(1)
                if key:
                    print(key)  # 显示用户输入
                    return key.lower()
                else:
                    return _fallback_input()
                    
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                
        except (ImportError, OSError, AttributeError) as e:
            # 如果termios不可用或出错，回退到普通输入
            print(f"\n⚠️  终端模式不支持，使用标准输入 ({e})")
            return _fallback_input()


def _fallback_input() -> str:
    """
    回退输入方法，使用标准输入
    """
    try:
        key = input().strip()
        return key.lower() if key else ""
    except (KeyboardInterrupt, EOFError):
        return "q"  # Ctrl+C 或 EOF 时退出


def get_line_input(prompt: str = "") -> str:
    """
    获取一行输入
    
    Args:
        prompt: 提示信息
        
    Returns:
        str: 用户输入的字符串
    """
    try:
        return input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        return ""


def confirm_action(prompt: str, default: bool = False) -> bool:
    """
    确认操作
    
    Args:
        prompt: 提示信息
        default: 默认值
        
    Returns:
        bool: 用户确认结果
    """
    suffix = " [Y/n]" if default else " [y/N]"
    response = get_line_input(prompt + suffix).lower()
    
    if not response:
        return default
    
    return response in ['y', 'yes', '是', '确认']
