import os
from datetime import datetime

def generate_timeline(folder_path):
    timeline_items = []
    
    # 获取目标文件夹中的所有文件和文件夹
    items = os.listdir(folder_path)
    
    for item in items:
        # 构建文件/文件夹的相对路径
        relative_path = os.path.join("./Downloads", item)
        
        # 获取文件/文件夹的创建时间
        item_path = os.path.join(folder_path, item)
        ctime = os.path.getctime(item_path)
        # 将时间戳转换为日期字符串
        date_str = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d')
        
        # 构建时间轴项
        timeline_item = f"""
        <li>
            <i class="node-icon"><img src="./img/tb.svg"></i>
            <span class="time">{date_str}</span>
            <span class="txt">归档<a href="{relative_path}">「{item}」</a></span>
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

def generate_html(timeline_html):
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
	<head>
		<title>下载目录</title>   
		<meta charset="utf-8" name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
		<meta name="KEYWords" contect="少星博客,个人主页,个人引导页">
		<meta name="DEscription" contect="少星博客少星.icu的个人引导页">
		<meta name="Author" contect="少星">
		<meta name="Robots" contect= "all">
		<link rel="shortcut icon" href="./img/favicon.ico">
		<link rel="stylesheet"  href="./css/style.css">
	</head>
	<body>
		<div class="container"><!-- 主体开始 -->
			<div class="hander"><!-- 导航开始 -->
				<nav id="nav-menu">
					<a href="#" data-rel="home-me-section">&nbsp;&nbsp;&nbsp;&nbsp;👉🏻</a>&nbsp;&nbsp;
					<a href="#" data-rel="course-exp-section" class="active">少星de盘</a>
					<a href="#" data-rel="website-exp-section">👈🏻&nbsp;&nbsp;</a>
				</nav>
			</div><!-- 导航结束 -->
			<div class="content"><!-- 内容开始 -->
				<section class="home-me-section active-section"><!-- 首页开始 -->
				</section><!-- 首页结束 -->
				<section class="course-exp-section"><!-- 历程开始 -->
					<div class="main"><!-- 历程内容 -->
						<img src="./img/bgt.jpg" class="bgt" />
						<img src="./img/tx.png" class="ats" />
						<div class="box">
							<div id="boxs">
								{timeline_html}
							</div><!-- 时间轴结束 -->
						</div>
						<div style="color:#aaa;text-align:center;font-size:12px">
							注: 上下滑动查看历史进程
						</div>
					</div><!-- 历程内容结束 -->
				</section><!-- 历程结束 -->
			</div><!-- 内容结束 -->
		</div><!-- 主体结束 -->
		<div class="footer"><!-- 底部版权 -->
			<script type="text/javascript" src="https://www.iowen.cn/jitang/api/?format=js&charset=utf-8"></script>
			<div id="zha"><script>hitokoto()</script></div>
			<span id="sitetime"></span><!-- 运行时间 -->
			<br>©️ <a href="https://shaoxing.netlify.app">少星</a> 
			<br>
			<a href="https://beian.miit.gov.cn/" target="_blank">冀ICP备2022001845号-1</a>
		</div><!-- 版权结束 -->
		<!-- 音乐开始 -->
		<style type="text/css">
			audio{{z-index:5;position:absolute;bottom:0;opacity:.1;-webkit-transition:all 2s;-moz-transition:all 2s;-ms-transition:all 2s;-o-transition:all 2s;transition:all 2s}}
			audio:hover{{opacity:5}}
		</style>
		<audio id="backgroud-music" controls="controls" autoplay="true" loop="loop">
			<source src="./病变.m4a">
		</audio>
		<!--  音乐结束-->
		<script src="./js/index.js"></script><!-- 核心插件 -->
		<script src="./js/Sitetime.js"></script><!-- 运行时间 -->
	</body>
</html>
"""
    return html_content

# 使用示例
folder_path = os.path.abspath('./Downloads')  # 设置为Downloads文件夹的绝对路径
timeline_html = generate_timeline(folder_path)
html_content = generate_html(timeline_html)

# 将生成的HTML保存到文件
with open('Downloads.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("完整的HTML已生成并保存到Downloads.html文件中")
