import os
import re

def generate_timeline(folder_path):
    timeline_html = """
    <div class="track-list"><!-- 时间轴开始 -->
    """
    
    # 定义文件夹的自定义排序顺序
    folder_order = ["Android", "ios", "Chrome扩展", "Mac", "Windows", "EFI", "其他"]
    
    # 获取所有文件夹和文件
    all_folders = []
    for root, dirs, files in os.walk(folder_path):
        # 忽略以 . 开头的文件夹
        if os.path.basename(root).startswith('.'):
            continue
        
        # 构建文件夹的相对路径
        relative_folder_path = os.path.relpath(root, folder_path)
        if relative_folder_path == '.':
            folder_title = "Root"
        else:
            folder_title = relative_folder_path
        
        # 获取文件夹中的文件
        folder_files = []
        for file in files:
            if file.startswith('.'):
                continue
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, folder_path)
            display_name = os.path.basename(relative_path)
            folder_files.append((relative_path, display_name))
        
        # 如果文件夹为空，则跳过
        if not folder_files:
            continue
        
        # 对文件按名称排序
        folder_files.sort(key=lambda x: x[1])
        
        # 添加文件夹和文件到列表
        all_folders.append((folder_title, folder_files))
    
    # 对文件夹按自定义顺序排序
    all_folders.sort(key=lambda x: folder_order.index(x[0]) if x[0] in folder_order else len(folder_order))
    
    # 生成HTML
    for folder_title, folder_files in all_folders:
        timeline_html += f"""
            <div class="category">
                <i class="fa-solid fa-compact-disc"></i>
                <span class="txt">{folder_title}</span>
            </div>
        """
        for relative_path, display_name in folder_files:
            timeline_html += f"""
            <div class="item">
                <span class="txt"><a href="./hema/{relative_path}">「{display_name}」</a></span>
            </div>
            """
    
    timeline_html += """
    </div><!-- 时间轴结束 -->
    """
    
    return timeline_html

# 使用示例
folder_path = os.path.abspath('./hema')  # 设置为hema文件夹的绝对路径
timeline_html = generate_timeline(folder_path)

# 检查hema.html文件是否存在
if not os.path.exists('hema.html'):
    print("错误：hema.html文件不存在")
else:
    # 读取hema.html文件内容
    with open('hema.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 使用正则表达式找到时间轴部分的起始和结束位置
    pattern = r'(<div class="track-list"><!-- 时间轴开始 -->(.*?<!-- 时间轴结束 -->))'
    match = re.search(pattern, html_content, re.DOTALL)

    if match:
        # 获取匹配到的时间轴部分
        original_timeline = match.group(1)
        
        # 替换时间轴部分
        new_html_content = html_content.replace(original_timeline, timeline_html)
        
        # 将修改后的内容写回hema.html文件
        with open('hema.html', 'w', encoding='utf-8') as f:
            f.write(new_html_content)
        
        print("时间轴HTML已更新到hema.html文件中")
    else:
        print("未找到时间轴部分，无法更新")