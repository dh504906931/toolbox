"""
Set插件 - 通用的结构管理插件
可以被任何Page调用来管理其子结构
"""

from typing import Any, Dict, List
from ..core.base import PluginBase
from ..core.structure import StructureManager


class SettingPlugin(PluginBase):
    """结构管理插件 - 管理页面和插件的组织"""
    
    def __init__(self):
        super().__init__(
            name="setting",
            summary="管理页面和插件的组织结构",
            category="system"
        )
        
    def run(self, operation: str = "interactive", args: List[str] = None, **kwargs) -> Any:
        """
        执行结构管理功能
        
        参数:
        - node_id: 要管理的节点ID
        - operation: 操作类型 (list/disable/enable/reorder/interactive)
        - target: 目标项目名称
        - config: 配置参数
        """
        from ..core.base import get_renderer
        renderer = get_renderer()
        
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
            
        # 显示子项列表 - 使用表格格式，避免内容溢出
        if children:
            from rich.table import Table
            from rich import box
            
            structure_table = Table(
                title="📝 当前结构",
                box=box.SIMPLE,
                border_style=renderer.theme.BORDER,
                show_header=False,
                expand=False,
                width=100
            )
            structure_table.add_column("序号", width=5)
            structure_table.add_column("状态", width=8)
            structure_table.add_column("名称", width=25)
            structure_table.add_column("描述", width=35)
            
            for i, child in enumerate(children, 1):
                type_icon = "📄" if child.get('type') == 'page' else "🔌"
                enabled_icon = "✅" if child.get('enabled', True) else "❌"
                name = child.get('display_name', child.get('name', '未知'))
                desc = child.get('description', child.get('summary', ''))
                
                # 限制描述长度
                if len(desc) > 30:
                    desc = desc[:27] + "..."
                
                structure_table.add_row(
                    f"{i}.",
                    f"{type_icon} {enabled_icon}",
                    name,
                    desc
                )
            
            renderer.console.print()
            renderer.console.print(structure_table)
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
        
        while True:
            # 清屏并显示简化界面
            renderer.clear_screen()
            
            # 显示简化的当前结构 - 只有选项框
            children = structure.get_node_children(node_id)
            
            if not children:
                renderer.print_info("当前节点下没有子项")
                return True
                
            # 显示子项列表 - 使用简单框架
            from rich.table import Table
            from rich import box
            
            structure_table = Table(
                box=box.ROUNDED,
                border_style="cyan",
                show_header=False,
                expand=False,
                width=80
            )
            structure_table.add_column("序号", width=5)
            structure_table.add_column("状态", width=8)
            structure_table.add_column("名称", width=25)
            structure_table.add_column("描述", width=35)
            
            for i, child in enumerate(children, 1):
                type_icon = "📄" if child.get('type') == 'page' else "🔌"
                enabled_icon = "✅" if child.get('enabled', True) else "❌"
                name = child.get('display_name', child.get('name', '未知'))
                desc = child.get('description', child.get('summary', ''))
                
                # 限制描述长度
                if len(desc) > 30:
                    desc = desc[:27] + "..."
                
                structure_table.add_row(
                    f"[{i}]",
                    f"{type_icon} {enabled_icon}",
                    name,
                    desc
                )
            
            renderer.console.print(structure_table)
            renderer.console.print()
            
            # 显示操作菜单 - 使用数字序号
            options = [
                {'key': '1', 'name': '切换状态', 'description': '启用/禁用选中项目', 'icon': '🔄'},
                {'key': '2', 'name': '排序项目', 'description': '调整项目显示顺序', 'icon': '📋'},
                {'key': '3', 'name': '重新扫描', 'description': '从源码重新扫描子项', 'icon': '🔄'},
                {'key': '4', 'name': '查看详情', 'description': '查看选中项的详细信息', 'icon': '🔍'},
            ]
            
            table = renderer.print_menu(
                title="管理操作",
                options=options,
                show_help=True
            )
            renderer.console.print(table)
            
            # 获取用户选择 - 使用单键输入
            choice = self._get_single_key_input(renderer)
            
            if choice == 'q':
                break
            elif choice == '-':
                break  # 返回上级
            elif choice == '1':
                self._handle_toggle_status(renderer, structure, node_id)
            elif choice == '2':
                self._handle_reorder(renderer, structure, node_id)
            elif choice == '3':
                if structure.rescan_node(node_id):
                    # 不显示确认提示，直接刷新界面
                    pass
                else:
                    renderer.print_error("重新扫描失败")
                    import time
                    time.sleep(1)
            elif choice == '4':
                target = self._get_target_input(renderer, structure, node_id, "查看详情")
                if target:
                    self._view_item_details(renderer, structure, node_id, target)
                    import time
                    time.sleep(2)  # 简单延时显示详情，然后自动返回
            else:
                renderer.print_warning(f"未知选项: {choice}")
                import time
                time.sleep(0.5)
                
        return True
    
    def _handle_toggle_status(self, renderer, structure, node_id: str) -> bool:
        """处理切换状态操作 - 支持连续操作"""
        while True:
            children = structure.get_node_children(node_id)
            if not children:
                renderer.print_info("当前节点下没有子项")
                return False
            
            # 清屏显示当前项目列表
            renderer.clear_screen()
            
            # 显示可选项目
            from rich.table import Table
            from rich import box
            
            selection_table = Table(
                title="🔄 切换启用状态",
                box=box.SIMPLE,
                border_style="cyan",
                show_header=False,
                expand=False,
                width=80
            )
            selection_table.add_column("序号", width=5)
            selection_table.add_column("状态", width=8)
            selection_table.add_column("名称", width=25)
            selection_table.add_column("描述", width=35)
            
            for i, child in enumerate(children, 1):
                type_icon = "📄" if child.get('type') == 'page' else "🔌"
                enabled_icon = "✅" if child.get('enabled', True) else "❌"
                name = child.get('name', '未知')
                desc = child.get('description', child.get('summary', ''))
                
                # 限制描述长度
                if len(desc) > 30:
                    desc = desc[:27] + "..."
                
                selection_table.add_row(f"[{i}]", f"{type_icon} {enabled_icon}", name, desc)
            
            renderer.console.print(selection_table)
            renderer.console.print()
            
            # 获取用户输入
            from ..utils.input_utils import get_single_key_input
            
            choice = get_single_key_input("请选择序号切换状态 (- 返回): ")
            if choice == '-':
                return True  # 返回主菜单
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(children):
                    child = children[index]
                    child_name = child.get('name', '')
                    current_enabled = child.get('enabled', True)
                    new_enabled = not current_enabled
                    
                    if structure.set_child_enabled(node_id, child_name, new_enabled):
                        status = "启用" if new_enabled else "禁用"
                        renderer.print_success(f"✅ 已{status}: {child_name}")
                        import time
                        time.sleep(0.8)  # 短暂显示状态
                        # 继续循环，不返回
                    else:
                        renderer.print_error(f"❌ 切换状态失败: {child_name}")
                        import time
                        time.sleep(1)
                else:
                    renderer.print_warning("⚠️ 序号无效")
                    import time
                    time.sleep(0.5)
            except ValueError:
                renderer.print_warning("⚠️ 请输入有效的数字")
                import time
                time.sleep(0.5)
            except KeyboardInterrupt:
                return True  # Ctrl+C 返回主菜单
    
    def _view_item_details(self, renderer, structure, node_id: str, target: str) -> bool:
        """查看项目详情"""
        children = structure.get_node_children(node_id)
        target_child = None
        
        for child in children:
            if child.get('name') == target:
                target_child = child
                break
        
        if not target_child:
            renderer.print_error(f"未找到项目: {target}")
            return False
        
        # 显示详情信息
        from rich.table import Table
        from rich import box
        
        details_table = Table(
            title=f"📋 项目详情: {target}",
            box=box.ROUNDED,
            border_style="cyan",
            show_header=False,
            width=80
        )
        details_table.add_column("属性", width=15, style="bold")
        details_table.add_column("值", width=60)
        
        # 基本信息
        details_table.add_row("名称", target_child.get('name', '未知'))
        details_table.add_row("类型", "📄 页面" if target_child.get('type') == 'page' else "🔌 插件")
        details_table.add_row("状态", "✅ 启用" if target_child.get('enabled', True) else "❌ 禁用")
        details_table.add_row("ID", str(target_child.get('id', '未知')))
        
        # 显示描述（如果有）
        if 'description' in target_child:
            details_table.add_row("描述", target_child.get('description', ''))
        
        # 显示路径（如果有）
        if 'path' in target_child:
            details_table.add_row("路径", target_child.get('path', ''))
        
        renderer.console.print(details_table)
        return True
    
    def _get_single_key_input(self, renderer) -> str:
        """获取单键输入"""
        from ..utils.input_utils import get_single_key_input
        return get_single_key_input("❯ 请选择操作 (1-4, - 返回, q 退出): ")
    
    def _get_target_input(self, renderer, structure, node_id: str, operation: str) -> str:
        """获取目标项目输入"""
        children = structure.get_node_children(node_id)
        if not children:
            renderer.print_info("当前节点下没有子项")
            return ""
        
        # 使用表格格式显示可选项目，保持界面美观
        from rich.table import Table
        from rich import box
        
        selection_table = Table(
            title=f"请选择要{operation}的项目:",
            box=box.SIMPLE,
            border_style="cyan",
            show_header=False,
            expand=False,
            width=80
        )
        selection_table.add_column("序号", width=5)
        selection_table.add_column("状态", width=8)
        selection_table.add_column("名称", width=25)
        
        for i, child in enumerate(children, 1):
            type_icon = "📄" if child.get('type') == 'page' else "🔌"
            enabled_icon = "✅" if child.get('enabled', True) else "❌"
            name = child.get('name', '未知')
            selection_table.add_row(f"[{i}]", f"{type_icon} {enabled_icon}", name)
        
        renderer.console.print(selection_table)
        
        # 获取用户输入，使用单键输入
        from ..utils.input_utils import get_single_key_input
        
        choice = get_single_key_input(f"\n请选择序号 1-{len(children)} (- 取消): ")
        if choice == '-':
            return ""
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(children):
                return children[index].get('name', '')
            else:
                renderer.print_warning("序号无效")
                import time
                time.sleep(0.5)
                return ""
        except ValueError:
            renderer.print_warning("请输入有效的数字")
            import time
            time.sleep(0.5)
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
        
        renderer.console.print("\n💡 排序说明:")
        renderer.console.print("• 输入数字序号（用空格分隔）进行部分排序")
        renderer.console.print("• 例如: '3 1 2' 将第3项移到前面，然后是第1项和第2项")
        renderer.console.print("• 或输入完整的项目名称进行全量排序")
        renderer.console.print("• 按 '-' 取消操作")
        
        try:
            new_order_str = renderer.get_line_input("新顺序", "").strip()
            if new_order_str == '-':
                renderer.print_info("取消排序")
                return False
            elif not new_order_str:
                renderer.print_info("取消排序")
                return False
            
            # 尝试解析为数字序号
            if self._is_number_sequence(new_order_str):
                return self._reorder_by_numbers(renderer, structure, node_id, new_order_str, children)
            else:
                # 按项目名称排序
                new_order = new_order_str.split()
                return self._reorder_items(renderer, structure, node_id, {'items': new_order})
                
        except KeyboardInterrupt:
            renderer.print_info("取消排序")
            return False
    
    def _is_number_sequence(self, input_str: str) -> bool:
        """检查输入是否为数字序列"""
        try:
            numbers = input_str.split()
            for num_str in numbers:
                int(num_str)
            return True
        except ValueError:
            return False
    
    def _reorder_by_numbers(self, renderer, structure, node_id: str, number_str: str, children: List) -> bool:
        """根据数字序号进行部分排序"""
        try:
            # 解析数字序号
            indices = [int(x) - 1 for x in number_str.split()]  # 转换为0-based索引
            
            # 验证索引有效性
            valid_indices = []
            for idx in indices:
                if 0 <= idx < len(children):
                    valid_indices.append(idx)
                else:
                    renderer.print_warning(f"序号 {idx + 1} 无效，已忽略")
            
            if not valid_indices:
                renderer.print_error("没有有效的序号")
                return False
            
            # 构建新的排序：指定的项目在前，其他项目在后
            new_order = []
            
            # 先添加指定顺序的项目
            for idx in valid_indices:
                if idx < len(children):
                    new_order.append(children[idx].get('name'))
            
            # 再添加未指定的项目
            for i, child in enumerate(children):
                if i not in valid_indices:
                    new_order.append(child.get('name'))
            
            return self._reorder_items(renderer, structure, node_id, {'items': new_order})
            
        except ValueError as e:
            renderer.print_error(f"数字解析错误: {e}")
            return False
