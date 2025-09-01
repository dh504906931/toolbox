import sys
from ddd.cli import setup_bash_completion
from ddd.cli import DDDCLI


def main():
    """CLI主入口"""
    # 处理特殊命令
    if len(sys.argv) > 1 and sys.argv[1] == "--setup-completion":
        setup_bash_completion()
        return

    # 创建CLI实例并运行
    cli = DDDCLI()
    args = sys.argv[1:]  # 移除脚本名称
    cli.run(args)


if __name__ == "__main__":
    main()
