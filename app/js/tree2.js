document.addEventListener('DOMContentLoaded', function() {
    // DOM元素获取
    const selectFolderBtn = document.getElementById('selectFolderBtn');
    const generateBtn = document.getElementById('generateBtn');
    const includeHiddenCheckbox = document.getElementById('includeHidden');
    const treePreview = document.getElementById('treePreview');
    const emptyState = document.getElementById('emptyState');
    const statusDiv = document.getElementById('status');
    const loader = document.getElementById('loader');
    const dropArea = document.getElementById('dropArea');

    // 状态变量
    let selectedFolderHandle = null;
    let treeStructure = null;

    // 初始化拖拽功能
    function initDragAndDrop() {
        // 阻止默认事件
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        // 高亮拖拽区域
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight, false);
        });

        function highlight() {
            dropArea.classList.add('drag-over');
        }

        function unhighlight() {
            dropArea.classList.remove('drag-over');
        }

        // 处理拖放
        dropArea.addEventListener('drop', handleDrop, false);

        async function handleDrop(e) {
            const dt = e.dataTransfer;
            const items = dt.items;

            if (items && items.length > 0) {
                try {
                    showLoading(true);
                    statusDiv.textContent = "处理拖放的文件夹...";
                    statusDiv.className = "status";

                    if (!('getAsFileSystemHandle' in items[0])) {
                        throw new Error('您的浏览器不支持拖放文件夹功能，请使用最新版Chrome或Edge');
                    }

                    const handle = await items[0].getAsFileSystemHandle();
                    if (handle.kind !== 'directory') {
                        throw new Error('请拖放文件夹而非文件');
                    }

                    selectedFolderHandle = handle;
                    statusDiv.textContent = "正在生成目录树...";
                    treeStructure = await generateDirectoryTree(selectedFolderHandle);
                    displayTreePreview(treeStructure);
                    emptyState.style.display = "none";
                    generateBtn.disabled = false;

                    statusDiv.textContent = `已选择: ${selectedFolderHandle.name}`;
                    statusDiv.className = "status success";
                } catch (error) {
                    console.error("拖放错误:", error);
                    statusDiv.textContent = `错误: ${error.message}`;
                    statusDiv.className = "status error";
                } finally {
                    showLoading(false);
                }
            }
        }
    }

    // 选择文件夹按钮点击事件
    selectFolderBtn.addEventListener('click', async function() {
        try {
            showLoading(true);
            statusDiv.textContent = "正在访问文件夹...";
            statusDiv.className = "status";

            if (!('showDirectoryPicker' in window)) {
                throw new Error('您的浏览器不支持文件夹选择功能，请使用最新版Chrome或Edge');
            }

            selectedFolderHandle = await window.showDirectoryPicker();
            statusDiv.textContent = "正在生成目录树...";
            treeStructure = await generateDirectoryTree(selectedFolderHandle);
            displayTreePreview(treeStructure);
            emptyState.style.display = "none";
            generateBtn.disabled = false;

            statusDiv.textContent = `已选择: ${selectedFolderHandle.name}`;
            statusDiv.className = "status success";
        } catch (error) {
            console.error("选择文件夹错误:", error);
            statusDiv.textContent = `错误: ${error.message}`;
            statusDiv.className = "status error";
        } finally {
            showLoading(false);
        }
    });

    // 生成HTML按钮点击事件
    generateBtn.addEventListener('click', async function() {
        if (!selectedFolderHandle || !treeStructure) {
            statusDiv.textContent = "请先选择文件夹并生成目录树";
            statusDiv.className = "status error";
            return;
        }

        try {
            showLoading(true);
            statusDiv.textContent = "正在生成HTML文件...";
            statusDiv.className = "status";

            const htmlContent = createHTMLFromTree(treeStructure, selectedFolderHandle.name);
            downloadHTML(htmlContent, `${selectedFolderHandle.name}_目录树.html`);

            statusDiv.textContent = "HTML文件生成成功!";
            statusDiv.className = "status success";
        } catch (error) {
            console.error("生成HTML错误:", error);
            statusDiv.textContent = `生成失败: ${error.message}`;
            statusDiv.className = "status error";
        } finally {
            showLoading(false);
        }
    });

    // 生成目录树结构
    async function generateDirectoryTree(directoryHandle, path = '', level = 0) {
        const tree = {
            name: directoryHandle.name,
            path: path,
            type: 'directory',
            level: level,
            children: []
        };

        for await (const entry of directoryHandle.values()) {
            if (!includeHiddenCheckbox.checked && entry.name.startsWith('.')) {
                continue;
            }

            try {
                if (entry.kind === 'directory') {
                    const childTree = await generateDirectoryTree(
                        entry,
                        path ? `${path}/${entry.name}` : entry.name,
                        level + 1
                    );
                    tree.children.push(childTree);
                } else if (entry.kind === 'file') {
                    tree.children.push({
                        name: entry.name,
                        path: path ? `${path}/${entry.name}` : entry.name,
                        type: 'file',
                        level: level + 1
                    });
                }
            } catch (e) {
                console.warn(`无法访问 ${entry.name}:`, e);
            }
        }

        tree.children.sort((a, b) => {
            if (a.type === 'directory' && b.type !== 'directory') return 1;
            if (a.type !== 'directory' && b.type === 'directory') return -1;
            return a.name.localeCompare(b.name);
        });

        return tree;
    }

    // 显示目录树预览
    function displayTreePreview(tree) {
        let previewText = '';

        function buildPreview(node, prefix = '') {
            const isLast = node === node.parent?.children?.slice(-1)[0];
            const newPrefix = prefix + (isLast ? '    ' : '│   ');
            const icon = node.type === 'directory' ? '📂' : '📄';
            previewText += prefix + (isLast ? '└── ' : '├── ') + icon + ' ' + node.name + '\n';

            if (node.children && node.children.length > 0) {
                node.children.forEach(child => {
                    child.parent = node;
                    buildPreview(child, newPrefix);
                });
            }
        }

        const simplifiedTree = {
            name: tree.name,
            type: 'directory',
            children: tree.children,
            parent: null
        };

        buildPreview(simplifiedTree);
        treePreview.textContent = previewText;
    }

    // 创建完整HTML内容（核心UI替换部分）
    function createHTMLFromTree(tree, folderName) {
        const generationTime = new Date().toLocaleString();

        let htmlContent = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${folderName} 目录结构</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    :root {
        --primary-color: #4a90e2;
        --secondary-color: #347ab7;
        --bg-color: #f9fafc;
        --card-bg: #ffffff;
        --text-color: #333333;
        --border-color: #eaeaea;
        --hover-color: #f0f7ff;
        --shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        --transition: all 0.2s ease;
        --spacing: 12px;
    }

    body.dark {
        --bg-color: #181818;
        --card-bg: #242424;
        --text-color: #ffffff;
        --border-color: #333333;
        --hover-color: #333333;
        --primary-color: #74c3ff;
    }

    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    body {
        font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
        background-color: var(--bg-color);
        color: var(--text-color);
        padding: 15px;
        line-height: 1.6;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .container {
        max-width: 900px;
        width: 100%;
        background-color: var(--card-bg);
        border-radius: 8px;
        box-shadow: var(--shadow);
        padding: 25px;
        margin-top: 20px;
        transition: var(--transition);
    }

    .header {
        text-align: center;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid var(--border-color);
    }

    h1 {
        color: var(--primary-color);
        font-size: 1.7rem;
        font-weight: 500;
        margin-bottom: 8px;
    }

    .search-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 12px;
        margin: 20px 0;
    }

    .search-container button {
        background: none;
        border: 1px solid var(--border-color);
        width: 40px;
        height: 40px;
        border-radius: 6px;
        cursor: pointer;
        transition: var(--transition);
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text-color);
    }

    .search-container button:hover {
        background-color: var(--hover-color);
        border-color: var(--primary-color);
        color: var(--primary-color);
    }

    .search-container input {
        flex: 1;
        padding: 10px 15px;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        font-size: 15px;
        transition: var(--transition);
        min-width: 250px;
        max-width: 500px;
    }

    .search-container input:focus {
        outline: none;
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
    }

    .tree {
        list-style: none;
        margin: 0;
        padding: 0;
    }

    .tree li {
        margin-bottom: 8px;
        padding: 12px 15px;
        position: relative;
        background-color: var(--card-bg);
        border-radius: 6px;
        border: 1px solid var(--border-color);
        transition: var(--transition);
        cursor: pointer;
    }

    .tree li:hover {
        background-color: var(--hover-color);
        border-color: var(--primary-color);
    }

    .tree .directory-wrapper {
        display: flex;
        align-items: center;
    }

    .tree .toggle {
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 10px;
        color: var(--primary-color);
    }

    .tree .directory, .tree .file-name {
        flex: 1;
        font-size: 15px;
    }

    .tree ul {
        display: none;
        padding-left: 20px;
        margin-top: 8px;
        list-style: none;
    }

    .tree li.open > ul {
        display: block;
    }

    .tree .file {
        display: flex;
        align-items: center;
        padding-left: 30px;
    }

    .file-icon {
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 10px;
        color: var(--primary-color);
    }

    a {
        text-decoration: none;
        color: inherit;
    }

    a:hover {
        color: var(--primary-color);
    }

    .generated-time {
        text-align: center;
        margin-top: 30px;
        padding-top: 15px;
        border-top: 1px solid var(--border-color);
        color: #666;
        font-size: 14px;
        opacity: 0.8;
    }

    .time-icon {
        margin-right: 6px;
        color: var(--primary-color);
    }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>${folderName} 目录结构</h1>
</div>
<div class="search-container">
<button id="toggle-theme"><i class="fas fa-moon"></i></button>
<button id="toggle-all"><i class="fas fa-folder-open"></i></button>
<input type="text" id="search-input" placeholder="搜索文件或文件夹...">
<button id="reset-search"><i class="fas fa-redo"></i></button>
</div>
<ul class="tree">`;

        function buildHTMLTree(node) {
            htmlContent += `<li>
                <div class="directory-wrapper">
                    <span class="toggle"><i class="fas fa-folder"></i></span>
                    <span class="directory">${node.name}</span>
                </div>
                <ul>`;

            node.children.forEach(child => {
                if (child.type === 'file') {
                    htmlContent += `<li>
                        <div class="file">
                            <span class="file-icon"><i class="fas fa-file"></i></span>
                            <a href="./${child.path.replace(/\\/g, '/')}" target="_blank">${child.name}</a>
                        </div>
                    </li>`;
                } else if (child.type === 'directory') {
                    buildHTMLTree(child);
                }
            });

            htmlContent += `</ul>
            </li>`;
        }

        buildHTMLTree(tree);

        htmlContent += `</ul>
<div class="generated-time">
<i class="fas fa-clock time-icon"></i>
<span>生成时间: ${generationTime}</span>
</div>
</div>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        // 目录项点击事件
        document.querySelectorAll('.tree .directory-wrapper').forEach(wrapper => {
            wrapper.addEventListener('click', function(e) {
                if(e.target === this.querySelector('.toggle') || 
                   e.target.parentElement === this.querySelector('.toggle')) {
                    const parent = this.parentElement;
                    parent.classList.toggle('open');
                    const icon = this.querySelector('i');
                    icon.className = parent.classList.contains('open') 
                        ? 'fas fa-folder-open' : 'fas fa-folder';
                }
            });
        });

        // 主题切换
        const toggleTheme = document.getElementById('toggle-theme');
        toggleTheme.addEventListener('click', function() {
            document.body.classList.toggle('dark');
            localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
            this.querySelector('i').className = 
                document.body.classList.contains('dark') ? 'fas fa-sun' : 'fas fa-moon';
        });

        // 初始化主题
        if (localStorage.getItem('theme') === 'dark') {
            document.body.classList.add('dark');
            toggleTheme.querySelector('i').className = 'fas fa-sun';
        }

        // 展开/折叠全部
        const toggleAll = document.getElementById('toggle-all');
        toggleAll.addEventListener('click', function() {
            const isExpanded = this.querySelector('i').className === 'fas fa-folder-open';
            document.querySelectorAll('.tree li').forEach(li => {
                const icon = li.querySelector('.directory-wrapper i');
                if(icon) {
                    li.classList.toggle('open', !isExpanded);
                    icon.className = isExpanded ? 'fas fa-folder' : 'fas fa-folder-open';
                }
            });
            this.querySelector('i').className = isExpanded ? 'fas fa-folder' : 'fas fa-folder-open';
        });

        // 搜索功能
        const searchInput = document.getElementById('search-input');
        const resetSearch = document.getElementById('reset-search');
        
        searchInput.addEventListener('input', function() {
            const term = this.value.toLowerCase();
            document.querySelectorAll('.tree li').forEach(li => {
                const text = li.textContent.toLowerCase();
                const isMatch = text.includes(term);
                li.style.display = isMatch ? '' : 'none';
                
                if(isMatch) {
                    let parent = li.parentElement;
                    while(parent && parent.classList.contains('tree') === false) {
                        parent.style.display = '';
                        parent.classList.add('open');
                        const icon = parent.querySelector('.directory-wrapper i');
                        if(icon) icon.className = 'fas fa-folder-open';
                        parent = parent.parentElement;
                    }
                }
            });
        });

        resetSearch.addEventListener('click', function() {
            searchInput.value = '';
            document.querySelectorAll('.tree li').forEach(li => {
                li.style.display = '';
            });
            const toggleAllIcon = document.getElementById('toggle-all').querySelector('i');
            toggleAllIcon.className = 'fas fa-folder-open';
            document.querySelectorAll('.tree li').forEach(li => {
                li.classList.add('open');
                const icon = li.querySelector('.directory-wrapper i');
                if(icon) icon.className = 'fas fa-folder-open';
            });
        });
    });
</script>
</body>
</html>`;

        return htmlContent;
    }

    // 下载HTML文件
    function downloadHTML(content, filename) {
        const blob = new Blob([content], { type: 'text/html' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();

        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);
    }

    // 显示/隐藏加载动画
    function showLoading(show) {
        loader.style.display = show ? 'block' : 'none';
        selectFolderBtn.disabled = show;
        generateBtn.disabled = show || !selectedFolderHandle;
        includeHiddenCheckbox.disabled = show;
    }

    // 初始化拖拽功能
    initDragAndDrop();
});