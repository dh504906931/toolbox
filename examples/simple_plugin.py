"""
简单插件示例
演示基本的插件开发模式
"""

from ddd.core.base import PluginBase
from typing import Any


class SimplePlugin(PluginBase):
    """简单插件示例"""
    
    def get_description(self) -> str:
        return "一个简单的示例插件"
    
    def run(self, **kwargs) -> Any:
        """插件主要功能"""
        print("🎉 欢迎使用简单插件!")
        print("这是一个基本的插件示例")
        
        # 返回结果
        return "插件执行完成"


class CalculatorPlugin(PluginBase):
    """计算器插件示例"""
    
    def get_description(self) -> str:
        return "简单计算器"
    
    def run(self, **kwargs) -> Any:
        """计算器功能"""
        from ddd.utils.input_utils import get_user_input
        
        try:
            print("🧮 简单计算器")
            print("支持基本四则运算")
            
            expression = get_user_input("请输入表达式 (如: 2 + 3): ")
            
            # 简单的安全性检查
            allowed_chars = "0123456789+-*/.() "
            if not all(c in allowed_chars for c in expression):
                return "❌ 包含不允许的字符"
            
            result = eval(expression)
            return f"✅ 结果: {expression} = {result}"
            
        except Exception as e:
            return f"❌ 计算错误: {e}"


class FileManagerPlugin(PluginBase):
    """文件管理插件示例"""
    
    def get_description(self) -> str:
        return "简单文件管理器"
    
    def run(self, **kwargs) -> Any:
        """文件管理功能"""
        from pathlib import Path
        from ddd.utils.input_utils import get_user_input
        
        print("📁 文件管理器")
        print("1. 列出文件")
        print("2. 创建目录") 
        print("3. 删除文件")
        
        choice = get_user_input("请选择操作 (1-3): ")
        
        if choice == "1":
            return self._list_files()
        elif choice == "2":
            return self._create_directory()
        elif choice == "3":
            return self._delete_file()
        else:
            return "❌ 无效选择"
    
    def _list_files(self):
        """列出当前目录文件"""
        try:
            current_dir = Path.cwd()
            files = list(current_dir.iterdir())
            
            result = [f"📂 当前目录: {current_dir}"]
            result.append(f"📊 共 {len(files)} 个项目:")
            
            for file in sorted(files):
                icon = "📁" if file.is_dir() else "📄"
                result.append(f"  {icon} {file.name}")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ 列出文件失败: {e}"
    
    def _create_directory(self):
        """创建目录"""
        from ddd.utils.input_utils import get_user_input
        
        try:
            dir_name = get_user_input("目录名: ")
            if not dir_name:
                return "❌ 目录名不能为空"
            
            new_dir = Path.cwd() / dir_name
            if new_dir.exists():
                return f"❌ 目录已存在: {dir_name}"
            
            new_dir.mkdir()
            return f"✅ 创建目录成功: {dir_name}"
            
        except Exception as e:
            return f"❌ 创建目录失败: {e}"
    
    def _delete_file(self):
        """删除文件"""
        from ddd.utils.input_utils import get_user_input
        
        try:
            file_name = get_user_input("要删除的文件名: ")
            if not file_name:
                return "❌ 文件名不能为空"
            
            file_path = Path.cwd() / file_name
            if not file_path.exists():
                return f"❌ 文件不存在: {file_name}"
            
            confirm = get_user_input(f"确定删除 {file_name}? (y/n): ")
            if confirm.lower() != 'y':
                return "❌ 已取消删除"
            
            if file_path.is_dir():
                file_path.rmdir()  # 只能删除空目录
            else:
                file_path.unlink()
            
            return f"✅ 删除成功: {file_name}"
            
        except Exception as e:
            return f"❌ 删除失败: {e}"
