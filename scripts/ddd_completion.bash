#!/bin/bash
# DDD工具箱Bash自动补全脚本 - 高性能版本
# 使用方法: source scripts/ddd_completion.bash

# 简单的补全缓存（避免关联数组兼容性问题）
_DDD_CACHE_TTL=60   # 缓存1分钟（减少缓存时间以确保数据新鲜）
_DDD_LAST_CACHE_TIME=0
_DDD_CACHED_ROOT_COMPLETIONS=""

_ddd_get_completions_fast() {
    local path_key="$1"
    local current_time=$(date +%s)
    
    # 简单缓存策略：只缓存根节点（最常用的场景）
    if [[ -z "$path_key" ]] && [[ -n "$_DDD_CACHED_ROOT_COMPLETIONS" ]] && 
       [[ $((current_time - _DDD_LAST_CACHE_TIME)) -lt $_DDD_CACHE_TTL ]]; then
        echo "$_DDD_CACHED_ROOT_COMPLETIONS"
        return 0
    fi
    
    # 缓存失效，重新获取（使用快速模式）
    local completions
    if [[ -z "$path_key" ]]; then
        # 根节点 - 直接读取结构文件获取第一层节点
        if [[ -f ".ddd_config/structure.json" ]]; then
            completions=$(python3 -c "
import json, sys
try:
    with open('.ddd_config/structure.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    if '0' in data and 'children' in data['0']:
        children = []
        for child_id in data['0']['children']:
            if str(child_id) in data:
                children.append(data[str(child_id)]['name'])
        print(' '.join(children))
except: pass
" 2>/dev/null)
        fi
    else
        # 使用Python快速查询（最小化加载）
        completions=$(python3 -c "
import json, sys
try:
    with open('.ddd_config/structure.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 解析路径
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
            sys.exit(1)
    
    # 获取子节点
    if current_id in data and 'children' in data[current_id]:
        children = []
        for child_id in data[current_id]['children']:
            if str(child_id) in data:
                children.append(data[str(child_id)]['name'])
        print(' '.join(children))
except: pass
" 2>/dev/null)
    fi
    
    # 更新缓存（仅根节点）
    if [[ -z "$path_key" ]]; then
        _DDD_CACHED_ROOT_COMPLETIONS="$completions"
        _DDD_LAST_CACHE_TIME=$current_time
    fi
    
    echo "$completions"
}

_ddd_completion() {
    local cur prev words cword
    _init_completion || return

    # 获取当前命令路径
    local cmd_path=()
    for ((i=1; i<cword; i++)); do
        if [[ "${words[i]}" != -* ]]; then
            cmd_path+=("${words[i]}")
        fi
    done
    
    # 构建路径字符串用于缓存键
    local path_key=""
    if [[ ${#cmd_path[@]} -gt 0 ]]; then
        printf -v path_key "%s/" "${cmd_path[@]}"
        path_key="${path_key%/}"  # 移除尾部斜杠
    fi

    # 快速获取补全建议
    local completions
    completions=$(_ddd_get_completions_fast "$path_key")

    # 添加通用选项（仅在根级别）
    local options=""
    if [[ ${#cmd_path[@]} -eq 0 ]]; then
        options="--help -h --config-dir --setup-completion"
    fi
    
    # 生成补全结果
    COMPREPLY=($(compgen -W "$completions $options" -- "$cur"))
}

# 注册补全函数
complete -F _ddd_completion ddd
