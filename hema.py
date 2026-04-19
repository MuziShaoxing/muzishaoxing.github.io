import os
import re
from pathlib import Path

def generate_enhanced_timeline(folder_path):
    """
    生成增强版的时间轴HTML，保持分栏导航结构
    """
    
    # 获取所有文件夹和文件的层级结构
    def get_directory_structure(base_path):
        structure = {}
        root_files = []
        
        if not os.path.exists(base_path):
            return root_files, structure
            
        for root, dirs, files in os.walk(base_path):
            # 过滤隐藏文件
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            files = [f for f in files if not f.startswith('.')]
            
            rel_path = os.path.relpath(root, base_path)
            
            if rel_path == '.':
                # 根目录文件
                root_files = [(f, os.path.join('hema', f)) for f in sorted(files)]
            else:
                # 子目录
                if rel_path not in structure:
                    structure[rel_path] = []
                for file in sorted(files):
                    structure[rel_path].append((file, os.path.join('hema', rel_path.replace('\\', '/'), file)))
        
        return root_files, structure
    
    root_files, dir_structure = get_directory_structure(folder_path)
    
    print(f"📊 扫描结果: Root文件 {len(root_files)} 个, 子目录 {len(dir_structure)} 个")
    
    # 生成HTML - 使用与手动修复后相同的结构
    timeline_html = '''<!-- 时间轴开始 -->
        
            <!-- 分栏导航标签 -->
            <div class="folder-tabs">
                <button class="folder-tab active" data-folder="root">
                    <i class="fa-solid fa-folder"></i> Root
                </button>
'''
    
    # 为每个子目录创建标签 - 使用有意义的英文ID
    for dir_name in sorted(dir_structure.keys()):
        display_name = dir_name.replace('\\', '/').split('/')[-1]
        # 生成安全的英文ID
        folder_id = re.sub(r'[^a-zA-Z0-9]', '-', dir_name)
        # 如果ID只包含连字符，使用默认名称
        if not folder_id.strip('-'):
            folder_id = 'folder-' + str(hash(dir_name) % 1000)
        
        timeline_html += f'''
                <button class="folder-tab" data-folder="{folder_id}">
                    <i class="fa-solid fa-folder-open"></i> {display_name}
                </button>'''
    
    timeline_html += '''
            </div>
        
            <!-- Root 文件夹内容 -->
            <div class="folder-content active" id="folder-root">'''
    
    if root_files:
        for filename, filepath in root_files:
            # 检查是否是HTML文件
            is_html = filename.lower().endswith('.html')
            target_attr = 'target="_blank" rel="noopener noreferrer"' if is_html else ''
            
            timeline_html += f'''
            
            <div class="item">
                <span class="txt"><a href="{filepath}" {target_attr}>「{filename}」</a></span>
            </div>'''
    else:
        timeline_html += '''
            
            <div class="item">
                <span class="txt" style="color: #999; font-style: italic;">暂无文件</span>
            </div>'''
    
    timeline_html += '''
            </div>'''
    
    # 为每个子目录创建内容区域
    for dir_name, files in sorted(dir_structure.items()):
        folder_id = re.sub(r'[^a-zA-Z0-9]', '-', dir_name)
        if not folder_id.strip('-'):
            folder_id = 'folder-' + str(hash(dir_name) % 1000)
        
        timeline_html += f'''
        
            <!-- {dir_name} 文件夹内容 -->
            <div class="folder-content" id="folder-{folder_id}">'''
        
        if files:
            for filename, filepath in files:
                is_html = filename.lower().endswith('.html')
                target_attr = 'target="_blank" rel="noopener noreferrer"' if is_html else ''
                
                timeline_html += f'''
            
            <div class="item">
                <span class="txt"><a href="{filepath}" {target_attr}>「{filename}」</a></span>
            </div>'''
        else:
            timeline_html += '''
            
            <div class="item">
                <span class="txt" style="color: #999; font-style: italic;">暂无文件</span>
            </div>'''
        
        timeline_html += '''
            </div>'''
    
    timeline_html += '''
    
    </div><!-- 时间轴结束 -->'''
    
    return timeline_html

def update_html_file(html_path, timeline_html):
    """精确替换时间轴内容，保留样式和脚本"""
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    backup_path = html_path + '.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 已备份到: {backup_path}")
    
    # 查找时间轴标记 - 使用与手动修复后一致的标记
    start_marker = '<!-- 时间轴开始 -->'
    end_marker = '</div><!-- 时间轴结束 -->'
    
    start_pos = content.find(start_marker)
    end_pos = content.find(end_marker)
    
    if start_pos == -1:
        print("尝试查找 <div class=\"track-list\"><!-- 时间轴开始 -->...")
        start_pos = content.find('<div class="track-list"><!-- 时间轴开始 -->')
        if start_pos != -1:
            start_marker = '<div class="track-list"><!-- 时间轴开始 -->'
    
    if start_pos == -1:
        print("❌ 无法找到时间轴开始位置")
        return False
    
    if end_pos == -1:
        print("❌ 无法找到时间轴结束位置")
        return False
    
    # 计算实际的结束位置
    end_pos = end_pos + len(end_marker)
    
    print(f"✅ 时间轴位置: {start_pos} - {end_pos}")
    
    # 检查并提取原有的样式和脚本
    style_pattern = r'<style>.*?\.folder-tabs.*?</style>'
    script_pattern = r'<script>.*?分栏导航.*?</script>'
    
    existing_styles = ''
    existing_scripts = ''
    
    style_match = re.search(style_pattern, content, re.DOTALL)
    if style_match:
        existing_styles = style_match.group(0)
        print("✅ 找到现有样式")
    
    script_match = re.search(script_pattern, content, re.DOTALL)
    if script_match:
        existing_scripts = script_match.group(0)
        print("✅ 找到现有脚本")
    
    # 替换时间轴内容
    new_content = content[:start_pos] + timeline_html + content[end_pos:]
    
    # 如果没有现有样式，添加默认样式
    if not existing_styles:
        default_styles = '''
    <style>
        /* 分栏导航样式 */
        .folder-tabs {
            display: flex;
            gap: 8px;
            margin: 20px 0 15px 0;
            padding: 0 5px;
            border-bottom: 2px solid #e0e0e0;
            flex-wrap: wrap;
        }
        
        .folder-tab {
            padding: 10px 20px;
            background: #f5f5f5;
            border: 1px solid #ddd;
            color: #333;
            font-size: 14px;
            cursor: pointer;
            border-radius: 8px 8px 0 0;
            transition: all 0.3s ease;
            font-weight: 500;
            position: relative;
            margin-bottom: -1px;
        }
        
        .folder-tab:hover {
            background: #e8e8e8;
            color: #000;
            border-color: #bbb;
        }
        
        .folder-tab.active {
            color: #2196F3;
            background: #fff;
            border-bottom: 2px solid #2196F3;
            border-left-color: #ddd;
            border-right-color: #ddd;
            border-top-color: #ddd;
        }
        
        .folder-tab i {
            margin-right: 6px;
            font-size: 14px;
        }
        
        /* 内容区域 */
        .folder-content {
            display: none;
        }
        
        .folder-content.active {
            display: block;
        }
        
        /* 内容切换动画 */
        .folder-content .item {
            animation: tabFadeIn 0.3s ease;
        }
        
        @keyframes tabFadeIn {
            from { 
                opacity: 0; 
                transform: translateY(-5px); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0); 
            }
        }
        
        /* HTML文件标识 */
        .item a[href$=".html"]::after {
            content: " 🌐";
            margin-left: 5px;
            font-size: 12px;
            opacity: 0.7;
        }
    </style>
'''
        new_content = new_content.replace('</head>', default_styles + '\n</head>')
        print("✅ 已添加默认样式")
    
    # 如果没有现有脚本，添加默认脚本
    if not existing_scripts:
        default_script = '''
    <script>
        (function() {
            console.log('🚀 分栏导航初始化');
            
            function initTabs() {
                const tabs = document.querySelectorAll('.folder-tab');
                const contents = document.querySelectorAll('.folder-content');
                
                console.log('标签数量:', tabs.length);
                console.log('内容区数量:', contents.length);
                
                if (tabs.length === 0) {
                    setTimeout(initTabs, 100);
                    return;
                }
                
                // 显示所有标签
                tabs.forEach((tab, i) => {
                    console.log(`标签${i}:`, tab.textContent.trim(), 'data-folder:', tab.getAttribute('data-folder'));
                });
                
                // 绑定点击事件
                tabs.forEach(tab => {
                    tab.addEventListener('click', function(e) {
                        e.preventDefault();
                        const folderId = this.getAttribute('data-folder');
                        console.log('切换到:', folderId);
                        
                        // 切换class
                        tabs.forEach(t => t.classList.remove('active'));
                        this.classList.add('active');
                        
                        // 切换内容
                        contents.forEach(c => c.classList.remove('active'));
                        const target = document.getElementById('folder-' + folderId);
                        if (target) {
                            target.classList.add('active');
                            console.log('✅ 显示内容:', folderId);
                        } else {
                            console.error('❌ 找不到内容区:', 'folder-' + folderId);
                        }
                        
                        // 修复HTML链接
                        setTimeout(fixHtmlLinks, 50);
                    });
                });
                
                // 确保默认显示正确的内容
                const activeTab = document.querySelector('.folder-tab.active');
                if (activeTab) {
                    const folderId = activeTab.getAttribute('data-folder');
                    const activeContent = document.getElementById('folder-' + folderId);
                    if (activeContent) {
                        activeContent.classList.add('active');
                    }
                }
            }
            
            function fixHtmlLinks() {
                document.querySelectorAll('.folder-content.active .item a[href$=".html"]').forEach(link => {
                    link.setAttribute('target', '_blank');
                    link.setAttribute('rel', 'noopener noreferrer');
                });
            }
            
            // 初始化
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initTabs);
            } else {
                initTabs();
            }
            
            // 全局拦截HTML下载
            document.addEventListener('click', function(e) {
                const target = e.target.closest('a');
                if (target && target.href && target.href.toLowerCase().endsWith('.html')) {
                    target.setAttribute('target', '_blank');
                    target.setAttribute('rel', 'noopener noreferrer');
                    target.removeAttribute('download');
                }
            });
        })();
    </script>
'''
        new_content = new_content.replace('</body>', default_script + '\n</body>')
        print("✅ 已添加默认脚本")
    
    # 写回文件
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(script_dir, 'hema')
    html_file = os.path.join(script_dir, 'hema.html')
    
    print("=" * 60)
    print("分栏导航更新工具")
    print("=" * 60)
    
    if not os.path.exists(html_file):
        print(f"❌ {html_file} 不存在")
        return
    
    if not os.path.exists(folder_path):
        print(f"⚠️ 创建目录: {folder_path}")
        os.makedirs(folder_path, exist_ok=True)
    
    print("\n🔍 扫描文件...")
    timeline_html = generate_enhanced_timeline(folder_path)
    
    print("\n✏️ 更新HTML...")
    if update_html_file(html_file, timeline_html):
        print("\n✅ 更新成功！")
        print("\n特点：")
        print("1. 保留了分栏导航结构")
        print("2. 自动生成安全的英文ID")
        print("3. 保留原有样式和脚本")
        print(f"\n备份文件: {html_file}.backup")
    else:
        print("\n❌ 更新失败")
        print(f"可以从备份恢复: {html_file}.backup")

if __name__ == "__main__":
    main()