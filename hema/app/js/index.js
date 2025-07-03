document.addEventListener('DOMContentLoaded', function () {
    const downloadLinks = document.querySelectorAll('.item a');

    downloadLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault(); // 阻止默认下载行为

            const originalUrl = this.getAttribute('href');
            const fileName = originalUrl.substring(originalUrl.lastIndexOf('/') + 1);
            const currentDate = new Date();

            // 格式化日期为 YYMMDD
            const year = currentDate.getFullYear().toString().slice(-2); // 获取年份的后两位
            const month = (currentDate.getMonth() + 1).toString().padStart(2, '0'); // 获取月份并补零
            const day = currentDate.getDate().toString().padStart(2, '0'); // 获取日期并补零
            const formattedDate = `${year}${month}${day}`;

            // 新文件名，格式为 "原文件名_YYMMDD.扩展名"
            const newFileName = fileName.replace(/\.\w+$/, `_${formattedDate}$&`);

            // 创建一个新的隐身的 a 标签
            const tempLink = document.createElement('a');
            tempLink.href = originalUrl; // 使用原始文件的 URL
            tempLink.download = newFileName; // 设置下载的文件名为新文件名
            document.body.appendChild(tempLink);

            // 触发下载
            tempLink.click();

            // 清理
            document.body.removeChild(tempLink);
        });
    });
});