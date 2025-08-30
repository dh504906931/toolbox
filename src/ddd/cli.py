#!/usr/bin/env python3
"""
DDD工具箱命令行接口
支持 ddd run, ddd cd <路径短名> 等命令
"""

import sys
import os
import argparse
from typing import List, Optional
from .core.structure import StructureManager
from .pages.home import HomePage
from .utils.config import set_config_dir


def cd_command(short_name: str) -> None:
    """处理 cd 命令"""
    try:
        # 初始化结构管理器
        structure = StructureManager()
        
        # 获取path插件
        path_plugin = structure.get_plugin("path")
        if not path_plugin:
            print("❌ 路径插件未找到")
            sys.exit(1)
        
        # 获取路径
        target_path = path_plugin.run(operation="get", short_name=short_name)
        if not target_path:
            print(f"❌ 未找到路径短名: {short_name}")
            
            # 显示可用的路径短名
            paths = path_plugin.run(operation="list")
            if paths:
                print("\n📁 可用路径:")
                for name, info in paths.items():
                    print(f"  📍 {name} -> {info['path']}")
                    if info.get('description'):
                        print(f"      {info['description']}")
            else:
                print("\n💡 提示: 使用 'ddd path' 添加路径短名")
            sys.exit(1)
        
        # 检查路径是否存在
        if not os.path.exists(target_path):
            print(f"⚠️ 路径不存在: {target_path}")
            choice = input("是否仍要输出cd命令? (y/N): ").strip().lower()
            if choice != 'y':
                sys.exit(1)
        
        # 输出cd命令，让shell执行
        print(f"cd '{target_path}'")
        
    except Exception as e:
        print(f"❌ 执行cd命令失败: {e}")
        sys.exit(1)


def run_command() -> None:
    """运行主界面"""
    try:
        # 初始化结构管理器
        structure = StructureManager()
        
        # 创建并运行主页
        home_page = HomePage()
        structure.register_page_instance(home_page)
        home_page.run()
        
    except KeyboardInterrupt:
        print("\n👋 感谢使用 DDD 工具箱！")
    except Exception as e:
        print(f"❌ 程序运行错误: {e}")
        sys.exit(1)


def get_completions(partial: str) -> List[str]:
    """获取自动补全建议"""
    try:
        structure = StructureManager()
        
        # 获取path插件的补全
        path_plugin = structure.get_plugin("path")
        if path_plugin:
            return path_plugin.run(operation="get_completions", partial=partial)
        
        return []
    except Exception:
        return []


def show_config_info() -> None:
    """显示配置信息"""
    try:
        from .utils.config import get_config_manager
        
        config_manager = get_config_manager()
        info = config_manager.get_info()
        
        print("🔧 DDD工具箱配置信息")
        print("=" * 50)
        print(f"📂 配置目录: {info['config_dir']}")
        print(f"🔨 开发模式: {'是' if info['is_development_mode'] else '否'}")
        
        if info['project_root']:
            print(f"📁 项目根目录: {info['project_root']}")
        
        if info['custom_config_dir']:
            print(f"⚙️ 自定义配置: {info['custom_config_dir']}")
        
        print(f"\n📄 配置文件:")
        print(f"  🌳 结构文件: {info['structure_file']}")
        print(f"  🛤️ 路径文件: {info['paths_file']}")
        print(f"  🔌 插件配置: {info['plugins_config_file']}")
        
        # 检查文件是否存在
        print(f"\n📊 文件状态:")
        for name, path in [
            ("结构文件", info['structure_file']),
            ("路径文件", info['paths_file']),
            ("插件配置", info['plugins_config_file'])
        ]:
            exists = os.path.exists(path)
            status = "✅ 存在" if exists else "❌ 不存在"
            print(f"  {name}: {status}")
        
        # 环境变量提示
        print(f"\n💡 环境变量:")
        print(f"  DDD_CONFIG_DIR={os.environ.get('DDD_CONFIG_DIR', '(未设置)')}")
        
    except Exception as e:
        print(f"❌ 获取配置信息失败: {e}")


def main() -> None:
    """命令行主入口"""
    parser = argparse.ArgumentParser(
        prog='ddd',
        description='DDD 开发工具箱 - 领域驱动设计开发者工具集合'
    )
    
    # 全局选项
    parser.add_argument(
        '--config-dir', '-c',
        help='自定义配置目录路径',
        metavar='PATH'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # run 命令
    run_parser = subparsers.add_parser('run', help='运行主界面')
    
    # cd 命令
    cd_parser = subparsers.add_parser('cd', help='跳转到指定路径')
    cd_parser.add_argument('short_name', help='路径短名')
    
    # completion 命令 (用于shell补全)
    comp_parser = subparsers.add_parser('completion', help='获取补全建议')
    comp_parser.add_argument('partial', nargs='?', default='', help='部分输入')
    
    # config 命令 (显示配置信息)
    config_parser = subparsers.add_parser('config', help='显示配置信息')
    
    # 解析参数
    args = parser.parse_args()
    
    # 设置自定义配置目录（如果提供）
    if hasattr(args, 'config_dir') and args.config_dir:
        set_config_dir(args.config_dir)
    
    if args.command == 'run' or args.command is None:
        run_command()
    elif args.command == 'cd':
        cd_command(args.short_name)
    elif args.command == 'completion':
        completions = get_completions(args.partial)
        for completion in completions:
            print(completion)
    elif args.command == 'config':
        show_config_info()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()