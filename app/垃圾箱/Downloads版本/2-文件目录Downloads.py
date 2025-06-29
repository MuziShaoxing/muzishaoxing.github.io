import os
import re

def generate_timeline(folder_path):
    timeline_html = """
    <div class="track-list"><!-- 时间轴开始 -->
    """
    
    # 递归获取文件夹下的所有文件（包括子文件夹中的文件）
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
        
        # 添加文件夹标题（作为分栏标题）
        timeline_html += f"""
            <i class="folder-icon"></i>
            <i class="node-icon"><img src="./img/tb.svg"></i>
            <span class="txt">{folder_title}</span><br>
        """
        
        # 遍历文件夹中的文件
        for file in files:
            # 忽略以 . 开头的文件
            if file.startswith('.'):
                continue
            
            # 构建文件的相对路径
            relative_path = os.path.relpath(os.path.join(root, file), folder_path)
            display_name = os.path.basename(relative_path)
            
            # 构建文件项（作为分栏内的内容）
            timeline_html += f"""
            &emsp;&emsp;<span class="txt"><a href="./Downloads/{relative_path}">「{display_name}」</a></span><br>
            """
    
    timeline_html += """
    </div><!-- 时间轴结束 -->
    """
    
    return timeline_html

# 使用示例
folder_path = os.path.abspath('./Downloads')  # 设置为Downloads文件夹的绝对路径
timeline_html = generate_timeline(folder_path)

# 检查index.html文件是否存在
if not os.path.exists('index.html'):
    print("错误：index.html文件不存在")
else:
    # 读取index.html文件内容
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 使用正则表达式找到时间轴部分的起始和结束位置
    pattern = r'(<div class="track-list"><!-- 时间轴开始 -->(.*?<!-- 时间轴结束 -->))'
    match = re.search(pattern, html_content, re.DOTALL)

    if match:
        # 获取匹配到的时间轴部分
        original_timeline = match.group(1)
        
        # 替换时间轴部分
        new_html_content = html_content.replace(original_timeline, timeline_html)
        
        # 将修改后的内容写回index.html文件
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(new_html_content)
        
        print("时间轴HTML已更新到index.html文件中")
    else:
        print("未找到时间轴部分，无法更新")