// 网站运行时间计算脚本
(function() {
  // 网站上线日期（格式：YYYY, MM, DD）
  const launchDate = new Date(2023, 3, 1); // 例如：2023年4月1日（注意：月份从0开始，3表示4月）

  // 更新运行时间的函数
  function updateSiteTime() {
    // 获取当前日期和时间
    const now = new Date();
    // 计算运行时间
    const diff = now - launchDate;

    // 转换为天数、小时、分钟和秒
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    // 更新页面中的运行时间显示
    document.getElementById('sitetime').innerText = `本站已运行：${days}天 ${hours}小时 ${minutes}分钟 ${seconds}秒`;
  }

  // 初始更新
  updateSiteTime();

  // 每秒更新一次
  setInterval(updateSiteTime, 1000);
})();