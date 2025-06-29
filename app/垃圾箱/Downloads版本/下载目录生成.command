#!/bin/bash
# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR=$(dirname "$(realpath "$0")")
# 切换到脚本所在目录
cd "${SCRIPT_DIR}"
# 运行 Downloads.py
python3 Downloads.py
