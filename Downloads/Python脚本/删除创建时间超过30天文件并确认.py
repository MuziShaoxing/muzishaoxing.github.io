#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
一键清理下载目录中超过30天的文件（基于创建时间）
支持Windows和macOS/Linux系统
新增功能：先显示列表，再确认删除
"""

import os
import time
import sys
import argparse
import platform
from datetime import datetime, timedelta

def get_download_path():
    """获取当前系统的下载目录路径"""
    if sys.platform == 'win32':
        # Windows系统
        try:
            import winreg
            sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                downloads_path = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
                return downloads_path
        except:
            # 如果注册表方式失败，使用默认用户目录下的Downloads
            return os.path.join(os.path.expanduser('~'), 'Downloads')
    else:
        # macOS/Linux系统
        return os.path.join(os.path.expanduser('~'), 'Downloads')

def get_file_creation_time(file_path):
    """
    获取文件的创建时间
    返回时间戳（秒）
    """
    try:
        if sys.platform == 'win32':
            # Windows系统：使用创建时间
            return os.path.getctime(file_path)
        else:
            # macOS/Linux系统
            if platform.system() == 'Darwin':  # macOS
                # macOS上使用st_birthtime获取创建时间
                stat = os.stat(file_path)
                return stat.st_birthtime
            else:  # Linux
                # Linux通常没有创建时间，回退到修改时间
                return os.path.getmtime(file_path)
    except Exception as e:
        print(f"获取创建时间失败 {file_path}: {e}")
        # 如果获取创建时间失败，回退到修改时间
        return os.path.getmtime(file_path)

def is_older_than_days_by_ctime(file_path, days=30):
    """检查文件是否超过指定天数（基于创建时间）"""
    if not os.path.exists(file_path):
        return False
    
    # 获取文件的创建时间
    file_ctime = get_file_creation_time(file_path)
    # 获取当前时间
    current_time = time.time()
    # 计算时间差（秒）
    time_diff = current_time - file_ctime
    # 转换为天数并比较
    return time_diff > (days * 24 * 60 * 60)

def get_file_size_str(size_bytes):
    """将字节大小转换为可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_time_type_str():
    """返回当前使用的时间类型说明"""
    if sys.platform == 'win32':
        return "创建时间 (Creation Time)"
    elif platform.system() == 'Darwin':
        return "创建时间 (Birth Time)"
    else:
        return "修改时间 (Modification Time，Linux回退)"

def scan_files(downloads_path, days=30, exclude_dirs=None):
    """
    扫描目录，返回要删除的文件列表
    
    返回:
        list of tuples: [(file_path, file_size, creation_time), ...]
    """
    files_to_delete = []
    skipped_dirs = 0
    
    print("正在扫描文件...")
    
    for root, dirs, files in os.walk(downloads_path):
        # 检查当前目录是否需要排除
        rel_path = os.path.relpath(root, downloads_path)
        if rel_path == '.':
            rel_path = ''
        
        if exclude_dirs and rel_path in exclude_dirs:
            skipped_dirs += 1
            # 清空dirs列表，防止继续遍历子目录
            dirs.clear()
            continue
        
        for file in files:
            file_path = os.path.join(root, file)
            
            try:
                if is_older_than_days_by_ctime(file_path, days):
                    file_size = os.path.getsize(file_path)
                    file_ctime = get_file_creation_time(file_path)
                    files_to_delete.append((file_path, file_size, file_ctime))
            except Exception as e:
                print(f"扫描文件时出错 {file_path}: {e}")
    
    return files_to_delete, skipped_dirs

def display_files_to_delete(files_to_delete):
    """显示要删除的文件列表"""
    if not files_to_delete:
        print("\n没有找到需要清理的文件。")
        return False
    
    print("\n" + "="*80)
    print("以下文件将被删除：")
    print("="*80)
    
    # 按目录分组显示
    files_by_dir = {}
    for file_path, file_size, file_ctime in files_to_delete:
        dir_name = os.path.dirname(file_path)
        if dir_name not in files_by_dir:
            files_by_dir[dir_name] = []
        files_by_dir[dir_name].append((file_path, file_size, file_ctime))
    
    total_size = 0
    total_files = 0
    
    # 显示每个目录的文件
    for dir_name, files in sorted(files_by_dir.items()):
        print(f"\n📁 {dir_name}")
        print("-" * 60)
        
        dir_size = 0
        for file_path, file_size, file_ctime in sorted(files, key=lambda x: x[2]):  # 按时间排序
            file_name = os.path.basename(file_path)
            time_str = datetime.fromtimestamp(file_ctime).strftime('%Y-%m-%d %H:%M:%S')
            size_str = get_file_size_str(file_size)
            print(f"  📄 {file_name}")
            print(f"    创建时间: {time_str} | 大小: {size_str}")
            dir_size += file_size
        
        print(f"  目录小计: {len(files)} 个文件, 总计: {get_file_size_str(dir_size)}")
        total_size += dir_size
        total_files += len(files)
    
    print("\n" + "="*80)
    print(f"总计: {total_files} 个文件, 释放空间: {get_file_size_str(total_size)}")
    print("="*80)
    
    return True

def ask_for_confirmation():
    """询问用户是否确认删除"""
    while True:
        response = input("\n是否确认删除以上文件？(yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("请输入 'yes' 或 'no'")

def delete_files(files_to_delete, verbose=True):
    """实际删除文件"""
    if not files_to_delete:
        return 0, 0
    
    total_deleted = 0
    total_size = 0
    failed_files = []
    
    print("\n正在删除文件...")
    
    for file_path, file_size, _ in files_to_delete:
        try:
            os.remove(file_path)
            total_deleted += 1
            total_size += file_size
            if verbose:
                print(f"✓ 已删除: {file_path}")
        except Exception as e:
            failed_files.append((file_path, str(e)))
            if verbose:
                print(f"✗ 删除失败: {file_path} - {e}")
    
    # 显示失败的文件
    if failed_files and verbose:
        print("\n删除失败的文件：")
        for file_path, error in failed_files:
            print(f"  {file_path}: {error}")
    
    return total_deleted, total_size

def clean_downloads(days=30, auto_yes=False, verbose=True, exclude_dirs=None):
    """
    清理下载目录中的旧文件（基于创建时间）
    
    参数:
        days: 超过多少天的文件将被删除
        auto_yes: 自动确认删除（不询问）
        verbose: 是否显示详细信息
        exclude_dirs: 要排除的目录列表（相对路径）
    """
    downloads_path = get_download_path()
    
    if not os.path.exists(downloads_path):
        print(f"错误：下载目录不存在 - {downloads_path}")
        return
    
    time_type = get_time_type_str()
    
    print(f"下载目录: {downloads_path}")
    print(f"清理超过 {days} 天的文件")
    print(f"时间依据: {time_type}")
    
    # 第一步：扫描文件
    files_to_delete, skipped_dirs = scan_files(downloads_path, days, exclude_dirs)
    
    if not files_to_delete:
        print("\n没有找到需要清理的文件。")
        return
    
    # 第二步：显示文件列表
    if not display_files_to_delete(files_to_delete):
        return
    
    print(f"\n跳过目录数: {skipped_dirs}")
    
    # 第三步：询问确认
    if not auto_yes:
        if not ask_for_confirmation():
            print("\n操作已取消，没有删除任何文件。")
            return
    else:
        print("\n自动确认模式，继续删除...")
    
    # 第四步：执行删除
    total_deleted, total_size = delete_files(files_to_delete, verbose)
    
    # 第五步：显示总结
    print("\n" + "="*50)
    print("清理完成总结")
    print("="*50)
    print(f"扫描目录: {downloads_path}")
    print(f"时间依据: {time_type}")
    print(f"跳过目录数: {skipped_dirs}")
    print(f"成功删除: {total_deleted} 个文件")
    print(f"释放空间: {get_file_size_str(total_size)}")
    
    if total_deleted < len(files_to_delete):
        print(f"删除失败: {len(files_to_delete) - total_deleted} 个文件")

def test_file_times(file_path):
    """测试文件的各个时间属性"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    stat = os.stat(file_path)
    
    print(f"\n文件: {file_path}")
    print("-" * 40)
    print(f"修改时间 (mtime): {datetime.fromtimestamp(stat.st_mtime)}")
    print(f"访问时间 (atime): {datetime.fromtimestamp(stat.st_atime)}")
    
    if sys.platform == 'win32':
        print(f"创建时间 (ctime): {datetime.fromtimestamp(stat.st_ctime)}")
    elif platform.system() == 'Darwin':
        print(f"创建时间 (birthtime): {datetime.fromtimestamp(stat.st_birthtime)}")
    else:
        print(f"状态改变时间 (ctime): {datetime.fromtimestamp(stat.st_ctime)}")
        print("注意：Linux的ctime不是创建时间，而是inode修改时间")

def main():
    parser = argparse.ArgumentParser(description='清理下载目录中超过指定天数的文件（基于创建时间）')
    parser.add_argument('--days', type=int, default=30,
                       help='文件超过多少天将被删除（默认：30）')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='自动确认删除（不询问）')
    parser.add_argument('--quiet', action='store_true',
                       help='安静模式，减少输出信息')
    parser.add_argument('--exclude', nargs='+', default=[],
                       help='要排除的子目录名称（相对路径，例如：important temp）')
    parser.add_argument('--path', type=str,
                       help='指定要清理的目录路径（默认：系统下载目录）')
    parser.add_argument('--test', type=str,
                       help='测试指定文件的时间属性')
    
    args = parser.parse_args()
    
    # 如果指定了测试模式
    if args.test:
        test_file_times(args.test)
        return
    
    # 如果指定了自定义路径，覆盖下载目录
    if args.path:
        global get_download_path
        def custom_path():
            return args.path
        get_download_path = custom_path
    
    # 运行清理
    clean_downloads(
        days=args.days,
        auto_yes=args.yes,
        verbose=not args.quiet,
        exclude_dirs=args.exclude
    )

if __name__ == "__main__":
    main()