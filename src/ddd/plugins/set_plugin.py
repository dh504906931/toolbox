"""
Set插件 - 通用的结构管理插件
可以被任何Page调用来管理其子结构
"""

from typing import Any, Dict, List
from ..core.base import PluginBase
from ..core.structure import StructureManager


class SetPlugin(PluginBase):
    """结构管理插件 - 管理页面和插件的组织"""
    
    def __init__(self):
        super().__init__(
            name="set",
            summary="管理页面和插件的组织结构",
            category="system"
        )
        
    def run(self, **kwargs) -> Any:
        """
        执行结构管理功能
        
        参数:
        - node_id: 要管理的节点ID
        - operation: 操作类型 (list/disable/enable/reorder/interactive)
        - target: 目标项目名称
        - config: 配置参数
        """
        from ..core.renderer import Renderer
        renderer = Renderer()
        
        node_id = kwargs.get('node_id', 'home')
        operation = kwargs.get('operation', 'interactive')
        target = kwargs.get('target', '')
        config = kwargs.get('config', {})
        
        structure = StructureManager()
        
        try:
            if operation == 'list':
                return self._list_structure(renderer, structure, node_id)
            elif operation == 'disable':
                return self._disable_item(renderer, structure, node_id, target)
            elif operation == 'enable':
                return self._enable_item(renderer, structure, node_id, target)
            elif operation == 'reorder':
                return self._reorder_items(renderer, structure, node_id, config)
            elif operation == 'interactive':
                return self._interactive_mode(renderer, structure, node_id)
            else:
                renderer.print_error(f"未知操作: {operation}")
                return False
                
        except Exception as e:
            renderer.print_error(f"结构管理操作失败: {e}")
            return False
            
    def _list_structure(self, renderer, structure, node_id: str) -> bool:
        """列出结构信息"""
        node_info = structure.get_node_info(node_id)
        node_name = node_info.get('display_name', node_info.get('name', node_id)) if node_info else node_id
        
        renderer.print_banner(
            title="🌳 结构管理器",
            subtitle=f"节点: {node_name}"
        )
        
        children = structure.get_node_children(node_id)
        
        if not children:
            renderer.print_info("当前节点下没有子项")
            return True
            
        # 显示子项列表
        renderer.print_section("当前结构", "")
        
        for i, child in enumerate(children, 1):
            type_icon = "📄" if child.get('type') == 'page' else "🔌"
            enabled_icon = "✅" if child.get('enabled', True) else "❌"
            name = child.get('display_name', child.get('name', '未知'))
            desc = child.get('description', child.get('summary', ''))
            
            renderer.console.print(f"{i}. {type_icon} {enabled_icon} {name}")
            if desc:
                renderer.console.print(f"   📝 {desc}")
            renderer.console.print()
            
        return True
        
    def _disable_item(self, renderer, structure, node_id: str, target: str) -> bool:
        """禁用指定项目"""
        if structure.set_child_enabled(node_id, target, False):
            renderer.print_success(f"已禁用项目: {target}")
            return True
        else:
            renderer.print_error(f"禁用项目失败: {target}")
            return False
        
    def _enable_item(self, renderer, structure, node_id: str, target: str) -> bool:
        """启用指定项目"""
        if structure.set_child_enabled(node_id, target, True):
            renderer.print_success(f"已启用项目: {target}")
            return True
        else:
            renderer.print_error(f"启用项目失败: {target}")
            return False
        
    def _reorder_items(self, renderer, structure, node_id: str, config: Dict) -> bool:
        """重新排序项目"""
        items = config.get('items', [])
        if structure.reorder_children(node_id, items):
            renderer.print_success(f"已重新排序项目: {', '.join(items)}")
            return True
        else:
            renderer.print_error("排序失败")
            return False
        
    def _interactive_mode(self, renderer, structure, node_id: str) -> bool:
        """交互式管理模式"""
        renderer.clear_screen()
        renderer.print_banner(
            title="🌳 交互式结构管理",
            subtitle="管理页面和插件的组织结构"
        )
        
        while True:
            # 显示当前结构
            self._list_structure(renderer, structure, node_id)
            
            # 显示操作菜单
            options = [
                {'key': '1', 'name': '查看详情', 'description': '查看选中项的详细信息', 'icon': '🔍'},
                {'key': '2', 'name': '禁用项目', 'description': '临时禁用选中的项目', 'icon': '🚫'},
                {'key': '3', 'name': '启用项目', 'description': '重新启用被禁用的项目', 'icon': '✅'},
                {'key': '4', 'name': '重新排序', 'description': '调整项目显示顺序', 'icon': '📋'},
                {'key': '5', 'name': '重新扫描', 'description': '从源码重新扫描子项', 'icon': '🔄'},
            ]
            
            table = renderer.print_menu(
                title="管理操作",
                options=options,
                show_help=True
            )
            renderer.console.print(table)
            
            # 获取用户选择 - 使用单键输入
            choice = self._get_single_key_input(renderer)
            
            if choice == 'q' or choice == 'quit':
                break
            elif choice == '-':
                break  # 返回上级
            elif choice == '1':
                renderer.print_info("查看详情功能开发中...")
            elif choice == '2':
                target = self._get_target_input(renderer, structure, node_id, "禁用")
                if target:
                    self._disable_item(renderer, structure, node_id, target)
            elif choice == '3':
                target = self._get_target_input(renderer, structure, node_id, "启用")
                if target:
                    self._enable_item(renderer, structure, node_id, target)
            elif choice == '4':
                self._handle_reorder(renderer, structure, node_id)
            elif choice == '5':
                if structure.rescan_node(node_id):
                    renderer.print_success("重新扫描完成")
                else:
                    renderer.print_error("重新扫描失败")
            else:
                renderer.print_warning("无效选择")
                
            # 等待继续
            if choice != 'q':
                renderer.console.print("\n按 Enter 继续...")
                input()
                renderer.clear_screen()
                
        return True
    
    def _get_single_key_input(self, renderer) -> str:
        """获取单键输入"""
        import os
        import sys
        
        if os.name == 'nt':
            import msvcrt
            renderer.console.print("❯ 请选择操作 (数字键选择, - 返回, q 退出): ", end="")
            while True:
                try:
                    key = msvcrt.getch().decode('utf-8').lower()
                    print(key)  # 显示用户输入
                    return key
                except (UnicodeDecodeError, AttributeError):
                    continue
        else:
            # Unix/Linux系统的单键输入实现 - 使用通用输入工具
            from ..utils.input_utils import get_single_key_input
            return get_single_key_input("❯ 请选择操作 (数字键选择, - 返回, q 退出): ")
    
    def _get_target_input(self, renderer, structure, node_id: str, operation: str) -> str:
        """获取目标项目输入"""
        children = structure.get_node_children(node_id)
        if not children:
            renderer.print_info("当前节点下没有子项")
            return ""
        
        # 显示可选项目
        renderer.print_section(f"请选择要{operation}的项目:", "")
        for i, child in enumerate(children, 1):
            type_icon = "📄" if child.get('type') == 'page' else "🔌"
            enabled_icon = "✅" if child.get('enabled', True) else "❌"
            name = child.get('name', '未知')
            renderer.console.print(f"{i}. {type_icon} {enabled_icon} {name}")
        
        # 获取用户输入
        try:
            choice = input("\n请输入序号 (0取消): ").strip()
            if choice == '0':
                return ""
            
            index = int(choice) - 1
            if 0 <= index < len(children):
                return children[index].get('name', '')
            else:
                renderer.print_warning("序号无效")
                return ""
        except (ValueError, KeyboardInterrupt):
            return ""
    
    def _handle_reorder(self, renderer, structure, node_id: str) -> bool:
        """处理重新排序"""
        children = structure.get_node_children(node_id)
        if not children:
            renderer.print_info("当前节点下没有子项")
            return False
        
        renderer.print_section("当前顺序:", "")
        for i, child in enumerate(children, 1):
            type_icon = "📄" if child.get('type') == 'page' else "🔌"
            name = child.get('name', '未知')
            renderer.console.print(f"{i}. {type_icon} {name}")
        
        renderer.console.print("\n请输入新的排序（用空格分隔项目名称）:")
        renderer.console.print("例如: set dev_tools system_tools")
        
        try:
            new_order = input("新顺序: ").strip().split()
            if new_order:
                return self._reorder_items(renderer, structure, node_id, {'items': new_order})
            else:
                renderer.print_info("取消排序")
                return False
        except KeyboardInterrupt:
            return False
