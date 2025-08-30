"""
路径管理插件 - 管理常用路径的短名映射
支持添加、删除、列表、跳转常用路径
"""

import json
import os
from typing import Dict, List, Optional, Any
from ..core.base import PluginBase
from ..utils.config import get_config_manager


class PathPlugin(PluginBase):
    """路径管理插件"""
    
    def __init__(self):
        super().__init__(
            name="path",
            summary="管理常用路径的短名映射",
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
                print(f"📂 已加载路径配置: {self.config_file}")
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
            print(f"💾 路径配置已保存: {self.config_file}")
        except Exception as e:
            print(f"❌ 保存路径配置失败: {e}")
    
    def run(self, operation: str = "interactive", **kwargs) -> Any:
        """执行路径操作"""
        if operation == "interactive":
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
            print("  [0] 返回")
            
            choice = input("\n请选择操作 (0-4): ").strip()
            
            if choice == "0":
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
            short_name = input("路径短名 (如: proj, home, docs): ").strip()
            if not short_name:
                print("❌ 短名不能为空")
                continue
            if short_name in self.paths:
                print(f"❌ 短名 '{short_name}' 已存在")
                continue
            break
        
        # 获取路径
        while True:
            path = input("路径 (可以是相对或绝对路径): ").strip()
            if not path:
                print("❌ 路径不能为空")
                continue
            
            # 展开路径
            expanded_path = os.path.expanduser(path)
            if not os.path.exists(expanded_path):
                confirm = input(f"⚠️ 路径 '{expanded_path}' 不存在，是否仍要添加? (y/N): ").strip().lower()
                if confirm != 'y':
                    continue
            break
        
        # 获取描述（可选）
        description = input("描述 (可选): ").strip()
        
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
        
        choice = input(f"\n请选择要删除的路径 (1-{len(self.paths)}) 或输入短名: ").strip()
        
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
        confirm = input(f"确认删除 '{short_name}' -> '{path_info['path']}'? (y/N): ").strip().lower()
        if confirm == 'y':
            del self.paths[short_name]
            self._save_paths()
            print(f"✅ 已删除路径: {short_name}")
        else:
            print("⚠️ 已取消删除")
    
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
        
        choice = input(f"\n请选择要编辑的路径 (1-{len(self.paths)}) 或输入短名: ").strip()
        
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
        new_path = input(f"新路径 (回车保持不变): ").strip()
        if new_path:
            expanded_path = os.path.expanduser(new_path)
            if not os.path.exists(expanded_path):
                confirm = input(f"⚠️ 路径 '{expanded_path}' 不存在，是否仍要使用? (y/N): ").strip().lower()
                if confirm == 'y':
                    path_info['path'] = expanded_path
            else:
                path_info['path'] = expanded_path
        
        # 编辑描述
        new_description = input(f"新描述 (回车保持不变): ").strip()
        if new_description:
            path_info['description'] = new_description
        
        path_info['updated_at'] = self._get_timestamp()
        self._save_paths()
        print(f"✅ 已更新路径: {short_name}")
    
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
