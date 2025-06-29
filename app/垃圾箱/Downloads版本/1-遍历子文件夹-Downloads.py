import os
import time
from datetime import datetime
import re

def generate_timeline(folder_path):
    timeline_items = []
    
    # 递归获取文件夹下的所有文件（包括子文件夹中的文件）
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 忽略以 . 开头的文件
            if file.startswith('.'):
                continue
            
            # 构建文件的相对路径
            relative_path = os.path.relpath(os.path.join(root, file), folder_path)
            # 如果文件在子文件夹中，获取子文件夹名称
            if os.path.dirname(relative_path):
                folder_name = os.path.dirname(relative_path)
                display_name = f"{folder_name}-{file}"
            else:
                display_name = file
            
            # 获取文件的创建时间
            file_path = os.path.join(root, file)
            ctime = os.path.getctime(file_path)
            # 将时间戳转换为日期字符串
            date_str = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d')
            
            # 构建时间轴项
            timeline_item = f"""
            <li>
                <i class="node-icon"><img src="./img/tb.svg"></i>
                <span class="time">{date_str}</span>
                <span class="txt">归档<a href="./Downloads/{relative_path}">「{display_name}」</a></span>
            </li>
            """
            
            timeline_items.append(timeline_item)
    
    # 按日期排序（从早到晚）
    timeline_items.sort(key=lambda x: datetime.strptime(x.split('time">')[1].split('</span>')[0], '%Y-%m-%d'))
    
    # 构建完整的时间轴HTML
    timeline_html = """
    <div class="track-list"><!-- 时间轴开始 -->
        <ul>
    """
    timeline_html += '\n'.join(timeline_items)
    timeline_html += """
        </ul>
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
    pattern = r'(<div class="track-list"><!-- 时间轴开始 -->(.*?</ul>.*?<!-- 时间轴结束 -->))'
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
