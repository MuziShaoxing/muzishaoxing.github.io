#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
一键清理下载目录中超过30天的文件
支持Windows和macOS/Linux系统
"""

import os
import time
import sys
import argparse
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

def is_older_than_days(file_path, days=30):
    """检查文件是否超过指定天数"""
    if not os.path.exists(file_path):
        return False
    
    # 获取文件的修改时间
    file_mtime = os.path.getmtime(file_path)
    # 获取当前时间
    current_time = time.time()
    # 计算时间差（秒）
    time_diff = current_time - file_mtime
    # 转换为天数并比较
    return time_diff > (days * 24 * 60 * 60)

def get_file_size_str(size_bytes):
    """将字节大小转换为可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def clean_downloads(days=30, dry_run=False, verbose=True, exclude_dirs=None):
    """
    清理下载目录中的旧文件
    
    参数:
        days: 超过多少天的文件将被删除
        dry_run: 是否模拟运行（只显示要删除的文件，不实际删除）
        verbose: 是否显示详细信息
        exclude_dirs: 要排除的目录列表（相对路径）
    """
    downloads_path = get_download_path()
    
    if not os.path.exists(downloads_path):
        print(f"错误：下载目录不存在 - {downloads_path}")
        return
    
    print(f"下载目录: {downloads_path}")
    print(f"清理超过 {days} 天的文件")
    if dry_run:
        print("【模拟运行模式】不会实际删除文件\n")
    else:
        print("【实际运行模式】文件将被永久删除\n")
    
    # 统计信息
    total_deleted = 0
    total_size = 0
    skipped_dirs = 0
    
    # 遍历下载目录
    for root, dirs, files in os.walk(downloads_path):
        # 检查当前目录是否需要排除
        rel_path = os.path.relpath(root, downloads_path)
        if rel_path == '.':
            rel_path = ''
        
        if exclude_dirs and rel_path in exclude_dirs:
            if verbose:
                print(f"跳过排除目录: {rel_path}")
            skipped_dirs += 1
            # 清空dirs列表，防止继续遍历子目录
            dirs.clear()
            continue
        
        for file in files:
            file_path = os.path.join(root, file)
            
            try:
                if is_older_than_days(file_path, days):
                    file_size = os.path.getsize(file_path)
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if verbose:
                        print(f"发现旧文件: {file_path}")
                        print(f"  大小: {get_file_size_str(file_size)}")
                        print(f"  修改时间: {file_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    if not dry_run:
                        try:
                            os.remove(file_path)
                            total_deleted += 1
                            total_size += file_size
                            if verbose:
                                print("  ✓ 已删除\n")
                        except Exception as e:
                            print(f"  ✗ 删除失败: {e}\n")
                    else:
                        total_deleted += 1
                        total_size += file_size
                        if verbose:
                            print("  (模拟删除)\n")
                else:
                    if verbose and False:  # 设置为True可以显示所有文件
                        print(f"保留文件: {file_path}")
            except Exception as e:
                print(f"处理文件时出错 {file_path}: {e}")
    
    # 打印总结
    print("\n" + "="*50)
    print("清理完成总结")
    print("="*50)
    print(f"扫描目录: {downloads_path}")
    print(f"跳过目录数: {skipped_dirs}")
    print(f"处理文件总数: {total_deleted}")
    print(f"释放空间: {get_file_size_str(total_size)}")
    if dry_run:
        print("\n注意：这是模拟运行，没有实际删除任何文件")
        print("要实际删除文件，请运行脚本时不带 --dry-run 参数")

def main():
    parser = argparse.ArgumentParser(description='清理下载目录中超过指定天数的文件')
    parser.add_argument('--days', type=int, default=30,
                       help='文件超过多少天将被删除（默认：30）')
    parser.add_argument('--dry-run', action='store_true',
                       help='模拟运行，只显示要删除的文件，不实际删除')
    parser.add_argument('--quiet', action='store_true',
                       help='安静模式，只显示总结信息')
    parser.add_argument('--exclude', nargs='+', default=[],
                       help='要排除的子目录名称（相对路径，例如：important temp）')
    parser.add_argument('--path', type=str,
                       help='指定要清理的目录路径（默认：系统下载目录）')
    
    args = parser.parse_args()
    
    # 如果指定了自定义路径，覆盖下载目录
    if args.path:
        global get_download_path
        def custom_path():
            return args.path
        get_download_path = custom_path
    
    # 运行清理
    clean_downloads(
        days=args.days,
        dry_run=args.dry_run,
        verbose=not args.quiet,
        exclude_dirs=args.exclude
    )

if __name__ == "__main__":
    main()