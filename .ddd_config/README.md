# DDD工具箱本地配置目录

这个目录在开发模式下用于存储配置文件，包括：

## 配置文件

- `structure.json` - 应用结构树配置
- `paths.json` - 路径短名映射配置  
- `plugins.json` - 插件配置（计划中）

## 开发模式vs生产模式

### 开发模式 (当前)
- 配置文件存储在项目的 `.ddd_config/` 目录
- 便于调试和版本控制
- 自动检测：项目目录包含 `pyproject.toml` 且运行脚本在项目内

### 生产模式
- 配置文件存储在 `~/.ddd_toolbox/` 目录
- 用户级别的配置存储
- 不同项目间共享配置

## 自定义配置路径

可以通过以下方式自定义配置目录：

1. **命令行参数**
   ```bash
   ddd --config-dir /path/to/config run
   ```

2. **环境变量**
   ```bash
   export DDD_CONFIG_DIR=/path/to/config
   ddd run
   ```

3. **查看当前配置**
   ```bash
   ddd config
   ```

## 配置优先级

1. 命令行 `--config-dir` 参数
2. 环境变量 `DDD_CONFIG_DIR`
3. 开发模式：项目中的 `.ddd_config/`
4. 生产模式：用户目录 `~/.ddd_toolbox/`
