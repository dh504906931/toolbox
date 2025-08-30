# 🚀 DDD工具箱

领域驱动设计(Domain-Driven Design)开发者工具集合

## ✨ 特性

- 🎨 **美观的TUI界面** - 基于Rich的现代化终端界面
- 🔌 **插件化架构** - 灵活的功能扩展系统
- 🌳 **树状结构管理** - 直观的页面和插件组织
- 📂 **路径管理** - 智能路径短名系统，快速目录跳转
- ⚡ **高性能** - 响应迅速的用户交互
- 🛠️ **开发友好** - 简单的插件开发API
- 🌍 **跨平台兼容** - 完美支持Windows、Linux、macOS

## 🚀 快速开始

### 安装运行

```bash
# 克隆项目
git clone <your-repo-url>
cd toolbox

# 使用uv运行（推荐）
uv run ddd

# 或开发模式
python main.py
```

### 路径管理快速上手

```bash
# 启动主界面
ddd

# 选择 [1] path 进入路径管理
# 添加常用路径短名，如：proj -> ~/projects/my-project

# 设置shell集成（可选）
source scripts/ddd_cd.sh  # bash用户
source scripts/ddd_cd.zsh # zsh用户

# 快速跳转
dcd proj  # 跳转到项目目录
```

### ⚙️ 配置管理

```bash
# 查看当前配置信息
ddd config

# 使用自定义配置目录
ddd --config-dir /path/to/config run

# 环境变量方式
export DDD_CONFIG_DIR=/path/to/config
ddd run
```

**配置优先级** (高到低):
1. 命令行 `--config-dir` 参数
2. 环境变量 `DDD_CONFIG_DIR`  
3. 开发模式: 项目中的 `.ddd_config/`
4. 生产模式: 用户目录 `~/.ddd_toolbox/`

## 🎯 核心功能

### 📂 路径管理
- **短名映射** - 为长路径设置简短别名
- **快速跳转** - `dcd <短名>` 直接跳转
- **自动补全** - Tab键补全路径短名
- **配置持久化** - 设置自动保存

### 🌳 结构管理
- **树状组织** - 页面和插件的层次结构
- **动态配置** - 运行时启用/禁用功能
- **设置界面** - 按 `*` 键进入页面设置

### 🔧 开发支持
- **插件系统** - 简单的插件开发框架
- **示例代码** - 丰富的开发示例
- **文档完善** - 详细的开发指南

## 🏗️ 项目结构

```
toolbox/
├── src/ddd/              # 主包源码
│   ├── core/            # 核心组件
│   │   ├── base.py      # 基础类定义
│   │   ├── renderer.py  # TUI渲染器
│   │   └── structure.py # 结构管理器
│   ├── pages/           # 页面实现
│   │   └── home.py      # 主页
│   ├── plugins/         # 插件实现
│   │   ├── path_plugin.py # 路径管理插件
│   │   └── set_plugin.py  # 结构管理插件
│   ├── utils/           # 工具模块
│   │   └── input_utils.py # 跨平台输入工具
│   └── cli.py           # CLI入口
├── scripts/             # Shell集成脚本
│   ├── ddd_cd.sh       # Bash集成
│   └── ddd_cd.zsh      # Zsh集成
├── examples/            # 开发示例
│   ├── simple_plugin.py # 插件示例
│   ├── simple_page.py   # 页面示例
│   └── README.md        # 示例说明
├── main.py              # 开发启动脚本
├── pyproject.toml       # 项目配置
├── DEVELOPMENT.md       # 开发指南
└── README.md           # 项目说明
```

## 📚 文档

- **[开发指南](DEVELOPMENT.md)** - 详细的开发文档
- **[示例代码](examples/)** - 插件和页面开发示例
- **[路径管理](examples/README.md#路径管理)** - 路径管理功能说明

## 🔧 开发

### 快速开始

```bash
# 查看示例
ls examples/

# 复制示例开始开发
cp examples/simple_plugin.py src/ddd/plugins/my_plugin.py

# 参考开发文档
cat DEVELOPMENT.md
```

### 主要概念

- **PageBase** - 页面基类，处理用户交互和导航
- **PluginBase** - 插件基类，实现具体功能逻辑
- **StructureManager** - 管理页面和插件的组织结构
- **配置持久化** - 自动保存用户设置到 `~/.ddd_toolbox/`

## 🌟 功能亮点

### 🚀 即开即用
- 零配置启动 - `uv run ddd` 立即可用
- 自动检测平台 - Windows/Linux/macOS完美支持
- 智能错误处理 - 友好的错误提示和恢复

### 🎯 高效工作流
- 路径快捷跳转 - 告别复杂的目录路径
- Tab键自动补全 - 快速输入路径短名
- 可视化管理界面 - 直观的配置和设置

### 🔧 开发友好
- 丰富的示例代码 - 快速上手插件开发
- 完善的开发文档 - 详细的API说明
- 模块化架构 - 易于扩展和维护

立即开始使用，体验高效的开发工具集！🚀
