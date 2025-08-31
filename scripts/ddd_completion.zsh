#!/bin/zsh
# DDD工具箱Zsh自动补全脚本 - 高性能版本
# 使用方法: source scripts/ddd_completion.zsh

# 补全缓存
typeset -A _DDD_COMPLETION_CACHE_ZSH
_DDD_CACHE_TTL_ZSH=300  # 缓存5分钟
_DDD_LAST_CACHE_TIME_ZSH=0

_ddd_get_completions_fast_zsh() {
    local path_key="$1"
    local current_time=$(date +%s)
    
    # 检查缓存
    if [[ -n "${_DDD_COMPLETION_CACHE_ZSH[$path_key]}" ]] && 
       [[ $((current_time - _DDD_LAST_CACHE_TIME_ZSH)) -lt $_DDD_CACHE_TTL_ZSH ]]; then
        echo "${_DDD_COMPLETION_CACHE_ZSH[$path_key]}"
        return 0
    fi
    
    # 重新获取（快速模式）
    local completions
    if [[ -z "$path_key" ]]; then
        # 根节点补全
        if [[ -f ".ddd_config/structure.json" ]]; then
            completions=$(python3 -c "
import json
try:
    with open('.ddd_config/structure.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    if '0' in data and 'children' in data['0']:
        children = []
        for child_id in data['0']['children']:
            if str(child_id) in data:
                children.append(data[str(child_id)]['name'])
        print('\n'.join(children))
except: pass
" 2>/dev/null)
        fi
    else
        # 路径补全
        completions=$(python3 -c "
import json
try:
    with open('.ddd_config/structure.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    path_parts = '$path_key'.split('/')
    current_id = '0'
    
    for part in path_parts:
        if not part: continue
        found = False
        if current_id in data and 'children' in data[current_id]:
            for child_id in data[current_id]['children']:
                if str(child_id) in data and data[str(child_id)]['name'] == part:
                    current_id = str(child_id)
                    found = True
                    break
        if not found:
            exit(1)
    
    if current_id in data and 'children' in data[current_id]:
        children = []
        for child_id in data[current_id]['children']:
            if str(child_id) in data:
                children.append(data[str(child_id)]['name'])
        print('\n'.join(children))
except: pass
" 2>/dev/null)
    fi
    
    # 更新缓存
    _DDD_COMPLETION_CACHE_ZSH[$path_key]="$completions"
    _DDD_LAST_CACHE_TIME_ZSH=$current_time
    
    echo "$completions"
}

_ddd() {
    local state line
    typeset -A opt_args

    _arguments -C \
        '--help[显示帮助信息]' \
        '-h[显示帮助信息]' \
        '--config-dir[指定配置目录]:config directory:_directories' \
        '--setup-completion[设置bash补全]' \
        '*::ddd commands:->commands' && return 0

    case $state in
        commands)
            local -a cmd_path
            cmd_path=($line)
            
            # 构建路径键
            local path_key=""
            if (( ${#cmd_path} > 0 )); then
                path_key="${(j:/:)cmd_path}"
            fi
            
            # 快速获取补全
            local completions_text
            completions_text=$(_ddd_get_completions_fast_zsh "$path_key")
            
            if [[ -n "$completions_text" ]]; then
                local -a completions
                completions=(${(f)completions_text})
                if (( ${#completions} > 0 )); then
                    _describe 'commands' completions
                fi
            fi
            ;;
    esac
}

# 注册补全函数
compdef _ddd ddd
