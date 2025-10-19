const { chromium } = require('playwright');
const path = require('path');

// 使用Playwright通过DOM结构提取HTML文件中的标题
async function extractTitleWithPlaywright() {
    const htmlFilePath = path.resolve('d:/AiProject/traeWorkspace/playWright/摘取.html');
    let browser = null;
    
    try {
        // 启动浏览器
        browser = await chromium.launch({
            headless: true // 设置为false可以看到浏览器操作过程
        });
        
        // 创建新页面
        const page = await browser.newPage();
        
        // 加载本地HTML文件
        await page.goto(`file://${htmlFilePath}`);
        console.log('HTML文件已加载');
        
        // 通过上层div的class来获取input的值
        // 尝试从class为"title-widget"的div内的input中获取标题
        let title = null;
        
        try {
            // 等待input元素加载完成
            await page.waitForSelector('.title-widget input', { timeout: 3000 });
            // 获取input的值
            title = await page.$eval('.title-widget input', input => input.value);
            console.log('成功通过Playwright从input中提取到标题:', title);
        } catch (inputError) {
            console.log('未找到input元素，尝试从文件名div中提取');
            
            // 如果input获取失败，尝试从class为"file-name"的div内的span元素中获取
            try {
                await page.waitForSelector('.file-name span', { timeout: 3000 });
                title = await page.$eval('.file-name span', span => span.textContent.trim());
                console.log('成功通过Playwright从文件名div中提取到标题:', title);
            } catch (spanError) {
                console.log('未找到文件名div元素');
            }
        }
        
        if (!title) {
            console.log('未找到目标标题');
        }
        
        return title;
    } catch (error) {
        console.error('使用Playwright提取标题时出错:', error.message);
        return null;
    } finally {
        // 确保关闭浏览器
        if (browser) {
            await browser.close();
            console.log('浏览器已关闭');
        }
    }
}

// 执行提取函数
(async () => {
    console.time('提取标题');
    const extractedTitle = await extractTitleWithPlaywright();
    console.log('最终提取结果:', extractedTitle);
    console.timeEnd('提取标题');
})();