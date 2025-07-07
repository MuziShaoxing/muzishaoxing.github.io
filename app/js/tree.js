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

                    // 检查是否支持文件系统访问API
                    if (!('getAsFileSystemHandle' in items[0])) {
                        throw new Error('您的浏览器不支持拖放文件夹功能，请使用最新版Chrome或Edge');
                    }

                    // 获取文件夹句柄
                    const handle = await items[0].getAsFileSystemHandle();
                    if (handle.kind !== 'directory') {
                        throw new Error('请拖放文件夹而非文件');
                    }

                    selectedFolderHandle = handle;
                    
                    // 生成目录树
                    statusDiv.textContent = "正在生成目录树...";
                    treeStructure = await generateDirectoryTree(selectedFolderHandle);
                    
                    // 显示预览
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

            // 检查浏览器支持
            if (!('showDirectoryPicker' in window)) {
                throw new Error('您的浏览器不支持文件夹选择功能，请使用最新版Chrome或Edge');
            }

            // 请求文件夹访问权限
            selectedFolderHandle = await window.showDirectoryPicker();

            // 生成目录树预览
            statusDiv.textContent = "正在生成目录树...";
            treeStructure = await generateDirectoryTree(selectedFolderHandle);

            // 显示预览
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

            // 创建HTML内容
            const htmlContent = createHTMLFromTree(treeStructure, selectedFolderHandle.name);

            // 下载文件
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
            // 根据复选框状态决定是否跳过隐藏文件
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

        // 排序：文件在前，文件夹在后（按名称排序）
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

            // 添加图标区分文件和文件夹
            const icon = node.type === 'directory' ? '📂' : '📄';
            previewText += prefix + (isLast ? '└── ' : '├── ') + icon + ' ' + node.name + '\n';

            if (node.children && node.children.length > 0) {
                // 为子节点添加父引用，用于判断是否为最后一个元素
                node.children.forEach(child => {
                    child.parent = node;
                    buildPreview(child, newPrefix);
                });
            }
        }

        // 简化树结构用于预览
        const simplifiedTree = {
            name: tree.name,
            type: 'directory',
            children: tree.children,
            parent: null
        };

        buildPreview(simplifiedTree);
        treePreview.textContent = previewText;
    }

    // 创建完整HTML内容
    function createHTMLFromTree(tree, folderName) {
        const generationTime = new Date().toLocaleString();

        let htmlContent = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${folderName} - 目录</title>
    <link rel="icon" href="./.APP/favicon.ico" type="image/x-icon">
<link rel="shortcut icon" href="./.APP/favicon.ico" type="image/x-icon">
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
        :root {
            --background-color: #f9fbff;
            --container-bg: #ffffff;
            --text-color: #4a5a7a;
            --primary-color: #6c8dcd;
            --secondary-color: #7da3e6;
            --light-color: #f3f8ff;
            --dark-color: #1d2430;
            --gray-color: #273142;
            --shadow-color: rgba(108, 141, 205, 0.08);
            --dark-shadow: rgba(0, 0, 0, 0.2);
            --button-size: 46px;
            --spacing: 15px;
            --transition-time: 0.3s;
            --border-radius: 12px;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Segoe UI', 'Microsoft YaHei', 'Roboto', sans-serif;
            background-color: var(--background-color);
            color: var(--text-color);
            padding: 20px;
            transition: background-color var(--transition-time), color var(--transition-time);
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            background-image: linear-gradient(135deg, #f9fbff 0%, #f3f8ff 100%);
        }
        .container {
            max-width: 1000px;
            width: 100%;
            background-color: var(--container-bg);
            padding: 30px;
            border-radius: var(--border-radius);
            box-shadow: 0 8px 25px var(--shadow-color);
            transition: all 0.4s ease;
            margin-top: 20px;
            position: relative;
            overflow: hidden;
        }
        .container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #6c8dcd, #7da3e6, #6c8dcd);
            border-radius: var(--border-radius) var(--border-radius) 0 0;
        }
        .header {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 25px;
            flex-wrap: wrap;
            gap: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e8f0ff;
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .logo-icon {
            width: 42px;
            height: 42px;
            object-fit: contain;
            border-radius: 0%;
            box-shadow: 0 2px 8px rgba(108, 141, 205, 0.15);
        }
        .logo-text {
            font-size: 1.8em;
            font-weight: 700;
            color: var(--text-color);
            letter-spacing: 0.5px;
            background: linear-gradient(135deg, #6c8dcd, #4a5a7a);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .search-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: var(--spacing);
            position: relative;
        }
        .button-group {
            display: flex;
            gap: var(--spacing);
        }
        .search-container button {
            background: #f3f8ff;
            color: var(--primary-color);
            border: 1px solid #e0ebff;
            width: var(--button-size);
            height: var(--button-size);
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2em;
            transition: all var(--transition-time);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            box-shadow: 0 2px 8px rgba(108, 141, 205, 0.08);
        }
        .search-container button:hover {
            background-color: #e6f0ff;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(108, 141, 205, 0.12);
        }
        .search-container button:active {
            transform: translateY(0);
            box-shadow: 0 2px 6px rgba(108, 141, 205, 0.08);
        }
        .search-container input {
            flex: 1;
            padding: 14px 20px;
            border: 1px solid #e0ebff;
            border-radius: 30px;
            font-size: 16px;
            transition: all var(--transition-time);
            max-width: 600px;
            min-width: 200px;
            background: #fafcff;
            color: var(--text-color);
            box-shadow: 0 2px 8px rgba(108, 141, 205, 0.05);
        }
        .search-container input:focus {
            border-color: var(--primary-color);
            outline: none;
            box-shadow: 0 0 0 3px rgba(108, 141, 205, 0.15);
            background: #fff;
        }
        .search-container input::placeholder {
            color: #b8cbe8;
        }
        .tree {
            margin: 0;
            padding: 0;
            list-style: none;
        }
        .tree li {
            margin: 0;
            padding: 10px 0;
            position: relative;
            background-color: var(--container-bg);
            border-radius: 8px;
            transition: all var(--transition-time);
            cursor: pointer;
            padding: 12px 18px;
            box-shadow: 0 2px 6px rgba(108, 141, 205, 0.04);
            margin-bottom: 8px;
            border-left: 3px solid transparent;
        }
        .tree li:hover {
            background-color: var(--light-color);
            border-left-color: var(--primary-color);
            transform: translateX(5px);
        }
        .tree .directory-wrapper {
            display: flex;
            align-items: center;
            padding-left: 10px;
        }
        .tree .toggle {
            margin-right: 12px;
            cursor: pointer;
            user-select: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            color: var(--primary-color);
            font-size: 14px;
            flex-shrink: 0;
            background: #e6f0ff;
            border-radius: 50%;
        }
        .material-icons {
            font-size: 20px;
            transition: transform 0.2s;
        }
        .tree .directory {
            font-weight: 600;
            color: var(--text-color);
            font-size: 1.05em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .tree .directory::before {
            content: '';
            display: inline-block;
            width: 24px;
            height: 24px;
            background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%236c8dcd'%3E%3Cpath d='M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z'/%3E%3C/svg%3E");
            background-size: contain;
        }
        .tree .file {
            display: flex;
            align-items: center;
            padding-left: 40px;
            position: relative;
        }
        .tree .file::before {
            content: '';
            position: absolute;
            left: 15px;
            width: 24px;
            height: 24px;
            background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%237da3e6'%3E%3Cpath d='M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6z'/%3E%3C/svg%3E");
            background-size: contain;
        }
        .tree .file a {
            text-decoration: none;
            color: var(--text-color);
            transition: all var(--transition-time);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            padding: 4px 0;
            border-bottom: 1px dashed transparent;
        }
        .tree .file a:hover {
            color: var(--primary-color);
            border-bottom: 1px dashed var(--primary-color);
            text-decoration: none;
        }
        .tree ul {
            display: none;
            padding-left: 25px;
            margin-top: 10px;
            list-style: none;
            border-left: 1px dashed #e0ebff;
            margin-left: 12px;
        }
        .tree li.open > ul {
            display: block;
        }

        /* 暗色主题 */
        body.dark {
            --background-color: var(--dark-color);
            --container-bg: var(--gray-color);
            --text-color: #d5e3ff;
            --primary-color: #7da3e6;
            --secondary-color: #8eb1f0;
            --light-color: #222b3d;
            --shadow-color: rgba(0, 15, 30, 0.3);
            background-image: linear-gradient(135deg, #1d2430 0%, #171e2a 100%);
        }

        body.dark .container::before {
            background: linear-gradient(90deg, #3d5a9c, #4d6fb8, #3d5a9c);
        }

        body.dark .tree li:hover {
            background-color: var(--light-color);
            border-left-color: var(--primary-color);
        }

        body.dark .search-container input {
            background: #1d2535;
            border-color: #2a3548;
            color: #d5e3ff;
        }

        body.dark .search-container input:focus {
            background: #212b3e;
            box-shadow: 0 0 0 3px rgba(125, 163, 230, 0.25);
        }

        body.dark .search-container button {
            background: #212b3e;
            border-color: #2a3548;
            color: #7da3e6;
        }

        body.dark .tree .file a:hover {
            color: var(--secondary-color);
            border-bottom: 1px dashed var(--secondary-color);
        }

        body.dark .tree ul {
            border-left: 1px dashed #2a3548;
        }

        /* 高分辨率屏幕上的图标大小 */
        @media (min-resolution: 2dppx) {
            .material-icons {
                font-size: 22px;
            }
        }

        /* 平板上的布局调整 */
        @media (max-width: 992px) {
            .container {
                padding: 20px 15px;
            }
            .search-container {
                flex-direction: column;
                gap: 10px;
            }
            .search-container input {
                width: 100%;
                max-width: 100%;
            }
            .button-group {
                width: 100%;
                justify-content: center;
            }
        }

        /* 手机上的布局优化 */
        @media (max-width: 576px) {
            body {
                padding: 10px;
            }
            .container {
                padding: 20px 12px;
                margin-top: 10px;
            }
            .logo-text {
                font-size: 1.5em;
            }
            .logo-icon {
                width: 36px;
                height: 36px;
            }
            .search-container input {
                padding: 12px 16px;
            }
            .tree li {
                padding: 10px 14px;
            }
            .tree .file {
                padding-left: 35px;
            }
            .tree .file::before {
                left: 10px;
            }
            .tree ul {
                padding-left: 20px;
            }
        }

        /* 滚动条样式 */
        .tree {
            max-height: 65vh;
            overflow-y: auto;
            padding-right: 8px;
            margin-top: 10px;
        }
        
        /* 自定义滚动条 */
        .tree::-webkit-scrollbar {
            width: 8px;
        }
        
        .tree::-webkit-scrollbar-track {
            background: rgba(108, 141, 205, 0.05);
            border-radius: 4px;
        }
        
        .tree::-webkit-scrollbar-thumb {
            background: rgba(108, 141, 205, 0.15);
            border-radius: 4px;
        }
        
        .tree::-webkit-scrollbar-thumb:hover {
            background: rgba(108, 141, 205, 0.25);
        }
        
        body.dark .tree::-webkit-scrollbar-track {
            background: rgba(29, 36, 48, 0.3);
        }
        
        body.dark .tree::-webkit-scrollbar-thumb {
            background: rgba(125, 163, 230, 0.25);
        }
        
        body.dark .tree::-webkit-scrollbar-thumb:hover {
            background: rgba(125, 163, 230, 0.35);
        }

        /* 全局操作按钮样式 */
        .global-action {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 18px;
            background: linear-gradient(135deg, #6c8dcd, #7da3e6);
            color: white;
            border: none;
            border-radius: 30px;
            cursor: pointer;
            font-size: 15px;
            transition: all var(--transition-time);
            height: var(--button-size);
            box-shadow: 0 4px 12px rgba(108, 141, 205, 0.2);
        }

        .global-action:hover {
            background: linear-gradient(135deg, #5e7cb8, #6c92d8);
            transform: translateY(-3px);
            box-shadow: 0 6px 15px rgba(108, 141, 205, 0.25);
        }

        .global-action:active {
            transform: translateY(0);
            box-shadow: 0 2px 8px rgba(108, 141, 205, 0.2);
        }

        body.dark .global-action {
            background: linear-gradient(135deg, #5a75b0, #6c8dcd);
        }

        body.dark .global-action:hover {
            background: linear-gradient(135deg, #4e67a0, #5e7cb8);
        }
        
        /* 高亮匹配项 */
        .match-highlight {
            background-color: rgba(108, 141, 205, 0.12) !important;
            border: 1px solid rgba(108, 141, 205, 0.2) !important;
            box-shadow: 0 0 10px rgba(108, 141, 205, 0.08) !important;
        }
        body.dark .match-highlight {
            background-color: rgba(125, 163, 230, 0.15) !important;
            border: 1px solid rgba(125, 163, 230, 0.3) !important;
        }
        
        /* 动画效果 */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .container {
            animation: fadeIn 0.5s ease-out;
        }

        /* 生成时间信息样式 */
        .generation-info {
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #e8f0ff;
            text-align: center;
            font-size: 0.9em;
            color: #8a9bb8;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
        }
        
        .generation-info .material-icons {
            font-size: 16px;
        }
        
        body.dark .generation-info {
            border-top-color: #2a3548;
            color: #7a8ca8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <div class="logo-text">${folderName}</div>
            </div>
        </div>
        <div class="search-container">
            <div class="button-group">
                <button id="toggle-theme" aria-label="切换主题"><span class="material-icons">light_mode</span></button>
                <button id="toggle-all" aria-label="展开/折叠全部">
                    <span class="material-icons">unfold_more</span>
                </button>
            </div>
            <input type="text" id="search-input" placeholder="搜索文件或文件夹...">
            <div class="button-group">
                <button id="reset-search" aria-label="重置搜索"><span class="material-icons">refresh</span></button>
            </div>
        </div>
        <ul class="tree">`;

        function buildHTMLTree(node) {
            htmlContent += `<li>
                <div class="directory-wrapper">
                    <span class="toggle"><span class="material-icons">chevron_right</span></span>
                    <span class="directory">${node.name}</span>
                </div>
                <ul>`;

            node.children.forEach(child => {
                if (child.type === 'file') {
                    htmlContent += `<li>
                        <div class="file">
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
        <div class="generation-info">
            <span class="material-icons">schedule</span>
            <span>生成时间: ${generationTime}</span>
        </div>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // 为所有目录项添加点击事件
            document.querySelectorAll('.tree .directory-wrapper').forEach(wrapper => {
                wrapper.addEventListener('click', function() {
                    const parentLi = this.parentElement;
                    parentLi.classList.toggle('open');
                    const toggleIcon = this.querySelector('.toggle .material-icons');
                    if (parentLi.classList.contains('open')) {
                        toggleIcon.textContent = 'expand_more';
                    } else {
                        toggleIcon.textContent = 'chevron_right';
                    }
                });
            });

            // 默认展开所有节点
            expandAll(document.querySelector('.tree'));

            // 切换主题按钮
            const toggleThemeButton = document.getElementById('toggle-theme');
            toggleThemeButton.addEventListener('click', function() {
                const body = document.body;
                if (body.classList.contains('dark')) {
                    body.classList.remove('dark');
                    this.querySelector('.material-icons').textContent = 'light_mode';
                    localStorage.setItem('theme', 'light');
                } else {
                    body.classList.add('dark');
                    this.querySelector('.material-icons').textContent = 'dark_mode';
                    localStorage.setItem('theme', 'dark');
                }
            });

            // 检查本地存储中的主题设置
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'dark') {
                document.body.classList.add('dark');
                document.getElementById('toggle-theme').querySelector('.material-icons').textContent = 'dark_mode';
            }

            // 展开&折叠按钮
            const toggleAllButton = document.getElementById('toggle-all');
            toggleAllButton.addEventListener('click', function() {
                const icon = this.querySelector('.material-icons');
                if (icon.textContent === 'unfold_more') {
                    collapseAll(document.querySelector('.tree'));
                    icon.textContent = 'unfold_less';
                } else {
                    expandAll(document.querySelector('.tree'));
                    icon.textContent = 'unfold_more';
                }
            });

            // 搜索功能
            const searchInput = document.getElementById('search-input');
            const resetSearchButton = document.getElementById('reset-search');
            const tree = document.querySelector('.tree');

            searchInput.addEventListener('input', function() {
                const searchTerm = this.value.trim().toLowerCase();
                filterTree(tree, searchTerm);
                
                // 显示/隐藏重置按钮
                if (searchTerm.length > 0) {
                    resetSearchButton.style.display = 'flex';
                } else {
                    resetSearchButton.style.display = 'none';
                }
            });

            // 初始隐藏重置按钮
            resetSearchButton.style.display = 'none';

            // 重置搜索框按钮
            resetSearchButton.addEventListener('click', function() {
                searchInput.value = '';
                filterTree(tree, '');
                this.style.display = 'none';
                // 重置后恢复展开状态
                expandAll(document.querySelector('.tree'));
                // 更新切换按钮状态
                const toggleAllButton = document.getElementById('toggle-all');
                toggleAllButton.querySelector('.material-icons').textContent = 'unfold_more';
            });
        });

        function expandAll(node) {
            node.querySelectorAll('.directory-wrapper').forEach(wrapper => {
                const parentLi = wrapper.parentElement;
                parentLi.classList.add('open');
                const toggleIcon = wrapper.querySelector('.toggle .material-icons');
                toggleIcon.textContent = 'expand_more';
            });
        }

        function collapseAll(node) {
            node.querySelectorAll('.directory-wrapper').forEach(wrapper => {
                const parentLi = wrapper.parentElement;
                parentLi.classList.remove('open');
                const toggleIcon = wrapper.querySelector('.toggle .material-icons');
                toggleIcon.textContent = 'chevron_right';
            });
        }

        function filterTree(node, searchTerm) {
            const listItems = node.querySelectorAll('li');
            let hasMatches = false;
            
            // 重置所有显示状态
            listItems.forEach(item => {
                item.style.display = '';
                item.classList.remove('match-highlight');
            });
            
            if (searchTerm === '') {
                return;
            }
            
            listItems.forEach(item => {
                const text = item.textContent.toLowerCase();
                
                if (text.includes(searchTerm)) {
                    hasMatches = true;
                    // 高亮匹配项
                    item.classList.add('match-highlight');
                    
                    // 确保所有祖先项都可见并展开
                    let parent = item.parentElement;
                    while (parent && parent.classList.contains('tree') === false) {
                        if (parent.tagName === 'UL') {
                            parent.style.display = 'block';
                            const parentLi = parent.parentElement;
                            if (parentLi && parentLi.classList.contains('li')) {
                                parentLi.classList.add('open');
                                const toggleIcon = parentLi.querySelector('.toggle .material-icons');
                                if (toggleIcon) {
                                    toggleIcon.textContent = 'expand_more';
                                }
                            }
                        }
                        parent = parent.parentElement;
                    }
                } else {
                    // 只隐藏没有子匹配项的项
                    const hasVisibleChildren = item.querySelector('li[style*="display:"]') !== null;
                    if (!hasVisibleChildren) {
                        item.style.display = 'none';
                    }
                }
            });
            
            // 如果没有匹配项，显示提示
            if (!hasMatches) {
                const noResults = document.createElement('li');
                noResults.textContent = '没有找到匹配项';
                noResults.style.textAlign = 'center';
                noResults.style.padding = '20px';
                noResults.style.color = '#999';
                node.appendChild(noResults);
            }
        }
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