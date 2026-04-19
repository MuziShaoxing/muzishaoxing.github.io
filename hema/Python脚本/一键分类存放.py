#!/usr/bin/env python3
"""
文件整理脚本
按照文件名中的中文部分创建文件夹并移动文件
无中文的文件统一移动到"其他"文件夹
在Downloads目录下创建"文件整理"文件夹作为整理目录
递归遍历所有文件（包括已整理文件夹内的文件）进行重新分类
并删除所有空闲文件夹
"""

import os
import shutil
import re
import argparse
from pathlib import Path
from collections import defaultdict

def extract_chinese_part(filename):
    """
    从文件名中提取中文部分
    """
    # 获取文件名（不含扩展名）
    name_without_ext = os.path.splitext(filename)[0]
    
    # 使用正则表达式匹配中文字符
    chinese_chars = re.findall(r'[\u4e00-\u9fff]+', name_without_ext)
    
    if chinese_chars:
        # 返回所有中文字符的组合
        return ''.join(chinese_chars)
    
    return None

def remove_empty_folders(directory_path):
    """
    递归删除所有空文件夹
    
    Args:
        directory_path: 要清理的目录路径
        
    Returns:
        int: 删除的空文件夹数量
    """
    directory = Path(directory_path).expanduser()
    empty_folders_removed = 0
    
    # 自底向上遍历目录树，确保先删除子空文件夹
    for root, dirs, files in os.walk(str(directory), topdown=False):
        current_dir = Path(root)
        
        # 检查当前目录是否为空（不包括隐藏文件）
        try:
            items = list(current_dir.iterdir())
            # 只考虑非隐藏文件和文件夹
            visible_items = [item for item in items if not item.name.startswith('.')]
            
            # 如果是空文件夹（没有可见文件或子文件夹）
            if len(visible_items) == 0:
                # 跳过根目录本身（避免删除用户指定的根目录）
                if current_dir == directory:
                    continue
                    
                try:
                    # 获取相对路径用于显示
                    if directory in current_dir.parents or current_dir == directory:
                        rel_path = current_dir.relative_to(directory)
                        print(f"删除空文件夹: {rel_path}")
                    else:
                        print(f"删除空文件夹: {current_dir}")
                    
                    current_dir.rmdir()
                    empty_folders_removed += 1
                except OSError as e:
                    print(f"无法删除文件夹 {current_dir}: {e}")
        except (PermissionError, OSError) as e:
            print(f"无法访问文件夹 {current_dir}: {e}")
    
    return empty_folders_removed

def organize_files_by_chinese(directory_path):
    """
    按照文件名中的中文部分整理文件
    深度扫描模式：递归遍历所有文件（包括已整理文件夹内的文件）进行重新分类
    
    Args:
        directory_path: 要整理的目录路径
    """
    directory = Path(directory_path).expanduser()
    
    if not directory.exists():
        print(f"错误：目录 {directory} 不存在")
        return
    
    if not directory.is_dir():
        print(f"错误：{directory} 不是一个目录")
        return
    
    # 创建主整理文件夹
    organized_dir = directory / "文件整理"
    organized_dir.mkdir(exist_ok=True)
    
    print(f"\n开始深度整理目录: {directory}")
    print(f"文件将移动到: {organized_dir}")
    print("将递归扫描所有文件（包括已整理文件夹内的文件）并重新分类")
    
    # 用于统计信息
    chinese_folders = defaultdict(int)
    other_count = 0
    moved_files = 0
    renamed_files = 0
    skipped_files = 0
    
    # 遍历所有文件和子目录
    for file_path in directory.rglob('*'):
        # 跳过目录，只处理文件
        if file_path.is_file():
            filename = file_path.name
            chinese_part = extract_chinese_part(filename)
            
            try:
                if chinese_part:
                    # 目标文件夹应该根据中文部分创建
                    target_dir = organized_dir / chinese_part
                    target_dir.mkdir(exist_ok=True)
                    
                    # 目标文件路径
                    target_file_path = target_dir / filename
                    
                    # 检查文件是否已经在正确的位置
                    if file_path.parent == target_dir:
                        # 文件已经在正确的中文文件夹中，跳过
                        skipped_files += 1
                        continue
                    
                    # 如果目标文件已存在，处理重名情况
                    if target_file_path.exists():
                        counter = 1
                        name_parts = os.path.splitext(filename)
                        while target_file_path.exists():
                            new_filename = f"{name_parts[0]}_{counter}{name_parts[1]}"
                            target_file_path = target_dir / new_filename
                            counter += 1
                        
                        # 显示相对路径
                        if directory in file_path.parents or file_path.parent == directory:
                            rel_path = file_path.relative_to(directory)
                            print(f"移动: {rel_path} -> 文件整理/{chinese_part}/{new_filename}")
                        else:
                            print(f"移动: {filename} -> 文件整理/{chinese_part}/{new_filename}")
                        
                        renamed_files += 1
                    else:
                        # 显示相对路径
                        if directory in file_path.parents or file_path.parent == directory:
                            rel_path = file_path.relative_to(directory)
                            print(f"移动: {rel_path} -> 文件整理/{chinese_part}/")
                        else:
                            print(f"移动: {filename} -> 文件整理/{chinese_part}/")
                    
                    # 移动文件
                    shutil.move(str(file_path), str(target_file_path))
                    
                    # 更新统计
                    chinese_folders[chinese_part] += 1
                    moved_files += 1
                    
                else:
                    # 无中文的文件移动到"其他"文件夹
                    target_dir = organized_dir / "其他"
                    target_dir.mkdir(exist_ok=True)
                    
                    target_file_path = target_dir / filename
                    
                    # 检查文件是否已经在"其他"文件夹中
                    if file_path.parent == target_dir:
                        # 文件已经在"其他"文件夹中，跳过
                        skipped_files += 1
                        continue
                    
                    # 如果目标文件已存在，处理重名情况
                    if target_file_path.exists():
                        counter = 1
                        name_parts = os.path.splitext(filename)
                        while target_file_path.exists():
                            new_filename = f"{name_parts[0]}_{counter}{name_parts[1]}"
                            target_file_path = target_dir / new_filename
                            counter += 1
                        
                        # 显示相对路径
                        if directory in file_path.parents or file_path.parent == directory:
                            rel_path = file_path.relative_to(directory)
                            print(f"移动: {rel_path} -> 文件整理/其他/{new_filename}")
                        else:
                            print(f"移动: {filename} -> 文件整理/其他/{new_filename}")
                        
                        renamed_files += 1
                    else:
                        # 显示相对路径
                        if directory in file_path.parents or file_path.parent == directory:
                            rel_path = file_path.relative_to(directory)
                            print(f"移动: {rel_path} -> 文件整理/其他/")
                        else:
                            print(f"移动: {filename} -> 文件整理/其他/")
                    
                    # 移动文件
                    shutil.move(str(file_path), str(target_file_path))
                    
                    # 更新统计
                    other_count += 1
                    moved_files += 1
                    
            except Exception as e:
                print(f"移动文件 {filename} 时出错: {e}")
    
    # 删除空闲文件夹（包括所有子文件夹）
    print("\n开始删除空闲文件夹...")
    empty_folders_count = remove_empty_folders(directory)
    
    # 打印统计信息
    print(f"\n整理完成！")
    print(f"共移动了 {moved_files} 个文件到 '文件整理' 文件夹")
    if renamed_files > 0:
        print(f"因重名而重命名的文件: {renamed_files} 个")
    if skipped_files > 0:
        print(f"已正确分类而跳过的文件: {skipped_files} 个")
    if other_count > 0:
        print(f"无中文文件: {other_count} 个")
    print(f"删除了 {empty_folders_count} 个空闲文件夹")
    if chinese_folders:
        print(f"创建/更新了 {len(chinese_folders)} 个中文文件夹:")
        for folder, count in sorted(chinese_folders.items()):
            print(f"  {folder}: {count} 个文件")

def main():
    parser = argparse.ArgumentParser(description='按照文件名中的中文部分整理文件（深度扫描模式）')
    parser.add_argument('directory', nargs='?', default='~/Downloads',
                       help='要整理的目录路径 (默认: ~/Downloads)')
    
    args = parser.parse_args()
    
    # 直接执行深度整理操作
    organize_files_by_chinese(args.directory)

if __name__ == "__main__":
    main()