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
        self.tree: Dict[int, Any] = {}            # 持久化的树状结构，key为数字ID
        self.next_id: int = 1                     # 下一个可用的节点ID
        # 根节点ID固定为0
        
        # 配置管理器
        self.config_manager = get_config_manager()
        self.config_dir = self.config_manager.get_config_dir()
        self.tree_file = self.config_manager.get_structure_file()
        
        self._initialized = True
        
        # 加载或初始化结构树
        self._load_or_initialize_structure()
        
        # 确保系统插件总是可用
        self._register_system_plugins()
    
    def _load_or_initialize_structure(self) -> None:
        """加载或初始化结构文件"""
        try:
            if os.path.exists(self.tree_file):
                with open(self.tree_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._load_tree(data)
                
                # print(f"📂 已加载结构树: {self.tree_file}, 根节点ID: 0")  # 静默加载
            else:
                print("🌱 首次运行，开始构建结构树...")
                self._build_initial_structure()
                self._save_structure()
        except Exception as e:
            print(f"⚠️ 加载结构树失败: {e}, 重新构建...")
            self._build_initial_structure()
            self._save_structure()

    def _load_tree(self, data: dict) -> None:
        """加载新格式数据"""
        self.tree = {}
        max_id = 0
        
        for key, node_data in data.items():
            try:
                node_id = int(key)
                self.tree[node_id] = node_data
                node_data['id'] = node_id  # 确保包含id字段
                max_id = max(max_id, node_id)
            except ValueError:
                print(f"⚠️ 跳过无效节点ID: {key}")
        
        self.next_id = max_id + 1
        
        # 检查根节点
        if 0 not in self.tree:
            print("⚠️ 缺少根节点，重新构建")
            self._build_initial_structure()
    
    def _build_initial_structure(self) -> None:
        """构建初始结构树 - 从根节点开始扫描"""
        print("🔍 正在扫描页面结构，创建根节点...")
        
        # 初始化树结构
        self.tree = {}
        self.next_id = 1  # 从1开始，0是根节点
        
        # 尝试获取根页面实例以构建初始结构
        root_page = self._get_or_create_instance("home", "page")
        if not root_page:
            print("❌ 无法创建home页面实例")
            return
        
        # 构建根节点(ID=0)
        self.tree[0] = {
            "id": 0,
            "type": "page",
            "name": root_page.name,
            "display_name": root_page.display_name,
            "description": root_page.description,
            "icon": root_page.icon,
            "children": [],  # 新格式：ID列表
            "enabled": True,
            "order": 0
        }
        
        # 扫描根页面的子项
        self._scan_page_children(0, root_page)
        
        print("✅ 结构树构建完成")
    
    def _register_system_plugins(self) -> None:
        """注册系统插件 - 这些插件总是可用，不在树中显示"""
        system_plugins = ["setting"]  # 使用统一命名
        
        for plugin_name in system_plugins:
            plugin = self._get_or_create_instance(plugin_name, "plugin")
            if plugin:
                self.plugins[plugin.name] = plugin
    
    def _get_or_create_instance(self, name: str, node_type: str) -> Optional[Union[PageBase, PluginBase]]:
        """懒加载：获取或创建实例（页面或插件）"""
        if node_type == "page":
            # 检查是否已存在实例
            if name in self.pages:
                return self.pages[name]
            # 创建新实例
            instance = self._create_page_instance(name)
            if instance:
                self.pages[name] = instance
            return instance
        elif node_type == "plugin":
            # 检查是否已存在实例
            if name in self.plugins:
                return self.plugins[name]
            # 创建新实例
            instance = self._create_plugin_instance(name)
            if instance:
                self.plugins[name] = instance
            return instance
        return None
    
    def _scan_page_children(self, node_id: int, page_instance: PageBase) -> None:
        """扫描页面的子项并添加到树中"""
        # 获取页面定义的子项（这是页面自己声明的默认子项）
        children_info = getattr(page_instance, 'get_default_children', lambda: [])()
        
        for child_info in children_info:
            child_name = child_info['name']
            child_type = child_info['type']
            
            if child_type == 'page':
                # 创建页面实例以获取其信息
                try:
                    child_page = self._get_or_create_instance(child_name, "page")
                    if child_page:
                        # 分配新的节点ID
                        child_node_id = self.next_id
                        self.next_id += 1
                        
                        # 创建子页面的树节点
                        self.tree[child_node_id] = {
                            "id": child_node_id,
                            "type": "page",
                            "name": child_page.name,
                            "display_name": child_page.display_name,
                            "description": child_page.description,
                            "icon": child_page.icon,
                            "children": [],  # 新格式：ID列表
                            "enabled": True,
                            "order": len(self.tree[node_id]["children"])
                        }
                        
                        # 将子节点ID添加到父节点的children列表
                        self.tree[node_id]["children"].append(child_node_id)
                        
                        # 递归扫描子页面的子项
                        self._scan_page_children(child_node_id, child_page)
                        
                except Exception as e:
                    print(f"⚠️ 跳过页面 {child_name}: {e}")
                    
            elif child_type == 'plugin':
                # 创建插件实例以获取其信息
                try:
                    plugin = self._get_or_create_instance(child_name, "plugin")
                    if plugin:
                        # 分配新的节点ID
                        child_node_id = self.next_id
                        self.next_id += 1
                        
                        # 创建插件的树节点
                        self.tree[child_node_id] = {
                            "id": child_node_id,
                            "type": "plugin",
                            "name": plugin.name,
                            "summary": plugin.summary,
                            "category": plugin.category,
                            "children": [],  # 新格式：ID列表
                            "enabled": True,
                            "order": len(self.tree[node_id]["children"])
                        }
                        
                        # 将子节点ID添加到父节点的children列表
                        self.tree[node_id]["children"].append(child_node_id)
                        
                except Exception as e:
                    print(f"⚠️ 跳过插件 {child_name}: {e}")
    
    def _create_page_instance(self, page_name: str) -> Optional[PageBase]:
        """根据统一命名规则创建页面实例"""
        import importlib
        
        # 统一命名规则: page_name -> PageNamePage类 在 ddd.pages.page_name 模块中
        try:
            # 将下划线命名转换为驼峰命名，添加Page后缀
            class_name = ''.join(word.capitalize() for word in page_name.split('_')) + 'Page'
            module_path = f"ddd.pages.{page_name}"
            
            # 导入模块
            module = importlib.import_module(module_path)
            page_class = getattr(module, class_name)
            instance = page_class()
            # print(f"✅ 成功创建页面实例: {page_name} -> {class_name}")  # 静默创建
            return instance
            
        except (ImportError, AttributeError) as e:
            print(f"❌ 无法创建页面实例 {page_name}: 模块={module_path}, 类={class_name}, 错误={e}")
            return None
    
    def _create_plugin_instance(self, plugin_name: str) -> Optional[PluginBase]:
        """根据统一命名规则创建插件实例"""
        import importlib
        
        # 统一命名规则: plugin_name -> PluginNamePlugin类 在 ddd.plugins.plugin_name 模块中
        try:
            # 将下划线命名转换为驼峰命名，添加Plugin后缀
            class_name = ''.join(word.capitalize() for word in plugin_name.split('_')) + 'Plugin'
            module_path = f"ddd.plugins.{plugin_name}"
            
            # 导入模块
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, class_name)
            instance = plugin_class()
            # print(f"✅ 成功创建插件实例: {plugin_name} -> {class_name}")  # 静默创建
            return instance
            
        except (ImportError, AttributeError) as e:
            print(f"❌ 无法创建插件实例 {plugin_name}: 模块={module_path}, 类={class_name}, 错误={e}")
            return None
    
    def _save_structure(self) -> None:
        """保存结构数据到文件"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            # 新格式：直接保存tree，key为字符串格式的数字ID
            structure_data = {}
            for node_id, node_data in self.tree.items():
                structure_data[str(node_id)] = node_data
            
            with open(self.tree_file, 'w', encoding='utf-8') as f:
                json.dump(structure_data, f, ensure_ascii=False, indent=2)
            print(f"💾 结构数据已保存: {self.tree_file}")
        except Exception as e:
            print(f"❌ 保存结构数据失败: {e}")
    
    def _save_tree(self) -> None:
        """保存结构树到文件（向后兼容）"""
        self._save_structure()
    
    # ===== 页面和插件管理接口 =====
    
    def register_page_instance(self, page: PageBase) -> None:
        """注册页面实例（仅用于运行时）"""
        self.pages[page.name] = page
        
    def register_plugin_instance(self, plugin: PluginBase) -> None:
        """注册插件实例（仅用于运行时）"""
        self.plugins[plugin.name] = plugin
        
    def get_page(self, page_name: str) -> Optional[PageBase]:
        """根据名称获取页面实例（懒加载）"""
        return self._get_or_create_instance(page_name, "page")
        
    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """根据名称获取插件实例（懒加载）"""
        return self._get_or_create_instance(plugin_name, "plugin")
    
    # ===== 结构查询接口 =====
    
    def get_node(self, node_id: Union[int, str]) -> Optional[Dict]:
        """获取节点信息"""
        # 兼容字符串ID（用于旧接口）
        if isinstance(node_id, str):
            try:
                node_id = int(node_id)
            except ValueError:
                # 字符串ID，尝试根节点
                if node_id == "home" or node_id == "0":
                    node_id = 0
                else:
                    return None
        
        if node_id in self.tree:
            node = self.tree[node_id].copy()
            return node
        return None
    
    def get_child_nodes(self, node_id: Union[int, str]) -> List[Dict]:
        """获取节点的子项列表，每个子项都包含完整信息"""
        # 兼容字符串ID
        if isinstance(node_id, str):
            try:
                node_id = int(node_id)
            except ValueError:
                if node_id == "home" or node_id == "0":
                    node_id = 0
                else:
                    return []
        
        if node_id not in self.tree:
            return []
            
        try:
            child_ids = self.tree[node_id].get("children", [])
            # 获取子节点的完整信息
            result = []
            for child_id in child_ids:
                if child_id in self.tree:
                    child_node = self.tree[child_id].copy()
                    result.append(child_node)
            # 按order排序
            return sorted(result, key=lambda x: x.get("order", 0))
        except Exception as e:
            print(f"⚠️ 获取子节点失败 ({node_id}): {e}")
            return []
    
    def get_node_children(self, node_id: Union[int, str]) -> List[Dict]:
        """获取节点的子项列表（保留原方法名以兼容）"""
        return self.get_child_nodes(node_id)
    
    def get_enabled_children(self, node_id: Union[int, str]) -> List[Dict]:
        """获取节点的启用子项列表"""
        children = self.get_node_children(node_id)
        return [child for child in children if child.get("enabled", True)]
    
    def get_node_info(self, node_id: Union[int, str]) -> Optional[Dict]:
        """获取节点信息"""
        return self.get_node(node_id)
        
    def find_node_by_path(self, path: List[str]) -> Optional[Dict]:
        """
        根据名称路径查找节点信息
        例如: ['cd', 'list'] 或 ['env_config']
        """
        current_node_id = 0  # 从根节点开始
        if not path:
            # 返回根节点
            return self.get_node(current_node_id)
            
        for i, name in enumerate(path):
            # 获取当前节点的子节点
            children = self.get_child_nodes(current_node_id)
            found_child = None
            
            # 查找匹配名称的子节点
            for child in children:
                if child.get("name") == name:
                    found_child = child
                    break
            
            if not found_child:
                return None  # 路径无效
            
            # 更新当前节点ID
            current_node_id = found_child.get("id")
            
            # 如果是路径的最后一部分，返回找到的节点
            if i == len(path) - 1:
                return found_child
            
            # 否则，继续向下查找（current_node_id已经在上面更新了）
            
        return None
        
    def get_node_by_id(self, node_id: Union[int, str]) -> Optional[Dict]:
        """根据节点ID获取节点信息"""
        return self.get_node(node_id)

    def get_completions_for_node(self, node_id: Union[int, str]) -> List[str]:
        """为指定节点获取可用的子项名称（用于自动补全）"""
        children = self.get_enabled_children(node_id)
        return [child['name'] for child in children]

    # ===== 结构修改接口 =====
    
    def set_child_enabled(self, node_id: Union[int, str], child_name: str, enabled: bool) -> bool:
        """启用/禁用子项"""
        node = self.get_node(node_id)
        if not node:
            return False
            
        # 查找对应名称的子节点
        children = self.get_child_nodes(node_id)
        for child in children:
            if child.get("name") == child_name:
                child_id = child.get("id")
                if child_id in self.tree:
                    self.tree[child_id]["enabled"] = enabled
                    self._save_structure()
                    return True
        return False
    
    def reorder_children(self, node_id: Union[int, str], ordered_names: List[str]) -> bool:
        """重新排序子项"""
        # 兼容处理
        if isinstance(node_id, str):
            try:
                node_id = int(node_id)
            except ValueError:
                if node_id == "home":
                    node_id = 0
                else:
                    return False
        
        if node_id not in self.tree:
            return False
            
        children = self.get_child_nodes(node_id)
        name_to_child = {child.get("name"): child for child in children}
        
        # 重新排序：只需要更新order字段，不改变children列表
        for i, name in enumerate(ordered_names):
            if name in name_to_child:
                child = name_to_child[name]
                child_id = child.get("id")
                if child_id in self.tree:
                    self.tree[child_id]["order"] = i
        
        # 为未在排序列表中的子项设置order
        for child in children:
            if child.get("name") not in ordered_names:
                child_id = child.get("id")
                if child_id in self.tree:
                    self.tree[child_id]["order"] = len(ordered_names)
        
        self._save_structure()
        return True
    
    def add_child(self, node_id: Union[int, str], child_info: Dict) -> bool:
        """添加子项"""
        # 兼容处理
        if isinstance(node_id, str):
            try:
                node_id = int(node_id)
            except ValueError:
                if node_id == "home":
                    node_id = 0
                else:
                    return False
        
        if node_id not in self.tree:
            return False
        
        # 分配新的子节点ID
        child_node_id = self.next_id
        self.next_id += 1
        
        # 创建完整的子节点
        child_node = {
            "id": child_node_id,
            "order": len(self.tree[node_id].get("children", [])),
            "enabled": child_info.get("enabled", True),
            **child_info
        }
        
        # 将子节点添加到树中
        self.tree[child_node_id] = child_node
        # 将子节点ID添加到父节点的children列表
        self.tree[node_id].setdefault("children", []).append(child_node_id)
        
        self._save_structure()
        return True
    
    def remove_child(self, node_id: Union[int, str], child_name: str) -> bool:
        """移除子项"""
        # 兼容处理
        if isinstance(node_id, str):
            try:
                node_id = int(node_id)
            except ValueError:
                if node_id == "home":
                    node_id = 0
                else:
                    return False
        
        if node_id not in self.tree:
            return False
        
        # 查找要删除的子节点
        children = self.get_child_nodes(node_id)
        child_to_remove = None
        for child in children:
            if child.get("name") == child_name:
                child_to_remove = child
                break
        
        if not child_to_remove:
            return False
        
        child_id_to_remove = child_to_remove.get("id")
        
        # 从父节点的children列表中移除
        current_children = self.tree[node_id].get("children", [])
        self.tree[node_id]["children"] = [
            cid for cid in current_children if cid != child_id_to_remove
        ]
        
        # 从树中删除节点（递归删除所有子节点）
        self._remove_node_recursive(child_id_to_remove)
        
        self._save_structure()
        return True
    
    def _remove_node_recursive(self, node_id: int) -> None:
        """递归删除节点及其所有子节点"""
        if node_id not in self.tree:
            return
        
        # 先删除所有子节点
        child_ids = self.tree[node_id].get("children", [])
        for child_id in child_ids:
            self._remove_node_recursive(child_id)
        
        # 删除节点本身
        del self.tree[node_id]
    
    def rescan_node(self, node_id: Union[int, str]) -> bool:
        """重新扫描节点的子项"""
        # 兼容处理
        if isinstance(node_id, str):
            try:
                node_id = int(node_id)
            except ValueError:
                if node_id == "home":
                    node_id = 0
                else:
                    return False
        
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
        
        # 删除现有的所有子节点
        child_ids = self.tree[node_id].get("children", [])
        for child_id in child_ids:
            self._remove_node_recursive(child_id)
        
        # 清空子项列表
        self.tree[node_id]["children"] = []
        
        # 重新扫描
        self._scan_page_children(node_id, page_instance)
        self._save_structure()
        return True
    
    # ===== 调试和工具方法 =====
    
    def print_tree(self, node_id: Union[int, str] = None, indent: int = 0) -> None:
        """打印树结构（调试用）"""
        if node_id is None:
            node_id = 0  # 默认根节点ID
        
        # 兼容处理
        if isinstance(node_id, str):
            try:
                node_id = int(node_id)
            except ValueError:
                if node_id == "home":
                    node_id = 0
                else:
                    return
            
        if node_id not in self.tree:
            return
            
        node = self.tree[node_id]
        prefix = "  " * indent
        type_icon = "📄" if node.get('type') == 'page' else "🔌"
        enabled_icon = "✅" if node.get('enabled', True) else "❌"
        
        display_name = node.get('display_name', node.get('summary', node.get('name', 'Unknown')))
        print(f"{prefix}{type_icon} {enabled_icon} {display_name} ({node_id})")
        
        # 递归打印子项
        children = self.get_node_children(node_id)
        for child in children:
            child_id = child.get('id')
            if child_id is not None:
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
                
        return sorted(list(set(completions)))  # 去重并排序
    
    def get_statistics(self) -> Dict[str, int]:
        """获取结构统计信息"""
        stats = {
            "pages": len(self.pages),
            "plugins": len(self.plugins),
            "tree_nodes": len(self.tree),
            "enabled_children": 0,
            "total_children": 0
        }
        
        # 统计所有子项
        for node_id in self.tree:
            children = self.tree[node_id].get("children", [])
            stats["total_children"] += len(children)
            stats["enabled_children"] += len([c for c in children if c.get("enabled", True)])
            
        return stats
