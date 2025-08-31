"""
路径管理插件 - 管理常用路径的短名映射
支持添加、删除、列表、跳转常用路径
"""

import json
import os
from typing import Dict, List, Optional, Any
from ..core.base import PluginBase
from ..utils.config import get_config_manager


class CdPlugin(PluginBase):
    """路径管理插件"""
    
    def __init__(self):
        super().__init__(
            name="cd",
            summary="快速跳转常用路径",
            category="system"
        )
        
        # 配置管理器
        self.config_manager = get_config_manager()
        self.config_dir = self.config_manager.get_config_dir()
        self.config_file = self.config_manager.get_paths_file()
        
        # 加载路径配置
        self._load_paths()
    
    def _load_paths(self) -> None:
        """加载路径配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.paths = json.load(f)
                # print(f"📂 已加载路径配置: {self.config_file}")  # 静默加载
            else:
                self.paths = {}
                print("🌱 初始化路径配置...")
                self._save_paths()
        except Exception as e:
            print(f"⚠️ 加载路径配置失败: {e}, 重置配置...")
            self.paths = {}
            self._save_paths()
    
    def _save_paths(self) -> None:
        """保存路径配置"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.paths, f, ensure_ascii=False, indent=2)
            # print(f"💾 路径配置已保存: {self.config_file}")  # 静默保存
        except Exception as e:
            print(f"❌ 保存路径配置失败: {e}")
    
    def run(self, operation: str = "interactive", args: List[str] = None, **kwargs) -> Any:
        """执行路径操作"""
        if operation == "cli":
            return self._handle_cli(args or [])
        elif operation == "interactive":
            return self._interactive_mode()
        elif operation == "add":
            return self._add_path(kwargs.get('short_name'), kwargs.get('path'))
        elif operation == "remove":
            return self._remove_path(kwargs.get('short_name'))
        elif operation == "list":
            return self._list_paths()
        elif operation == "get":
            return self._get_path(kwargs.get('short_name'))
        elif operation == "get_completions":
            return self._get_completions(kwargs.get('partial', ''))
        else:
            print(f"❌ 未知操作: {operation}")
            return False
    
    def _handle_cli(self, args: List[str]) -> bool:
        """处理CLI调用"""
        if not args:
            # 无参数时显示帮助和所有路径
            print("\n📁 路径管理器")
            print("=" * 30)
            print(self.get_help())
            print("\n当前保存的路径:")
            if not self.paths:
                print("  (暂无路径)")
            else:
                for short_name, path_info in self.paths.items():
                    print(f"  📍 {short_name} -> {path_info['path']}")
                    if path_info.get('description'):
                        print(f"      {path_info['description']}")
            return True
        
        # 处理子命令
        subcommand = args[0]
        sub_args = args[1:]
        
        if subcommand == "add":
            if len(sub_args) >= 2:
                return self._add_path(sub_args[0], sub_args[1])
            else:
                print("❌ 用法: ddd cd add <短名> <路径>")
                return False
        elif subcommand == "remove" or subcommand == "rm":
            if sub_args:
                return self._remove_path(sub_args[0])
            else:
                print("❌ 用法: ddd cd remove <短名>")
                return False
        elif subcommand == "list" or subcommand == "ls":
            paths = self._list_paths()
            if not paths:
                print("暂无保存的路径")
            else:
                print("已保存的路径:")
                for short_name, path_info in paths.items():
                    print(f"  📍 {short_name} -> {path_info['path']}")
            return True
        elif subcommand == "test":
            self._cli_test_paths()
            return True
        else:
            # 尝试跳转到指定短名
            path = self._get_path(subcommand)
            if path:
                print(f"cd '{path}'")
                # 这里可以集成shell脚本来实际改变目录
                return True
            else:
                print(f"❌ 未找到路径: {subcommand}")
                print("可用的路径:")
                for short_name in self.paths.keys():
                    print(f"  {short_name}")
                return False
    
    def _cli_test_paths(self) -> None:
        """CLI模式下测试路径"""
        if not self.paths:
            print("暂无路径可测试")
            return
        
        print("测试路径状态:")
        for short_name, path_info in self.paths.items():
            path = path_info['path']
            exists = os.path.exists(path)
            status = "✅" if exists else "❌"
            print(f"  {status} {short_name} -> {path}")
    
    def _interactive_mode(self) -> bool:
        """交互式路径管理"""
        print("\n" + "="*50)
        print("📁 路径管理器")
        print("="*50)
        
        while True:
            print(f"\n当前已保存 {len(self.paths)} 个路径:")
            if not self.paths:
                print("  (暂无路径)")
            else:
                for short_name, path_info in self.paths.items():
                    print(f"  📍 {short_name} -> {path_info['path']}")
                    if path_info.get('description'):
                        print(f"      {path_info['description']}")
            
            print("\n操作选项:")
            print("  [1] 添加路径")
            print("  [2] 删除路径")
            print("  [3] 编辑路径") 
            print("  [4] 测试路径")
            print("  [-] 返回")
            
            from ..utils.input_utils import get_single_key_input
            choice = get_single_key_input("\n请选择操作 (1-4, - 返回): ")
            
            if choice == "-":
                break
            elif choice == "1":
                self._interactive_add()
            elif choice == "2":
                self._interactive_remove()
            elif choice == "3":
                self._interactive_edit()
            elif choice == "4":
                self._interactive_test()
            else:
                print("❌ 无效选择，请重试")
        
        return True
    
    def _interactive_add(self) -> None:
        """交互式添加路径"""
        print("\n➕ 添加新路径")
        print("-" * 30)
        
        # 获取短名
        while True:
            try:
                short_name = input("路径短名 (如: proj, home, docs) [q=退出, -=取消]: ").strip()
                if short_name.lower() == 'q':
                    print("👋 退出添加操作")
                    return
                if short_name == '-':
                    print("📝 取消添加操作")
                    return
                if not short_name:
                    print("❌ 短名不能为空")
                    continue
                if short_name in self.paths:
                    print(f"❌ 短名 '{short_name}' 已存在")
                    continue
                break
            except KeyboardInterrupt:
                print("\n👋 取消操作")
                return
        
        # 获取路径
        while True:
            try:
                path = input("路径 (可以是相对或绝对路径) [q=退出, -=取消]: ").strip()
                if path.lower() == 'q':
                    print("👋 退出添加操作")
                    return
                if path == '-':
                    print("📝 取消添加操作")
                    return
                if not path:
                    print("❌ 路径不能为空")
                    continue
                
                # 展开路径
                expanded_path = os.path.expanduser(path)
                if not os.path.exists(expanded_path):
                    from ..utils.input_utils import get_single_key_input
                    confirm = get_single_key_input(f"⚠️ 路径 '{expanded_path}' 不存在，是否仍要添加? (y/N): ")
                    if confirm != 'y':
                        continue
                break
            except KeyboardInterrupt:
                print("\n👋 取消操作")
                return
        
        # 获取描述（可选）
        try:
            description = input("描述 (可选) [直接回车跳过]: ").strip()
        except KeyboardInterrupt:
            print("\n👋 取消操作")
            return
        
        # 添加路径
        self.paths[short_name] = {
            "path": expanded_path,
            "description": description,
            "created_at": self._get_timestamp()
        }
        
        self._save_paths()
        print(f"✅ 已添加路径: {short_name} -> {expanded_path}")
    
    def _interactive_remove(self) -> None:
        """交互式删除路径"""
        if not self.paths:
            print("❌ 暂无路径可删除")
            return
        
        print("\n➖ 删除路径")
        print("-" * 30)
        
        # 显示现有路径
        for i, (short_name, path_info) in enumerate(self.paths.items(), 1):
            print(f"  [{i}] {short_name} -> {path_info['path']}")
        
        try:
            choice = input(f"\n请选择要删除的路径 (1-{len(self.paths)}) 或输入短名 [q=退出, -=取消]: ").strip()
            
            if choice.lower() == 'q':
                print("👋 退出删除操作")
                return
            if choice == '-':
                print("📝 取消删除操作")
                return
            
            # 尝试按数字选择
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(self.paths):
                    short_name = list(self.paths.keys())[index]
                else:
                    print("❌ 无效选择")
                    return
            # 尝试按短名选择
            elif choice in self.paths:
                short_name = choice
            else:
                print("❌ 未找到指定的路径")
                return
            
            # 确认删除
            path_info = self.paths[short_name]
            from ..utils.input_utils import get_single_key_input
            confirm = get_single_key_input(f"确认删除 '{short_name}' -> '{path_info['path']}'? (y/N): ")
            if confirm == 'y':
                del self.paths[short_name]
                self._save_paths()
                print(f"✅ 已删除路径: {short_name}")
            else:
                print("⚠️ 已取消删除")
        except KeyboardInterrupt:
            print("\n👋 取消操作")
            return
    
    def _interactive_edit(self) -> None:
        """交互式编辑路径"""
        if not self.paths:
            print("❌ 暂无路径可编辑")
            return
        
        print("\n✏️ 编辑路径")
        print("-" * 30)
        
        # 显示现有路径
        for i, (short_name, path_info) in enumerate(self.paths.items(), 1):
            print(f"  [{i}] {short_name} -> {path_info['path']}")
        
        try:
            choice = input(f"\n请选择要编辑的路径 (1-{len(self.paths)}) 或输入短名 [q=退出, -=取消]: ").strip()
            
            if choice.lower() == 'q':
                print("👋 退出编辑操作")
                return
            if choice == '-':
                print("📝 取消编辑操作")
                return
            
            # 选择路径
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(self.paths):
                    short_name = list(self.paths.keys())[index]
                else:
                    print("❌ 无效选择")
                    return
            elif choice in self.paths:
                short_name = choice
            else:
                print("❌ 未找到指定的路径")
                return
            
            # 编辑选择的路径
            path_info = self.paths[short_name]
            print(f"\n编辑路径: {short_name}")
            print(f"当前路径: {path_info['path']}")
            print(f"当前描述: {path_info.get('description', '(无)')}")
            
            # 编辑路径
            try:
                new_path = input(f"新路径 (回车保持不变) [q=退出]: ").strip()
                if new_path.lower() == 'q':
                    print("👋 退出编辑操作")
                    return
                if new_path:
                    expanded_path = os.path.expanduser(new_path)
                    if not os.path.exists(expanded_path):
                        from ..utils.input_utils import get_single_key_input
                        confirm = get_single_key_input(f"⚠️ 路径 '{expanded_path}' 不存在，是否仍要使用? (y/N): ")
                        if confirm == 'y':
                            path_info['path'] = expanded_path
                    else:
                        path_info['path'] = expanded_path
                
                # 编辑描述
                new_description = input(f"新描述 (回车保持不变) [q=退出]: ").strip()
                if new_description.lower() == 'q':
                    print("👋 退出编辑操作")
                    return
                if new_description:
                    path_info['description'] = new_description
                
                path_info['updated_at'] = self._get_timestamp()
                self._save_paths()
                print(f"✅ 已更新路径: {short_name}")
            except KeyboardInterrupt:
                print("\n👋 取消操作")
                return
        except KeyboardInterrupt:
            print("\n👋 取消操作")
            return
    
    def _interactive_test(self) -> None:
        """交互式测试路径"""
        if not self.paths:
            print("❌ 暂无路径可测试")
            return
        
        print("\n🧪 测试路径")
        print("-" * 30)
        
        for short_name, path_info in self.paths.items():
            path = path_info['path']
            exists = os.path.exists(path)
            status = "✅" if exists else "❌"
            print(f"  {status} {short_name} -> {path}")
            if not exists:
                print(f"      ⚠️ 路径不存在")
    
    def _add_path(self, short_name: str, path: str) -> bool:
        """添加路径"""
        if not short_name or not path:
            return False
        
        if short_name in self.paths:
            print(f"❌ 短名 '{short_name}' 已存在")
            return False
        
        expanded_path = os.path.expanduser(path)
        self.paths[short_name] = {
            "path": expanded_path,
            "description": "",
            "created_at": self._get_timestamp()
        }
        
        self._save_paths()
        print(f"✅ 已添加路径: {short_name} -> {expanded_path}")
        return True
    
    def _remove_path(self, short_name: str) -> bool:
        """删除路径"""
        if not short_name:
            return False
        
        if short_name not in self.paths:
            print(f"❌ 未找到路径: {short_name}")
            return False
        
        del self.paths[short_name]
        self._save_paths()
        print(f"✅ 已删除路径: {short_name}")
        return True
    
    def _list_paths(self) -> Dict[str, Dict]:
        """列出所有路径"""
        return self.paths
    
    def _get_path(self, short_name: str) -> Optional[str]:
        """获取指定短名的路径"""
        if short_name in self.paths:
            return self.paths[short_name]['path']
        return None
    
    def _get_completions(self, partial: str) -> List[str]:
        """获取路径短名的补全建议"""
        return [name for name in self.paths.keys() if name.startswith(partial)]
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def get_help(self) -> str:
        """获取帮助信息"""
        return """路径管理器 - 管理常用路径的短名映射

功能:
  - 添加常用路径的短名
  - 删除不需要的路径
  - 列出所有已保存的路径
  - 支持 ddd cd <短名> 快速跳转

使用示例:
  ddd path          # 进入交互式管理
  ddd cd proj       # 跳转到项目目录
  ddd cd home       # 跳转到用户主目录
"""
