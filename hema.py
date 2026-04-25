#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
from pathlib import Path
from datetime import datetime  # 新增：用于生成备份时间戳

def extract_sort_key(dir_name):
    """从文件夹名提取排序数字，如 '0-HeMa' -> 0, '12-测试' -> 12"""
    match = re.match(r'^(\d+)-', dir_name)
    return int(match.group(1)) if match else 9999

def get_display_name(dir_name):
    """隐藏前缀数字和横线，如 '0-HeMa' -> 'HeMa'"""
    return re.sub(r'^\d+-', '', dir_name)

def generate_folder_id(dir_name):
    """生成稳定的文件夹ID (保留原始名称)"""
    folder_id = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff-]', '-', dir_name)
    folder_id = re.sub(r'-+', '-', folder_id)
    folder_id = folder_id.strip('-')
    if not folder_id:
        folder_id = 'folder'
    return folder_id

def get_file_icon(filename):
    """根据文件扩展名返回图标类"""
    ext = os.path.splitext(filename)[1].lower()
    icons = {
        '.xlsx': 'fa-file-excel', '.xls': 'fa-file-excel',
        '.docx': 'fa-file-word', '.doc': 'fa-file-word',
        '.pdf': 'fa-file-pdf', '.zip': 'fa-file-archive',
        '.rar': 'fa-file-archive', '.7z': 'fa-file-archive',
        '.jpg': 'fa-file-image', '.jpeg': 'fa-file-image', 
        '.png': 'fa-file-image', '.gif': 'fa-file-image',
        '.txt': 'fa-file-alt', '.html': 'fa-file-code', 
        '.htm': 'fa-file-code', '.css': 'fa-file-code', 
        '.js': 'fa-file-code', '.py': 'fa-file-code', 
        '.json': 'fa-file-code', '.mp4': 'fa-file-video', 
        '.mp3': 'fa-file-audio',
    }
    return icons.get(ext, 'fa-file')

def scan_directory(base_path):
    """扫描hema文件夹，返回 (root_files, folders_dict)"""
    root_files, folders = [], {}
    if not os.path.exists(base_path):
        return root_files, folders
    
    for item in sorted(os.listdir(base_path)):
        item_path = os.path.join(base_path, item)
        if os.path.isfile(item_path) and not item.startswith('.'):
            root_files.append({
                'name': item, 
                'path': f'hema/{item}', 
                'icon': get_file_icon(item)
            })
        elif os.path.isdir(item_path) and not item.startswith('.'):
            folders[item] = []
            for f in sorted(os.listdir(item_path)):
                fp = os.path.join(item_path, f)
                if os.path.isfile(fp) and not f.startswith('.'):
                    folders[item].append({
                        'name': f, 
                        'path': f'hema/{item}/{f}', 
                        'icon': get_file_icon(f)
                    })
    return root_files, folders

def generate_menu_html(folders):
    """生成下拉菜单HTML，仅包含文件夹，按数字前缀排序，显示名隐藏前缀"""
    sorted_names = sorted(folders.keys(), key=extract_sort_key)
    lines = []
    lines.append('            <div class="dropdown-menu" id="dropdownMenu">')
    lines.append('                <ul>')
    
    for name in sorted_names:
        display = get_display_name(name)
        fid = generate_folder_id(name)
        lines.append(f'                    <li data-folder="{fid}" data-name="{name}">')
        # 注意：此处图标由JS动态生成，因此仅保留占位，实际图标由JS映射表处理
        lines.append(f'                        <i class="fa-solid fa-folder-open"></i> {display}')
        lines.append('                    </li>')
    
    lines.append('                </ul>')
    lines.append('            </div>')
    return '\n'.join(lines)

def generate_panels_html(folders):
    """生成文件面板容器，仅包含文件夹对应的面板"""
    sorted_names = sorted(folders.keys(), key=extract_sort_key)
    lines = []
    for name in sorted_names:
        fid = generate_folder_id(name)
        lines.append(f'        <div class="file-panel" id="panel-{fid}" style="display:none;"></div>')
    return '\n'.join(lines)

def generate_data_js(root_files, folders):
    """生成 fileData JavaScript 对象，完全移除 root 键"""
    def format_file(f): 
        return f"{{ name: '{f['name']}', icon: '{f['icon']}', path: '{f['path']}' }}"
    
    lines = ["const fileData = {"]
    
    sorted_names = sorted(folders.keys(), key=extract_sort_key)
    for name in sorted_names:
        fid = generate_folder_id(name)
        files = folders[name]
        lines.append(f"        '{fid}': [")
        for f in files:
            lines.append(f"            {format_file(f)},")
        lines.append("        ],")
    
    lines.append("    };")
    return '\n'.join(lines)

def update_html(html_path, root_files, folders):
    """更新HTML文件，保留图标映射逻辑，备份到 backups/ 并添加时间戳"""
    with open(html_path, 'r', encoding='utf-8') as f: 
        content = f.read()
    
    # 备份：存入当前目录下的 backups 文件夹，文件名加上时间戳
    backup_dir = os.path.join(os.path.dirname(html_path), 'app/.backups')
    os.makedirs(backup_dir, exist_ok=True)  # 确保目录存在
    base_name = os.path.basename(html_path)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{base_name}_{timestamp}.backup"
    backup_path = os.path.join(backup_dir, backup_name)

    with open(backup_path, 'w', encoding='utf-8') as f: 
        f.write(content)
    print(f"✅ 已备份: {backup_path}")
    
    # 1. 更新下拉菜单
    menu_start = '<!-- ========== 脚本更新区域：下拉菜单 ========== -->'
    menu_end = '<!-- ========== 脚本更新区域结束 ========== -->'
    
    start_idx = content.find(menu_start)
    end_idx = content.find(menu_end, start_idx + len(menu_start))
    
    if start_idx != -1 and end_idx != -1:
        menu_html = generate_menu_html(folders)
        content = content[:start_idx + len(menu_start)] + '\n' + menu_html + '\n            ' + content[end_idx:]
        print("✅ 下拉菜单已更新")
    
    # 2. 更新文件面板
    panels_start = '<!-- ========== 脚本更新区域：文件面板 ========== -->'
    panels_end = '<!-- ========== 脚本更新区域结束 ========== -->'
    
    start_idx = content.find(panels_start)
    end_idx = content.find(panels_end, start_idx + len(panels_start))
    
    if start_idx != -1 and end_idx != -1:
        panels_html = generate_panels_html(folders)
        content = content[:start_idx + len(panels_start)] + '\n' + panels_html + '\n        ' + content[end_idx:]
        print("✅ 文件面板已更新")
    
    # 3. 更新数据对象
    data_pattern = r'(const fileData = \{)[\s\S]*?(\n    \};)'
    data_js = generate_data_js(root_files, folders)
    
    if re.search(data_pattern, content):
        content = re.sub(data_pattern, data_js, content)
        print("✅ fileData已更新")
    
    with open(html_path, 'w', encoding='utf-8') as f: 
        f.write(content)
    
    return True

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(script_dir, 'hema')
    html_file = os.path.join(script_dir, 'hema.html')
    
    print("=" * 50)
    print("📁 时间轴更新工具 v9.0 (图标映射完整版)")
    print("=" * 50)
    print(f"📂 工作目录: {script_dir}")
    print(f"📁 扫描文件夹: {folder_path}")
    print(f"📄 目标文件: {html_file}")
    print("=" * 50)
    
    if not os.path.exists(html_file):
        print(f"❌ {html_file} 不存在")
        return
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        print(f"⚠️ 创建目录: {folder_path}")
    
    root_files, folders = scan_directory(folder_path)
    
    print(f"\n📊 扫描结果:")
    if root_files:
        print(f"  📁 Root文件: {len(root_files)} 个 (将在界面中隐藏)")
    else:
        print(f"  📁 Root: 无文件")
    
    sorted_names = sorted(folders.keys(), key=extract_sort_key)
    for name in sorted_names:
        fid = generate_folder_id(name)
        display = get_display_name(name)
        print(f"  📂 {name} (显示为「{display}」, ID: {fid}): {len(folders[name])} 个文件")
    
    if update_html(html_file, root_files, folders):
        print(f"\n✅ 更新成功！图标映射已保留。")
        # 提示备份位置
        backup_dir = os.path.join(os.path.dirname(html_file), 'app/.backups')
        print(f"💾 备份文件保存在: {backup_dir}")
    else:
        print("\n❌ 更新失败")

if __name__ == "__main__":
    main()