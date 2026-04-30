#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re

def extract_sort_key(name):
    m = re.match(r'^(\d+)-', name)
    return int(m.group(1)) if m else 9999

def get_file_icon(filename):
    ext = os.path.splitext(filename)[1].lower()
    icons = {
        '.xlsx':'fa-file-excel','.xls':'fa-file-excel',
        '.docx':'fa-file-word','.doc':'fa-file-word',
        '.pdf':'fa-file-pdf','.zip':'fa-file-archive',
        '.rar':'fa-file-archive','.7z':'fa-file-archive',
        '.jpg':'fa-file-image','.jpeg':'fa-file-image',
        '.png':'fa-file-image','.gif':'fa-file-image',
        '.txt':'fa-file-alt','.html':'fa-file-code',
        '.htm':'fa-file-code','.css':'fa-file-code',
        '.js':'fa-file-code','.py':'fa-file-code',
        '.json':'fa-file-code','.mp4':'fa-file-video',
        '.mp3':'fa-file-audio',
    }
    return icons.get(ext, 'fa-file')

def has_favicon(dir_path):
    """检查目录中是否含有 .favicon.png 文件"""
    fav = os.path.join(dir_path, '.favicon.png')
    return os.path.isfile(fav)

def get_folder_icon(entry_name, base_dir):
    """返回文件夹图标数据：None 或 {'type':'image','value':'hema/.../.favicon.png'}"""
    if has_favicon(base_dir):
        return {'type': 'image', 'value': f'hema/{entry_name}/.favicon.png'}
    return None

def scan_directory_structure(base_path):
    result = {}
    if not os.path.exists(base_path):
        return result

    for entry in sorted(os.listdir(base_path)):
        entry_path = os.path.join(base_path, entry)
        if os.path.isdir(entry_path) and not entry.startswith('.'):
            folder_content = {
                'files': [],
                'folders': {},
                'icon': get_folder_icon(entry, entry_path)
            }
            # 扫描一级目录内的文件和子目录
            for item in os.listdir(entry_path):
                item_path = os.path.join(entry_path, item)
                if os.path.isfile(item_path):
                    # 忽略普通的隐藏文件，但保留 .favicon.png 已处理，不再重复添加
                    if item.startswith('.') and item != '.favicon.png':
                        continue
                    if item == '.favicon.png':
                        continue  # 图标文件不放入文件列表
                    folder_content['files'].append({
                        'name': item,
                        'icon': get_file_icon(item),
                        'path': f'hema/{entry}/{item}'
                    })
                elif os.path.isdir(item_path) and not item.startswith('.'):
                    sub_folder = {
                        'name': item,
                        'files': [],
                        'icon': get_folder_icon(f'{entry}/{item}', item_path)
                    }
                    for sub_file in os.listdir(item_path):
                        sub_file_path = os.path.join(item_path, sub_file)
                        if os.path.isfile(sub_file_path):
                            if sub_file.startswith('.') and sub_file != '.favicon.png':
                                continue
                            if sub_file == '.favicon.png':
                                continue
                            sub_folder['files'].append({
                                'name': sub_file,
                                'icon': get_file_icon(sub_file),
                                'path': f'hema/{entry}/{item}/{sub_file}'
                            })
                    folder_content['folders'][item] = sub_folder
            result[entry] = folder_content
    return result

def generate_data_js(folders):
    def format_file(f, indent=12):
        return f"{' '*indent}{{ name: '{f['name']}', icon: '{f['icon']}', path: '{f['path']}' }}"
    def format_icon(icon):
        if icon is None:
            return 'null'
        return f"{{ type: 'image', value: '{icon['value']}' }}"

    lines = ["const fileData = {"]
    sorted_names = sorted(folders.keys(), key=extract_sort_key)
    for name in sorted_names:
        folder = folders[name]
        lines.append(f"        '{name}': {{")
        # files
        lines.append(f"            files: [")
        for f in folder['files']:
            lines.append(format_file(f, 16) + ',')
        lines.append(f"            ],")
        # folders
        lines.append(f"            folders: {{")
        sub_names = sorted(folder['folders'].keys())
        if sub_names:
            for sub_name in sub_names:
                sub = folder['folders'][sub_name]
                lines.append(f"                '{sub_name}': {{")
                lines.append(f"                    name: '{sub['name']}',")
                lines.append(f"                    files: [")
                for f in sub['files']:
                    lines.append(format_file(f, 24) + ',')
                lines.append(f"                    ],")
                lines.append(f"                    icon: {format_icon(sub.get('icon'))}")
                lines.append(f"                }},")
        lines.append(f"            }},")
        lines.append(f"            icon: {format_icon(folder.get('icon'))}")
        lines.append(f"        }},")
    lines.append("    };")
    return '\n'.join(lines)

def update_html(html_path, folders):
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    backup = html_path + '.backup'
    with open(backup, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 已备份: {backup}")

    start_marker = 'const fileData = {'
    end_marker = '    };'
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("❌ 未找到 fileData 起点")
        return False
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        print("❌ 未找到 fileData 终点")
        return False
    end_idx += len(end_marker)

    new_data = generate_data_js(folders)
    content = content[:start_idx] + new_data + content[end_idx:]

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ fileData 已更新（含自定义图标信息）")
    return True

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    hema_dir = os.path.join(script_dir, 'hema')
    html_file = os.path.join(script_dir, 'hema.html')

    print("=" * 50)
    print("📁 时间轴更新工具 · 图标自动检测")
    print("=" * 50)

    if not os.path.exists(html_file):
        print(f"❌ {html_file} 不存在")
        return
    if not os.path.exists(hema_dir):
        os.makedirs(hema_dir, exist_ok=True)
        print(f"⚠️ 创建 hema 目录: {hema_dir}")

    folders = scan_directory_structure(hema_dir)
    print(f"\n📊 扫描结果:")
    for name in sorted(folders.keys(), key=extract_sort_key):
        f = folders[name]
        icon_status = "自定义图标" if f.get('icon') else "默认图标"
        sub_count = len(f['folders'])
        print(f"  📁 {name} [{icon_status}]: {len(f['files'])} 个文件, {sub_count} 个子文件夹")
        for sub_name in sorted(f['folders'].keys()):
            sub = f['folders'][sub_name]
            sub_icon = "自定义" if sub.get('icon') else "默认"
            print(f"       └─ {sub_name} [{sub_icon}]: {len(sub['files'])} 个文件")

    if update_html(html_file, folders):
        print(f"\n✅ 更新成功！现在可以在文件夹内放置 .favicon.png 自定义图标。")
    else:
        print("\n❌ 更新失败")

if __name__ == "__main__":
    main()