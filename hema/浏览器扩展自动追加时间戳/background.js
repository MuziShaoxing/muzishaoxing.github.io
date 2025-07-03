// background.js
chrome.downloads.onDeterminingFilename.addListener((item, suggest) => {
  // 监听 Chrome 下载事件，当确定文件名时触发回调函数
  // item：包含下载信息的对象
  // suggest：用于建议新文件名的函数

  console.log('Download detected:', item); // 添加调试信息，输出下载信息
  const currentDate = new Date(); // 获取当前日期和时间
  const year = String(currentDate.getFullYear()).substr(-2); // 获取年份的后两位
  const month = String(currentDate.getMonth() + 1).padStart(2, '0'); // 获取月份并确保是两位数字
  const day = String(currentDate.getDate()).padStart(2, '0'); // 获取日期并确保是两位数字
  const dateStr = `${year}${month}${day}`; // 组合成 YYMMDD 格式
  
  let fileName = item.filename; // 获取原始文件名
  const extensionMatch = item.filename.match(/\.[^/.]+$/); // 使用正则表达式匹配文件扩展名

  // 如果文件有扩展名
  if (extensionMatch) {
    const fileNameWithoutExtension = item.filename.replace(extensionMatch[0], ''); // 去掉扩展名
    fileName = `${fileNameWithoutExtension}_${dateStr}${extensionMatch[0]}`; // 组合新文件名：原文件名（无扩展）_日期.扩展名
  } else {
    // 如果没有扩展名，直接在文件名后添加日期
    fileName = `${fileName}_${dateStr}`;
  }

  console.log('Suggesting new filename:', fileName); // 输出建议的新文件名（调试信息）
  suggest({ filename: fileName }); // 建议使用新文件名
});