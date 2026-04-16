#!/bin/bash

# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR=$(dirname "$(realpath "$0")")

# 切换到脚本所在目录
cd "${SCRIPT_DIR}" || exit 1

# 提示用户拖入.py文件
echo "请将.py文件拖到此处，然后按回车键运行："
read -r file_path

# 检查用户是否输入了文件路径
if [ -z "$file_path" ]; then
    echo "错误：未提供文件路径"
    read -rp "按Enter键退出..."
    exit 1
fi

# 移除路径中的单引号（某些终端自动添加）
clean_path=$(echo "$file_path" | sed "s/^'//;s/'$//")

# 检查文件是否存在
if [ ! -f "$clean_path" ]; then
    echo "错误：文件不存在 - $clean_path"
    read -rp "按Enter键退出..."
    exit 1
fi

# 检查文件扩展名
if [[ "$clean_path" != *.py ]]; then
    echo "错误：只能运行.py文件 - $clean_path"
    read -rp "按Enter键退出..."
    exit 1
fi

# 运行Python文件
echo "正在运行: $clean_path"
python3 "$clean_path"

# 等待用户按回车退出
echo ""
read -rp "按Enter键退出..."