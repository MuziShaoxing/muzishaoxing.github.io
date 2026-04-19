#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
from datetime import datetime, timedelta

def main():
    # 获取下载文件夹路径
    download_dir = os.path.expanduser("~/Downloads")
    
    # 获取昨日日期并格式化为YYYY-MM-DD
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")
    
    # 创建目标文件夹路径
    target_dir = os.path.join(download_dir, date_str)
    
    # 如果目标文件夹不存在，则创建
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"创建文件夹: {target_dir}")
    else:
        print(f"文件夹已存在: {target_dir}")
    
    # 遍历下载文件夹中的所有文件和文件夹
    moved_count = 0
    for item in os.listdir(download_dir):
        item_path = os.path.join(download_dir, item)
        
        # 跳过目标文件夹本身和隐藏文件（以.开头的文件）
        if item == date_str or item.startswith('.'):
            continue
        
        # 处理目标路径中可能存在的重名文件
        target_item_path = os.path.join(target_dir, item)
        if os.path.exists(target_item_path):
            # 获取当前时间并格式化为HH_MM_SS
            time_str = datetime.now().strftime("%H_%M_%S")
            
            # 分离文件名和扩展名
            name, ext = os.path.splitext(item)
            
            # 构建新的文件名（添加时间戳）
            new_item_name = f"{name}_{time_str}{ext}"
            target_item_path = os.path.join(target_dir, new_item_name)
            
            print(f"重命名重复文件: {item} -> {new_item_name}")
        
        # 移动项目到目标文件夹
        try:
            shutil.move(item_path, target_item_path)
            print(f"移动: {item} -> {date_str}/")
            moved_count += 1
        except Exception as e:
            print(f"移动 {item} 时出错: {str(e)}")
    
    print(f"操作完成。共移动了 {moved_count} 个项目到 {date_str} 文件夹。")

if __name__ == "__main__":
    main()