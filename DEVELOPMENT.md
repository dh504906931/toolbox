# 🛠️ DDD工具箱开发指南

## 📖 快速开始

### 环境设置
```bash
# 克隆项目
git clone <your-repo>
cd toolbox

# 安装依赖
uv sync

# 开发模式运行
python main.py
# 或
uv run ddd
```

## 🏗️ 架构概览

### 核心组件
- **PageBase** - 页面基类，处理用户交互
- **PluginBase** - 插件基类，实现具体功能
- **StructureManager** - 管理页面和插件的组织结构
- **Renderer** - TUI界面渲染器

### 数据流
```
用户输入 → PageBase → PluginBase → 业务逻辑 → 渲染结果
```

## 🔌 插件开发

### 基本结构
```python
from ddd.core.base import PluginBase
from typing import Any, Dict

class MyPlugin(PluginBase):
    """我的插件"""
    
    def get_description(self) -> str:
        return "插件功能描述"
    
    def run(self, **kwargs) -> Any:
        """插件主要逻辑"""
        # 实现你的功能
        return "结果"
```

### 插件配置
```python
import json
from pathlib import Path

class ConfigurablePlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.config_file = Path.home() / ".ddd_toolbox" / "my_plugin.json"
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        if self.config_file.exists():
            return json.loads(self.config_file.read_text())
        return {}
    
    def save_config(self):
        self.config_file.parent.mkdir(exist_ok=True)
        self.config_file.write_text(json.dumps(self.config, indent=2))
```

### 用户输入处理
```python
from ddd.utils.input_utils import get_user_input

class InteractivePlugin(PluginBase):
    def run(self, **kwargs):
        # 跨平台用户输入
        name = get_user_input("请输入名称: ")
        confirm = get_user_input("确认吗? (y/n): ")
        
        if confirm.lower() == 'y':
            return f"处理: {name}"
        return "已取消"
```

## 📄 页面开发

### 基本页面
```python
from ddd.core.base import PageBase
from typing import List, Dict

class MyPage(PageBase):
    """我的页面"""
    
    def get_title(self) -> str:
        return "我的页面"
    
    def get_description(self) -> str:
        return "页面功能描述"
    
    def get_default_children(self) -> List[Dict]:
        """定义默认子项"""
        return [
            {
                "type": "plugin",
                "name": "my_plugin",
                "description": "我的插件"
            }
        ]
    
    def get_options(self) -> List[str]:
        """从结构管理器获取选项"""
        return self.structure_manager.get_enabled_children(self.node_id)
    
    def handle_selection(self, selection: int) -> bool:
        """处理用户选择"""
        options = self.get_options()
        if 1 <= selection <= len(options):
            option = options[selection - 1]
            if option["type"] == "plugin":
                plugin = self.structure_manager.get_plugin(option["name"])
                result = plugin.run(node_id=self.node_id)
                self.show_result(result)
            return True
        return False
```

### 动态页面
```python
class DynamicPage(PageBase):
    def __init__(self):
        super().__init__()
        self.data = []
    
    def get_title(self) -> str:
        return f"动态页面 ({len(self.data)} 项)"
    
    def get_content(self) -> str:
        """动态内容"""
        if not self.data:
            return "暂无数据"
        
        content = []
        for i, item in enumerate(self.data, 1):
            content.append(f"  {i}. {item}")
        return "\n".join(content)
    
    def refresh_data(self):
        """刷新数据"""
        self.data = self.load_data_from_somewhere()
```

## 📁 文件结构

### 添加新插件
1. 在 `src/ddd/plugins/` 创建文件
2. 实现插件类
3. 在需要的页面中注册

```python
# src/ddd/plugins/my_plugin.py
class MyPlugin(PluginBase):
    pass

# 在页面中使用
def get_default_children(self):
    return [
        {
            "type": "plugin", 
            "name": "my_plugin",
            "description": "我的插件"
        }
    ]
```

### 添加新页面
1. 在 `src/ddd/pages/` 创建文件
2. 实现页面类
3. 在父页面中注册

```python
# src/ddd/pages/my_page.py
class MyPage(PageBase):
    pass

# 在父页面中注册
def get_default_children(self):
    return [
        {
            "type": "page",
            "name": "my_page", 
            "description": "我的页面"
        }
    ]
```

## 🧪 测试

### 插件测试
```python
def test_my_plugin():
    plugin = MyPlugin()
    result = plugin.run(test_param="test")
    assert result == "expected_result"
```

### 页面测试
```python
def test_my_page():
    page = MyPage()
    options = page.get_options()
    assert len(options) > 0
    
    # 测试选择处理
    success = page.handle_selection(1)
    assert success
```

## 🎯 最佳实践

### 1. 错误处理
```python
def run(self, **kwargs):
    try:
        # 主要逻辑
        result = self.do_something()
        return result
    except Exception as e:
        return f"❌ 错误: {e}"
```

### 2. 用户友好的反馈
```python
def run(self, **kwargs):
    print("🔄 正在处理...")
    result = self.process()
    print("✅ 处理完成!")
    return result
```

### 3. 配置持久化
```python
def save_config(self):
    """保存配置到用户目录"""
    config_dir = Path.home() / ".ddd_toolbox"
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / f"{self.__class__.__name__.lower()}.json"
    config_file.write_text(json.dumps(self.config, indent=2))
```

### 4. 跨平台兼容
```python
from ddd.utils.input_utils import get_user_input

# 使用跨平台输入工具
user_input = get_user_input("提示: ")

# 路径处理
from pathlib import Path
path = Path.home() / "config" / "file.json"
```

## 🔧 调试技巧

### 添加调试日志
```python
import logging

logger = logging.getLogger(__name__)

def run(self, **kwargs):
    logger.debug(f"运行插件，参数: {kwargs}")
    # 主要逻辑
```

### 查看结构树
```bash
# 查看当前结构
ddd set list

# 重新扫描结构
# 在页面中按 * 进入设置，选择重新扫描
```

## 📚 示例参考

查看现有插件实现：
- `src/ddd/plugins/path_plugin.py` - 路径管理插件
- `src/ddd/plugins/set_plugin.py` - 结构管理插件
- `src/ddd/pages/home.py` - 主页实现
