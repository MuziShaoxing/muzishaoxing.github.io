const navMenuItems = document.querySelectorAll('#nav-menu a'); // 获取导航菜单中的所有链接元素

// 设置指示器的点击切换
function handleMenuItemClick(target) { // 定义处理菜单项点击的函数
    navMenuItems.forEach(item => { // 遍历所有导航菜单项
        item.classList.remove('active'); // 移除当前菜单项的 'active' 类
        item.style = ''; // 清除当前菜单项的内联样式
    });
    target.classList.add('active'); // 为被点击的菜单项添加 'active' 类

    // 设置要展示的内容
    const currentSection = document.querySelector('.active-section'); // 获取当前显示的页面内容区域
    currentSection.classList.remove('active-section'); // 移除当前内容区域的 'active-section' 类
    const newCurrentSection = document.querySelector(`.${target.getAttribute('data-rel')}`); // 根据被点击菜单项的 data-rel 属性找到对应的内容区域
    newCurrentSection.classList.add('active-section'); // 为对应的内容区域添加 'active-section' 类
}

navMenuItems.forEach(item => { // 遍历所有导航菜单项
    item.addEventListener('click', e => handleMenuItemClick(e.target)); // 为每个菜单项添加点击事件监听器，调用 handleMenuItemClick 函数
    item.classList.contains('active') && handleMenuItemClick(item); // 如果菜单项已经包含 'active' 类，则调用 handleMenuItemClick 函数
});