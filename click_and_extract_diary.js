const playwright = require('playwright');
const fs = require('fs');
const path = require('path');

// 日志文件路径
const logFilePath = path.join(__dirname, `执行日志_${new Date().toISOString().replace(/:/g, '-').replace(/\./g, '-')}.txt`);

// 重定向控制台输出到文件
const originalConsoleLog = console.log;
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;
const originalConsoleInfo = console.info;

// 自定义日志函数 - 支持多参数
function logToFileAndConsole(...args) {
    // 将所有参数转换为字符串并合并
    const logMessage = args.map(arg => {
        // 对于对象和数组使用JSON.stringify，否则使用String()
        return typeof arg === 'object' && arg !== null ? JSON.stringify(arg) : String(arg);
    }).join(' ');
    
    // 追加到日志文件
    fs.appendFileSync(logFilePath, logMessage + '\n');
    
    // 同时输出到控制台（保留原始参数）
    originalConsoleLog(...args);
}

// 重写控制台方法 - 支持多参数
console.log = logToFileAndConsole;

console.error = function(...args) {
    const logMessage = '[ERROR] ' + args.map(arg => {
        return typeof arg === 'object' && arg !== null ? JSON.stringify(arg) : String(arg);
    }).join(' ');
    
    fs.appendFileSync(logFilePath, logMessage + '\n');
    originalConsoleError(...args);
};

console.warn = function(...args) {
    const logMessage = '[WARN] ' + args.map(arg => {
        return typeof arg === 'object' && arg !== null ? JSON.stringify(arg) : String(arg);
    }).join(' ');
    
    fs.appendFileSync(logFilePath, logMessage + '\n');
    originalConsoleWarn(...args);
};

console.info = function(...args) {
    const logMessage = '[INFO] ' + args.map(arg => {
        return typeof arg === 'object' && arg !== null ? JSON.stringify(arg) : String(arg);
    }).join(' ');
    
    fs.appendFileSync(logFilePath, logMessage + '\n');
    originalConsoleInfo(...args);
};

console.log(`🔍 日志将同时保存到: ${logFilePath}`);

// 确保导出目录存在
const exportDir = path.join(__dirname, '笔记导出');
if (!fs.existsSync(exportDir)) {
    fs.mkdirSync(exportDir, { recursive: true });
}

// 生成带时间戳的文件名
function generateFileName(prefix = '日记') {
    const timestamp = new Date().toISOString().replace(/:/g, '-').replace(/\./g, '-');
    return path.join(exportDir, `有道云笔记_${prefix}_${timestamp}.txt`);
}

// 主提取函数
async function extractNotes() {
    console.log('🚀 开始有道云笔记日记提取...');
    console.log('==================================');

    let browser = null;
    let context = null;
    let page = null;
    const cookiePath = path.join(__dirname, 'cookies.json');

    try {
        // 启动浏览器
        console.log('🔧 启动浏览器...');
        browser = await playwright.chromium.launch({
            headless: false,
            slowMo: 100,
            args: ['--start-maximized']
        });

        // 创建上下文
        context = await browser.newContext({
            viewport: { width: 1920, height: 880 },
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        });
        let cookies = null;
        // 尝试加载保存的cookies
        if (fs.existsSync(cookiePath)) {
            try {
                console.log('🍪 尝试加载保存的cookie...');
                cookies = JSON.parse(fs.readFileSync(cookiePath, 'utf8'));
                await context.addCookies(cookies);
                console.log('✅ Cookie加载成功');
            } catch (err) {
                console.log('⚠️ Cookie加载失败:', err.message);
            }
        } else {
            console.log('ℹ️  Cookie文件不存在，将在登录后创建');
        }

        // 创建新页面
        page = await context.newPage();

        // 导航到有道云笔记网页版
        console.log('🌐 导航到有道云笔记...');
        await page.goto('https://note.youdao.com/web/');
        console.log('✅ 已打开有道云笔记网页版');

        // 等待一段时间让页面加载
        await page.waitForTimeout(3000);

        if (cookies == null) {
            // 等待用户登录和导航到日记文件夹
            console.log('\n📝 请按照以下步骤操作:');
            console.log('1. 在打开的浏览器窗口中完成登录');
            console.log('2. 成功登录后，手动导航到"日记"文件夹');
            console.log('3. 确保所有日记条目都显示在页面上');
            console.log('\n⏳ 请等待40秒完成上述操作...');
            // 等待60秒让用户完成登录和导航
            console.log('正在等待用户登录...');
            await page.waitForTimeout(40000);
            // 登录成功后保存cookies
            try {
                const cookies = await context.cookies();
                fs.writeFileSync(cookiePath, JSON.stringify(cookies, null, 2), 'utf8');
                console.log('✅ Cookie已保存，下次运行将自动登录');
            } catch (err) {
                console.log('❌ Cookie保存失败:', err.message);
            }

        } else {
            console.log('✅ 检测到已登录状态，跳过手动登录步骤');
            // 给已登录的页面一些加载时间
            await page.waitForTimeout(10000);
        }

        // 检查当前页面状态
        const currentUrl = await page.url();
        const pageTitle = await page.title();
        console.log(`\n📊 页面状态检查:`);
        console.log(`  - 当前URL: ${currentUrl}`);
        console.log(`  - 页面标题: ${pageTitle}`);

        // 尝试检查是否在日记页面
        const hasNotes = await page.evaluate(() => {
            const diaryElements = document.querySelectorAll(
                '.note-item, .list-item, [class*="diary"], [class*="journal"]'
            );
            return diaryElements.length > 0;
        });

        if (!hasNotes) {
            console.log('⚠️  警告: 可能不在日记页面，继续尝试提取...');
        } else {
            console.log('✅ 检测到笔记元素，继续提取...');
        }

        // 一、添加页面滚动逻辑以确保内容完全加载
        console.log('\n🔄 正在滚动页面加载更多内容...');
        const scrollIterations = 10; // 进一步增加滚动次数
        const uniqueContents = new Set(); // 用于检测是否加载了新内容
        let noUpdateCount = 0;
        const MAX_NO_UPDATES = 3; // 连续几次无更新后才停止

        for (let i = 0; i < scrollIterations; i++) {
            
            // 改进的滚动策略：先到底部，再回到顶部，再到底部，增加触发加载的概率
            const result = await page.evaluate(() => {
                const scrollableContainer = document.querySelector('.list-bd.topNameTag');
                if (scrollableContainer) {
                    scrollableContainer.scrollTop = scrollableContainer.scrollHeight;
                    return '⏳ 成功获取可滚动容器并滚动';
                } else {
                    return '❌ 未找到可滚动容器';
                }
            });
            console.log(result); // 这行会在 Node.js 终端打印

            // 增加等待时间，确保内容充分加载
            await page.waitForTimeout(1000);
        }

        console.log('✅ 页面滚动完成，已加载内容样本数:', uniqueContents.size);

        // page.on('console', msg => {
        //     console.log('📟 [浏览器控制台] ', msg.text());
        // });
        // 二、逐一点击页面中所有笔记
        // ✅ 先获取所有符合条件的 <li> 元素（list-li file-item selected）
        const listItems = await page.$$('.list-bd.topNameTag li.list-li.file-item');
        console.log(`✅ 找到 ${listItems.length} 个符合条件的 li 元素`);
        const outputValues = [];
        let content = "";
        // 日记条目
        let processedCount = 0;
        let totalContentLength = 0;
        for (const item of listItems) {
            console.log('---');
            console.log('🔸 准备点击一个 li 元素');
            // 1. 点击这个 li
            await item.click();
            console.log('✅ 已点击一个 li');
            // 增加等待时间，确保内容充分加载
            await page.waitForTimeout(1000);

            // 2. 等待 iframe 加载（可以根据实际情况调整选择器，比如通过 id 最精准）
            const iframeEl = await page.$('#bulb-editor'); // ✅ 用 iframe 的 id 来定位
            if (!iframeEl) {
                console.log('❌ 未找到 iframe（#bulb-editor）');
                outputValues.push('未找到 iframe');
                continue;
            }
            // 3. 获取 iframe 的 frame 对象
            const frame = await iframeEl.contentFrame();
            if (!frame) {
                console.log('❌ 无法获取 iframe 的 contentFrame');
                outputValues.push('未获取到 iframe 上下文');
                continue;
            }
            try {
                // 4. 等待 iframe 内的输入框出现（请根据实际选择器调整！）
                // 比如：可能是 .title-widget input，或者 .css-1r2ld0m，或者 input[placeholder="无标题笔记"]
                await page.waitForSelector('pre.top-title-placeholder', { timeout: 5000 });

                // 5. 获取标题
                //const inputEl = await frame.$('.title-widget input');
                const preEl = await page.$('pre.top-title-placeholder');
                if (preEl) {
                    const val = await preEl.textContent(); // ✅ 推荐获取输入框值的方法
                    console.log('📝 获取到的输入框值:', val);
                    content += '###标题###[' + val + '] \n\n';
                    processedCount++;
                    outputValues.push(val);
                } else {
                    console.log('❌ 在 iframe 中未找到 input 元素');
                    outputValues.push('未找到输入框（iframe内未找到）');
                }
                // 6. 找到正文所有段落 div（data-block-type="paragraph"）
                // 定义可能的选择器（按优先级排序）
                const SELECTORS = [
                    'div[data-block-type="paragraph"].css-1xgc5oj',// 优先选择器 有道云-正文格式
                    'span.css-wc3k03',// 次优先选择器 有道云-项目格式
                    'div.css-1eawncy > span'// 最后选择器 有道云-单选框格式
                ];
                let paragraphs = [];
                for (const selector of SELECTORS) {
                    paragraphs = await frame.$$(selector);
                    if (paragraphs.length > 0) {
                        console.log(`✅ 使用选择器 "${selector}" 找到 ${paragraphs.length} 个段落`);
                        break;
                    }
                    console.log(`❌ 使用选择器 "${selector}" 未找到段落`);
                }
                if (paragraphs.length === 0) {
                    console.log('❌ 所有选择器均未找到段落');
                }
                const allTextParts = [];
                for (const para of paragraphs) {
                    // ✅ 使用 Playwright 的 .$('selector') 查找子元素，不是原生 DOM 的 querySelector
                    const spanWrapper = await para.$('span[data-bulb-node-id]');
                    if (spanWrapper) {
                        let text = await spanWrapper.textContent(); // ✅ 注意：这是异步的，必须用 await
                        const textSpan = await spanWrapper.$('span'); // 最内层 span，包含文本
                        // 如果最内层span包含文本，就用最内层span的文本，否则用外层span的文本
                        if (textSpan) {
                            text = await textSpan.textContent(); // ✅ 注意：这是异步的，必须用 await
                        }
                        const trimmed = text?.trim();
                        if (trimmed) {
                            // console.log('📄 段落内容:', trimmed);
                            allTextParts.push(trimmed);
                        }
                    }
                }
                const combinedText = allTextParts.join('\n\n'); // 用两个换行符分隔段落
                console.log('🔗 拼接后的全文内容:\n', combinedText);
                content += combinedText + '\n\n';
            } catch (err) {
                console.log('❌ 在 iframe 中等待输入框超时或出错：', err.message);
                outputValues.push('未找到输入框（iframe内等待超时）');
            }
        }
        console.log('🎉 所有操作完成，获取的输入框值列表:', outputValues);

        let pageText = content; 
        // 获取页面文本内容 - 增强版
        console.log('\n📋 获取页面文本...');
        console.time('页面文本获取');

        console.timeEnd('页面文本获取');
        totalContentLength = pageText.length.toLocaleString();
        console.log(`📊 页面文本长度: ${totalContentLength} 字符`);

        // 给内容提取一个预热过程，确保所有内容都已加载
        await page.waitForTimeout(5000);

        // 统计信息
        console.log(`   - 原始文本行数: ${pageText.split('\n').length}`);

        // 准备输出内容
        let allNotesContent = '# 有道云笔记 - 日记内容汇总\n\n';
        allNotesContent += `导出时间: ${new Date().toLocaleString('zh-CN')}\n\n`;
        allNotesContent += `导出条目数: ${processedCount}\n\n`;
        allNotesContent += `==================================\n\n`;
        allNotesContent += pageText + '\n\n';

        // 保存提取的内容
        if (allNotesContent.length > 100) { // 确保有实际内容
            const outputFile = generateFileName('日记');
            fs.writeFileSync(outputFile, allNotesContent, 'utf8');

            // 最终统计信息
            console.log('\n🎉 提取完成！');
            console.log('==================================');
            console.log(`✅ 成功提取 ${processedCount} 个日记条目`);
            console.log(`📊 平均每个条目内容长度: ${Math.round(totalContentLength / processedCount)} 字符`);
            console.log(`📄 输出文件大小: ${Math.round(allNotesContent.length / 1024)} KB`);
            console.log(`📂 内容已保存到: ${outputFile}`);
            console.log('==================================');
        } else {
            console.log('\n❌ 未能提取到有效内容');

            // 当没有提取到内容时，尝试替代方法
            console.log('\n🔄 尝试替代提取方法...');
            try {
                console.log(`获取到页面文本内容 (长度: ${pageText.length})`);
                const outputFile = generateFileName('日记_替代方法');
                fs.writeFileSync(outputFile, `# 页面文本内容\n\n${pageText.substring(0, 10000)}`, 'utf8');
                console.log(`📄 替代内容已保存到: ${outputFile}`);
            } catch (e) {
                console.error('❌ 替代方法也失败:', e.message);
            }
        }

    } catch (error) {
        console.error(`\n❌ 发生错误: ${error.message}`);

        // 尝试获取页面文本作为备选
        try {
            if (page) {
                console.log('🔄 尝试获取页面文本作为备选...');
                const pageText = await page.evaluate(() => document.body.innerText);
                const outputFile = generateFileName('日记_替代方法');
                fs.writeFileSync(outputFile, pageText, 'utf8');
                console.log(`📄 备选文本已保存到: ${outputFile}`);
            }
        } catch (altError) {
            console.error('❌ 保存备选文本失败:', altError.message);
        }
    } finally {
        // 等待用户查看结果
        if (browser) {
            console.log('\n🔄 浏览器将在10秒后自动关闭...');
            await page.waitForTimeout(10000);
            console.log('👋 正在关闭浏览器...');
            await browser.close();
            console.log('✅ 浏览器已关闭');
        }
    }
}


// 运行提取器
extractNotes().catch(err => {
    console.error('程序执行出错:', err);
    process.exit(1);
});