"""
DDD - 美观的开发工具箱
"""

import typer
from typing import Optional
from .core import UI, Config, Logger
from .plugin_base import PluginManager
from .plugins.menu import MenuPlugin

app = typer.Typer(
    name="ddd",
    help="🚀 DDD - 美观的开发工具箱",
    add_completion=False
)

# 全局实例
ui = UI()
config = Config()
logger = Logger()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", "-d", help="启用调试模式"),
    config_dir: Optional[str] = typer.Option(None, "--config", "-c", help="指定配置目录")
):
    """启动 DDD 工具箱"""
    
    if ctx.invoked_subcommand is not None:
        return
    
    # 设置日志级别
    if debug:
        logger = Logger(level="DEBUG")
        logger.debug("调试模式已启用")
    
    # 设置配置目录
    if config_dir:
        config = Config(config_dir)
        logger.debug(f"使用配置目录: {config_dir}")
    
    # 显示欢迎信息
    ui.clear_screen()
    ui.print_banner(
        title="DDD 开发工具箱",
        subtitle="美观、高效、易用的开发者工具集合",
        version="0.1.0"
    )
    
    try:
        # 初始化插件管理器
        plugin_manager = PluginManager()
        
        # 注册主菜单插件
        menu_plugin = MenuPlugin()
        plugin_manager.register_plugin("menu", menu_plugin)
        
        # 运行主菜单
        plugin_manager.run_plugin("menu")
        
    except KeyboardInterrupt:
        ui.console.print("\n👋 再见!")
        raise typer.Exit(0)
    except Exception as e:
        logger.error(f"程序运行错误: {e}")
        ui.print_error(f"程序运行错误: {e}")
        if debug:
            logger.exception("详细错误信息")
        raise typer.Exit(1)


@app.command()
def version():
    """显示版本信息"""
    ui.print_info("DDD 开发工具箱 v0.1.0")


@app.command() 
def config_show():
    """显示配置信息"""
    ui.print_section("配置信息", f"配置目录: {config.config_dir}")


if __name__ == "__main__":
    app()