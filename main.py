#!/usr/bin/env python3
"""
DDD工具箱 - 项目根目录启动脚本
用于开发阶段直接运行，生产环境建议使用 `uv run ddd`
"""

import sys
from pathlib import Path

# 添加src路径以支持开发模式
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# 导入CLI模块
from ddd.cli import main as cli_main

if __name__ == "__main__":
    # 如果没有命令行参数，默认运行主界面
    if len(sys.argv) == 1:
        sys.argv.append('run')
    
    cli_main()
