"""
DDD架构结构管理器
负责管理整个应用的持久化树状结构
"""

import json
import os
from typing import Dict, List, Optional, Union, Any
from .base import PageBase, PluginBase
from ..utils.config import get_config_manager


class StructureManager:
    """结构管理器 - 基于持久化树结构的页面和插件管理"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        # 核心数据
        self.pages: Dict[str, PageBase] = {}      # 页面实例注册表
        self.plugins: Dict[str, PluginBase] = {}  # 插件实例注册表
        self.tree: Dict[str, Any] = {}            # 持久化的树状结构
        
        # 配置管理器
        self.config_manager = get_config_manager()
        self.config_dir = self.config_manager.get_config_dir()
        self.tree_file = self.config_manager.get_structure_file()
        
        self._initialized = True
        
        # 加载或初始化结构树
        self._load_or_initialize_tree()
        
        # 确保系统插件总是可用
        self._register_system_plugins()
    
    def _recreate_instances_from_tree(self) -> None:
        """从加载的树结构中重新创建页面和插件实例"""
        print("🔄 重新创建实例...")
        
        # 遍历树结构，找到所有插件和页面节点
        self._recreate_instances_recursive("home")
    
    def _recreate_instances_recursive(self, node_id: str) -> None:
        """递归重新创建实例"""
        if node_id not in self.tree:
            return
            
        node = self.tree[node_id]
        children = node.get("children", [])
        
        for child in children:
            child_type = child.get("type")
            child_name = child.get("name")
            
            if child_type == "plugin" and child_name:
                # 重新创建插件实例
                if child_name not in self.plugins:
                    plugin = self._import_plugin(child_name)
                    if plugin:
                        self.plugins[plugin.name] = plugin
                        print(f"✅ 重新创建插件: {plugin.name}")
                        
            elif child_type == "page" and child_name:
                # 重新创建页面实例（如果需要）
                if child_name not in self.pages:
                    page = self._import_page(child_name)
                    if page:
                        self.pages[page.short_name] = page
                        print(f"✅ 重新创建页面: {page.short_name}")
                
                # 递归处理子节点
                child_id = f"{node_id}_{child_name}"
                self._recreate_instances_recursive(child_id)
        
    def _load_or_initialize_tree(self) -> None:
        """加载或初始化结构树"""
        try:
            if os.path.exists(self.tree_file):
                with open(self.tree_file, 'r', encoding='utf-8') as f:
                    self.tree = json.load(f)
                print(f"📂 已加载结构树: {self.tree_file}")
                # 从已加载的树中重新创建插件实例
                self._recreate_instances_from_tree()
            else:
                print("🌱 首次运行，开始构建结构树...")
                self._build_initial_tree()
                self._save_tree()
        except Exception as e:
            print(f"⚠️ 加载结构树失败: {e}, 重新构建...")
            self._build_initial_tree()
            self._save_tree()
    
    def _build_initial_tree(self) -> None:
        """构建初始结构树 - 从home开始扫描"""
        print("🔍 正在扫描页面结构...")
        
        # 初始化树结构
        self.tree = {}
        
        # 从home页面开始扫描
        from ..pages.home import HomePage
        home_page = HomePage()
        
        # 注册home页面实例
        self.pages[home_page.short_name] = home_page
        
        # 构建home节点
        self.tree["home"] = {
            "type": "page",
            "name": home_page.short_name,
            "display_name": home_page.display_name,
            "description": home_page.description,
            "icon": home_page.icon,
            "children": [],
            "enabled": True,
            "order": 0
        }
        
        # 扫描home页面的子项
        self._scan_page_children("home", home_page)
        
        print("✅ 结构树构建完成")
    
    def _register_system_plugins(self) -> None:
        """注册系统插件 - 这些插件总是可用，不在树中显示"""
        system_plugins = ["set"]
        
        for plugin_name in system_plugins:
            plugin = self._import_plugin(plugin_name)
            if plugin:
                self.plugins[plugin.name] = plugin
    
    def _scan_page_children(self, node_id: str, page_instance: PageBase) -> None:
        """扫描页面的子项并添加到树中"""
        # 获取页面定义的子项（这是页面自己声明的默认子项）
        children_info = getattr(page_instance, 'get_default_children', lambda: [])()
        
        for child_info in children_info:
            child_id = f"{node_id}_{child_info['name']}"
            
            if child_info['type'] == 'page':
                # 尝试导入和实例化子页面
                try:
                    child_page = self._import_page(child_info['name'])
                    if child_page:
                        self.pages[child_page.short_name] = child_page
                        
                        # 添加子页面节点
                        child_node = {
                            "type": "page",
                            "name": child_page.short_name,
                            "display_name": child_page.display_name,
                            "description": child_page.description,
                            "icon": child_page.icon,
                            "children": [],
                            "enabled": True,
                            "order": len(self.tree[node_id]["children"])
                        }
                        
                        self.tree[node_id]["children"].append(child_node)
                        
                        # 递归扫描子页面的子项
                        self._scan_page_children(child_id, child_page)
                        
                except Exception as e:
                    print(f"⚠️ 跳过页面 {child_info['name']}: {e}")
                    
            elif child_info['type'] == 'plugin':
                # 尝试导入和实例化插件
                try:
                    plugin = self._import_plugin(child_info['name'])
                    if plugin:
                        self.plugins[plugin.name] = plugin
                        
                        # 添加插件节点
                        child_node = {
                            "type": "plugin",
                            "name": plugin.name,
                            "summary": plugin.summary,
                            "category": plugin.category,
                            "enabled": True,
                            "order": len(self.tree[node_id]["children"])
                        }
                        
                        self.tree[node_id]["children"].append(child_node)
                        
                except Exception as e:
                    print(f"⚠️ 跳过插件 {child_info['name']}: {e}")
    
    def _import_page(self, page_name: str) -> Optional[PageBase]:
        """动态导入页面类"""
        # 这里可以根据命名约定动态导入页面
        # 暂时返回None，实际实现时需要根据项目结构调整
        return None
    
    def _import_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """动态导入插件类"""
        # 根据插件名称动态导入
        try:
            if plugin_name == "path":
                from ..plugins.path_plugin import PathPlugin
                return PathPlugin()
            # set插件作为系统插件，总是可用，但不在树中显示
            elif plugin_name == "set":
                from ..plugins.set_plugin import SetPlugin
                return SetPlugin()
        except ImportError as e:
            print(f"⚠️ 导入插件 {plugin_name} 失败: {e}")
        return None
    
    def _save_tree(self) -> None:
        """保存结构树到文件"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.tree_file, 'w', encoding='utf-8') as f:
                json.dump(self.tree, f, ensure_ascii=False, indent=2)
            print(f"💾 结构树已保存: {self.tree_file}")
        except Exception as e:
            print(f"❌ 保存结构树失败: {e}")
    
    # ===== 页面和插件管理接口 =====
    
    def register_page_instance(self, page: PageBase) -> None:
        """注册页面实例（仅用于运行时）"""
        self.pages[page.short_name] = page
        
    def register_plugin_instance(self, plugin: PluginBase) -> None:
        """注册插件实例（仅用于运行时）"""
        self.plugins[plugin.name] = plugin
        
    def get_page(self, page_name: str) -> Optional[PageBase]:
        """根据名称获取页面实例"""
        return self.pages.get(page_name)
        
    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """根据名称获取插件实例"""
        return self.plugins.get(plugin_name)
    
    # ===== 结构查询接口 =====
    
    def get_node_children(self, node_id: str) -> List[Dict]:
        """获取节点的子项列表"""
        if node_id in self.tree:
            children = self.tree[node_id].get("children", [])
            # 按order排序
            return sorted(children, key=lambda x: x.get("order", 0))
        return []
    
    def get_enabled_children(self, node_id: str) -> List[Dict]:
        """获取节点的启用子项列表"""
        children = self.get_node_children(node_id)
        return [child for child in children if child.get("enabled", True)]
    
    def get_node_info(self, node_id: str) -> Optional[Dict]:
        """获取节点信息"""
        return self.tree.get(node_id)
    
    # ===== 结构修改接口 =====
    
    def set_child_enabled(self, node_id: str, child_name: str, enabled: bool) -> bool:
        """启用/禁用子项"""
        if node_id not in self.tree:
            return False
            
        children = self.tree[node_id].get("children", [])
        for child in children:
            if child.get("name") == child_name:
                child["enabled"] = enabled
                self._save_tree()
                return True
        return False
    
    def reorder_children(self, node_id: str, ordered_names: List[str]) -> bool:
        """重新排序子项"""
        if node_id not in self.tree:
            return False
            
        children = self.tree[node_id].get("children", [])
        name_to_child = {child.get("name"): child for child in children}
        
        # 重新排序
        reordered_children = []
        for i, name in enumerate(ordered_names):
            if name in name_to_child:
                child = name_to_child[name]
                child["order"] = i
                reordered_children.append(child)
        
        # 添加未在排序列表中的子项
        for child in children:
            if child.get("name") not in ordered_names:
                child["order"] = len(reordered_children)
                reordered_children.append(child)
        
        self.tree[node_id]["children"] = reordered_children
        self._save_tree()
        return True
    
    def add_child(self, node_id: str, child_info: Dict) -> bool:
        """添加子项"""
        if node_id not in self.tree:
            return False
            
        child_info["order"] = len(self.tree[node_id].get("children", []))
        child_info["enabled"] = child_info.get("enabled", True)
        
        self.tree[node_id].setdefault("children", []).append(child_info)
        self._save_tree()
        return True
    
    def remove_child(self, node_id: str, child_name: str) -> bool:
        """移除子项"""
        if node_id not in self.tree:
            return False
            
        children = self.tree[node_id].get("children", [])
        self.tree[node_id]["children"] = [
            child for child in children 
            if child.get("name") != child_name
        ]
        self._save_tree()
        return True
    
    def rescan_node(self, node_id: str) -> bool:
        """重新扫描节点的子项"""
        if node_id not in self.tree:
            return False
            
        node_info = self.tree[node_id]
        if node_info.get("type") != "page":
            return False
            
        # 获取页面实例
        page_name = node_info.get("name")
        page_instance = self.get_page(page_name)
        if not page_instance:
            return False
        
        # 清空现有子项
        self.tree[node_id]["children"] = []
        
        # 重新扫描
        self._scan_page_children(node_id, page_instance)
        self._save_tree()
        return True
    
    # ===== 调试和工具方法 =====
    
    def print_tree(self, node_id: str = "home", indent: int = 0) -> None:
        """打印树结构（调试用）"""
        if node_id not in self.tree:
            return
            
        node = self.tree[node_id]
        prefix = "  " * indent
        type_icon = "📄" if node.get('type') == 'page' else "🔌"
        enabled_icon = "✅" if node.get('enabled', True) else "❌"
        
        display_name = node.get('display_name', node.get('summary', node.get('name', 'Unknown')))
        print(f"{prefix}{type_icon} {enabled_icon} {display_name}")
        
        # 递归打印子项
        children = self.get_node_children(node_id)
        for child in children:
            child_id = f"{node_id}_{child.get('name')}"
            if child_id in self.tree:
                self.print_tree(child_id, indent + 1)
    
    def get_completions(self, partial: str) -> List[str]:
        """获取自动补全建议"""
        completions = []
        
        # 页面名称补全
        for page_name in self.pages.keys():
            if page_name.startswith(partial):
                completions.append(page_name)
                
        # 插件名称补全
        for plugin_name in self.plugins.keys():
            if plugin_name.startswith(partial):
                completions.append(plugin_name)
                
        return sorted(completions)
