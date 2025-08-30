# 📚 DDD工具箱示例

这个目录包含了插件和页面开发的示例代码，帮助开发者快速上手。

## 📁 文件结构

```
examples/
├── README.md           # 本文件
├── simple_plugin.py    # 插件开发示例
└── simple_page.py      # 页面开发示例
```

## 🔌 插件示例

### 1. 简单插件 (SimplePlugin)
最基本的插件实现，展示：
- 基本插件结构
- 用户交互处理
- 结果返回

### 2. 计算器插件 (CalculatorPlugin)
交互式插件示例，展示：
- 用户输入处理
- 数据验证
- 错误处理

### 3. 文件管理插件 (FileManagerPlugin)
复杂插件示例，展示：
- 多功能菜单
- 文件系统操作
- 状态管理

## 📄 页面示例

### 1. 简单页面 (SimplePage)
基础页面实现，展示：
- 页面结构定义
- 子项配置
- 静态内容显示

### 2. 动态页面 (DynamicPage)
动态内容页面，展示：
- 状态管理
- 内容更新
- 数据操作

### 3. 菜单页面 (MenuPage)
复杂菜单结构，展示：
- 多级导航
- 混合子项（页面+插件）
- 结构化内容

### 4. 可配置页面 (ConfigurablePage)
配置管理示例，展示：
- 配置文件处理
- 持久化存储
- 动态配置应用

## 🚀 使用方法

### 集成到项目

1. **复制示例文件**
   ```bash
   cp examples/simple_plugin.py src/ddd/plugins/my_plugin.py
   cp examples/simple_page.py src/ddd/pages/my_page.py
   ```

2. **修改类名和功能**
   ```python
   # 重命名类
   class MyPlugin(PluginBase):
       def get_description(self) -> str:
           return "我的插件功能"
   ```

3. **在页面中注册**
   ```python
   def get_default_children(self) -> List[Dict]:
       return [
           {
               "type": "plugin",
               "name": "my_plugin",
               "description": "我的插件"
           }
       ]
   ```

### 测试示例

```bash
# 运行主程序
python main.py

# 或使用 uv
uv run ddd
```

## 🎯 开发技巧

### 1. 插件开发要点
- 继承 `PluginBase`
- 实现 `get_description()` 和 `run()` 方法
- 使用 `get_user_input()` 处理用户输入
- 合理处理异常和错误

### 2. 页面开发要点
- 继承 `PageBase` 
- 实现 `get_title()`, `get_description()`, `get_default_children()` 方法
- 通过 `get_content()` 提供动态内容
- 使用结构管理器处理子项

### 3. 最佳实践
- 使用 emoji 提升用户体验
- 提供清晰的错误信息
- 支持配置持久化
- 确保跨平台兼容性

## 📖 相关文档

- [开发指南](../DEVELOPMENT.md) - 详细的开发文档
- [主README](../README.md) - 项目概览
- [源码](../src/ddd/) - 核心代码实现

## 💡 创意点子

基于这些示例，你可以开发：

### 插件创意
- 🌐 **API工具** - REST API测试器
- 📊 **数据分析** - CSV/JSON数据处理
- 🗃️ **数据库工具** - 数据库连接管理
- 🎨 **代码生成** - 模板代码生成器
- 📝 **笔记管理** - Markdown笔记系统

### 页面创意
- 🏠 **工作台** - 个人工作区管理
- 📂 **项目管理** - 项目文件组织
- ⚡ **快捷操作** - 常用命令快捷方式
- 📈 **监控面板** - 系统状态监控
- 🔧 **开发工具** - 开发环境管理

开始构建你的创意功能吧！🚀
