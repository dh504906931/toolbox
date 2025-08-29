# Toolbox

一个基于插件架构的命令行工具箱。

## 特性

- 插件式架构，易于扩展
- 支持交互式界面和命令行模式
- 命令补全功能
- 统一的插件接口
- 层级化的插件管理

## 安装

```bash
pip install .
```

## 使用方法

### 命令行模式

```bash
# 进入交互式界面
ddd

# 直接调用插件
ddd <插件名> [参数...]

# 使用Tab补全
ddd <Tab>
ddd 插件名 <Tab>
```

### 交互式界面

- 使用数字键选择菜单项
- 使用'-'返回上级菜单
- 使用'q'退出程序

## 开发插件

1. 在 `src/toolbox/plugins` 目录下创建新的插件模块
2. 继承 `Plugin` 基类并实现必要的方法
3. 在模块中导出 `plugin_class` 变量
4. 在 `config/structure.yaml` 中配置插件层级关系
5. 在 `config/plugins/<插件名>/` 目录下创建插件配置文件

示例插件：

```python
from toolbox.plugin_base import Plugin

class MyPlugin(Plugin):
    def __init__(self):
        super().__init__(
            name="my_plugin",
            description="这是一个示例插件"
        )
    
    def brief_info(self) -> str:
        return "示例插件的简要说明"
        
    def help(self) -> str:
        return "示例插件的详细帮助信息"
        
    def handle_interactive(self) -> None:
        # 实现交互式界面
        pass
        
    def handle_cli(self, args: List[str]) -> None:
        # 实现命令行处理
        pass

# 导出插件类
plugin_class = MyPlugin
```

## 依赖

- Python >= 3.8
- click >= 8.0.0
- rich >= 10.0.0
- prompt_toolkit >= 3.0.0
- typer >= 0.9.0

## 许可证

MIT