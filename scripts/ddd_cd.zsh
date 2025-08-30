#!/bin/zsh
# DDD 工具箱 cd 命令支持脚本 (Zsh版本)
# 将此脚本添加到 ~/.zshrc 中

ddd_cd() {
    if [ $# -eq 0 ]; then
        echo "用法: ddd_cd <路径短名>"
        return 1
    fi
    
    # 调用 ddd cd 命令获取目标路径
    local result=$(python -m ddd.cli cd "$1" 2>&1)
    
    # 检查是否成功
    if [ $? -eq 0 ] && [[ $result == cd* ]]; then
        # 执行cd命令
        eval "$result"
        echo "📁 已跳转到: $(pwd)"
    else
        # 显示错误信息
        echo "$result"
        return 1
    fi
}

# Zsh 自动补全支持
_ddd_cd_completion() {
    local completions=($(python -m ddd.cli completion "${words[2]}" 2>/dev/null))
    _describe 'paths' completions
}

# 注册补全
compdef _ddd_cd_completion ddd_cd

# 创建别名
alias dcd='ddd_cd'

echo "🔧 DDD 工具箱 cd 命令已加载 (Zsh)"
echo "使用方法:"
echo "  ddd_cd <路径短名>  # 或简写: dcd <路径短名>"
echo "  ddd run          # 打开主界面管理路径"
