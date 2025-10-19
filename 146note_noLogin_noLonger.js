const playwright = require('playwright');
const fs = require('fs');
const path = require('path');

// 确保导出目录存在
const exportDir = path.join(__dirname, '笔记导出');
if (!fs.existsSync(exportDir)) {
    fs.mkdirSync(exportDir, { recursive: true });
}

// 生成带时间戳的文件名
function generateFileName(prefix = '日记') {
    const timestamp = new Date().toISOString().replace(/:/g, '-').replace(/\./g, '-');
    return path.join(exportDir, `点击提取_${prefix}_${timestamp}.txt`);
}

// 文本相似度计算
function calculateSimilarity(str1, str2) {
    if (str1 === str2) return 1.0;
    if (str1.length === 0 || str2.length === 0) return 0.0;
    
    const longer = str1.length > str2.length ? str1 : str2;
    const shorter = str1.length > str2.length ? str2 : str1;
    
    const longerLength = longer.length;
    if (longerLength === 0) return 1.0;
    
    const distance = getEditDistance(longer, shorter);
    return (longerLength - distance) / parseFloat(longerLength);
}

// 计算编辑距离
function getEditDistance(str1, str2) {
    const matrix = Array(str1.length + 1).fill().map(() => Array(str2.length + 1).fill(0));
    
    for (let i = 0; i <= str1.length; i++) matrix[i][0] = i;
    for (let j = 0; j <= str2.length; j++) matrix[0][j] = j;
    
    for (let i = 1; i <= str1.length; i++) {
        for (let j = 1; j <= str2.length; j++) {
            const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
            matrix[i][j] = Math.min(
                matrix[i - 1][j] + 1,       // 删除
                matrix[i][j - 1] + 1,       // 插入
                matrix[i - 1][j - 1] + cost // 替换
            );
        }
    }
    
    return matrix[str1.length][str2.length];
}

// 移除重复段落
function removeDuplicateParagraphs(content) {
    const paragraphs = content.split(/\n\s*\n/).map(p => p.trim()).filter(p => p.length > 0);
    const uniqueParagraphs = [];
    
    for (const paragraph of paragraphs) {
        let isDuplicate = false;
        
        for (const unique of uniqueParagraphs) {
            if (calculateSimilarity(paragraph, unique) > 0.9) {
                isDuplicate = true;
                break;
            }
        }
        
        if (!isDuplicate) {
            uniqueParagraphs.push(paragraph);
        }
    }
    
    return uniqueParagraphs.join('\n\n');
}

// 过滤有道云笔记内容，移除UI元素和系统文本
function filterYoudaoContent(content) {
    // 移除常见的UI元素文本
    const navigationKeywords = [
        '我的文件夹', '最近', '工作', '生活', '学习', '收藏', '回收站',
        '新建笔记', '导入', '导出', '分享', '协作', '设置',
        '编辑', '查看', '格式', '插入', '帮助',
        '网易', '有道云笔记', '用户协议', '隐私政策',
        '功能介绍', '使用教程', '帮助中心', '意见反馈'
    ];
    
    let filteredContent = content;
    
    // 移除导航关键词相关内容
    for (const keyword of navigationKeywords) {
        const regex = new RegExp(`.*${keyword}.*\\n?`, 'gi');
        filteredContent = filteredContent.replace(regex, '');
    }
    
    // 移除空白行和多余空格
    filteredContent = filteredContent
        .replace(/\n\s*\n\s*\n/g, '\n\n') // 替换多个空行为两个换行
        .replace(/\s+/g, ' ') // 替换连续空格为单个空格
        .replace(/^\s+|\s+$/g, ''); // 移除首尾空格
    
    // 移除HTML/JS相关内容
    filteredContent = filteredContent.replace(/<[^>]*>/g, '');
    filteredContent = filteredContent.replace(/\{\{[^}]*\}\}/g, '');
    
    // 移除可能的代码片段
    filteredContent = filteredContent.replace(/function\s+\w+\s*\([^)]*\)\s*{[^}]*}/g, '');
    filteredContent = filteredContent.replace(/const\s+\w+\s*=\s*[^;]*;/g, '');
    
    return filteredContent;
}

// 提取真实的笔记内容
function extractTrueNoteContent(content) {
    // 尝试识别日记格式的标题行（如 2023-04-01 或 2023/04/01 格式）
    const datePattern = /^(\d{4}[-/]\d{2}[-/]\d{2}|\d{8}|\d{4}年\d{1,2}月\d{1,2}日)/;
    const lines = content.split('\n');
    
    let noteBlocks = [];
    let inNoteBlock = false;
    let currentBlock = [];
    let blockTextCount = 0;
    
    for (const line of lines) {
        const trimmedLine = line.trim();
        
        // 跳过空行
        if (trimmedLine.length === 0) {
            continue;
        }
        
        // 检查是否是日记标题行
        if (datePattern.test(trimmedLine) || trimmedLine.startsWith('#')) {
            // 如果已经在笔记块中，保存之前的块
            if (inNoteBlock && blockTextCount > 10) {
                noteBlocks.push(currentBlock.join('\n'));
            }
            
            // 开始新的笔记块
            inNoteBlock = true;
            currentBlock = [trimmedLine];
            blockTextCount = trimmedLine.length;
        } else if (inNoteBlock) {
            // 添加到当前笔记块
            currentBlock.push(trimmedLine);
            blockTextCount += trimmedLine.length;
        }
    }
    
    // 保存最后一个笔记块
    if (inNoteBlock && blockTextCount > 10) {
        noteBlocks.push(currentBlock.join('\n'));
    }
    
    // 如果没有识别到任何笔记块，返回清理后的原始内容
    if (noteBlocks.length === 0) {
        return content;
    }
    
    return noteBlocks.join('\n\n');
}

// 检查内容是否有效（不是系统文本或HTML代码）
function isValidContent(content) {
    if (!content || content.trim().length < 10) return false;
    
    // 检查是否包含过多系统相关词汇
    const systemKeywords = ['function', 'window', 'document', 'console', 'Object', 'Array', 'JSON'];
    const keywordCount = systemKeywords.filter(keyword => 
        content.toLowerCase().includes(keyword.toLowerCase())
    ).length;
    
    // 如果包含超过3个系统关键词，可能是系统文本
    if (keywordCount > 3) return false;
    
    // 检查是否主要包含HTML标签或JavaScript代码模式
    if (content.match(/<[^>]*>/g)?.length > 10) return false;
    if (content.match(/[{}()\[\]]/g)?.length > content.length * 0.1) return false;
    
    return true;
}

// 从页面文本中解析日记条目的函数
function parseDiaryEntriesFromPageText(pageText) {
    // 分割文本并提取日记条目
    const lines = pageText.split('\n');
    const entries = [];
    let currentEntry = null;
    let inEntryContent = false;
    
    // 无效标题关键词 - 更精确的过滤
    const invalidTitles = [
        '总共', '项', '我的文件夹', '工作', '每周回顾',
        '我的资源', '写作', '行动', '学习', '杂事', '照片',
        '与我分享', '加星', '标签', '回收站', '云协作', '官网',
        '客户端下载', '新建', '到期', '页面文本内容',
        '导入', '导出', '分享', '协作', '设置'
    ];
    
    // 扩展日期模式正则表达式，增加更多可能的格式
    const datePatterns = [
        /^\d{8}[-–]\S+/, // 20250812-标题格式
        /^\d{4}年\d{1,2}月\d{1,2}日[-–]\S+/, // 2025年8月12日-标题格式
        /^20\d{2}\d{2}\d{2}[-–]\S+/, // 20250812-标题格式（无分隔符）
        /^\d{4}[-/]\d{1,2}[-/]\d{1,2}[-–]\S+/, // 2025-08-12-标题格式
        /^201[7-9]\d{5}[-–]\S+/, // 特别关注2017-2019年的笔记，如20171210-
        /^202[0-5]\d{5}[-–]\S+/  // 特别关注2020-2025年的笔记
    ];
    
    // 文件信息模式（修改日期和文件大小）
    const fileInfoPattern = /^202\d\.\d{1,2}\.\d{1,2}\s+[\d.]+\s+[KMG]B$/;
    
    // 清理内容中的元数据模式 - 超级加强版
    const metadataPattern = /202\d\.\d{1,2}\.\d{1,2}\s+[\d.]+\s+[KMG]B/g;
    const metadataPatternAlt = /\s*\d{4}\.\d{2}\.\d{2}\s+\d+(?:\.\d+)?\s*[KMG]?B\s*/g;
    const dateSizePattern = /\s*\d{4}\.\d{2}\.\d{2}\s+\d+(?:\.\d+)?\s*[KMG]?B$/;
    const extendedMetadataPattern = /\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\s*\d{1,2}:\d{2}(:\d{2})?\s*(\d+[KkMmGg]?[Bb]?)?/gi;
    
    console.log('📋 开始解析页面文本中的日记条目...');
    
    for (const line of lines) {
        const trimmedLine = line.trim();
        
        // 跳过空行和无效行，但更宽松的过滤以避免丢失有效内容
        if (!trimmedLine || 
            (invalidTitles.some(keyword => trimmedLine.includes(keyword)) && 
             !datePatterns.some(pattern => pattern.test(trimmedLine)))) {
            continue;
        }
        
        // 检查是否是文件信息行（修改日期和文件大小）
        if (fileInfoPattern.test(trimmedLine)) {
            // 如果文件信息行紧跟在条目内容后面，说明当前条目结束
            if (currentEntry && currentEntry.content) {
                // 保存当前条目
                entries.push(currentEntry);
                currentEntry = null;
                inEntryContent = false;
            }
            continue;
        }
        
        // 检查是否是日记标题
        const isTitle = datePatterns.some(pattern => pattern.test(trimmedLine));
        
        if (isTitle) {
            // 如果已经在处理一个条目，先保存它
            // 降低内容长度要求，以便捕获更多短内容笔记
            if (currentEntry && currentEntry.content && currentEntry.content.trim().length > 5) {
                entries.push(currentEntry);
            }
            
            // 开始新条目
            currentEntry = {
                title: trimmedLine,
                content: ''
            };
            inEntryContent = true;
        } else if (inEntryContent && currentEntry) {
            // 这是条目的内容部分
            // 清理行中的元数据信息 - 使用多种模式确保完全清理
            let cleanLine = trimmedLine
                .replace(dateSizePattern, '')
                .replace(metadataPatternAlt, '')
                .replace(metadataPattern, '')
                .replace(extendedMetadataPattern, '')
                .trim();
            
            if (currentEntry.content && cleanLine) {
                currentEntry.content += '\n';
            }
            
            if (cleanLine) {
                currentEntry.content += cleanLine;
            }
        }
    }
    
    // 添加最后一个条目
    // 降低内容长度要求，以便捕获更多短内容笔记
    if (currentEntry && currentEntry.content && currentEntry.content.trim().length > 5) {
        // 清理最后一个条目的内容 - 使用多种模式确保完全清理
        currentEntry.content = currentEntry.content
            .replace(dateSizePattern, '')
            .replace(metadataPatternAlt, '')
            .replace(metadataPattern, '')
            .replace(extendedMetadataPattern, '')
            .trim();
        entries.push(currentEntry);
    }
    
    // 增强的去重逻辑 - 使用Map存储，保留内容更完整的版本
    const uniqueEntries = [];
    const titleMap = new Map();
    
    for (const entry of entries) {
        // 最终清理内容 - 使用多种模式确保完全清理
        entry.content = entry.content
            .replace(dateSizePattern, '')
            .replace(metadataPatternAlt, '')
            .replace(metadataPattern, '')
            .replace(extendedMetadataPattern, '')
            .trim();
        
        // 降低内容长度要求，以便捕获更多短内容笔记
        if (entry.content.trim().length > 5) {
            const title = entry.title;
            
            // 如果标题已经存在，比较内容长度，保留较长的
            if (titleMap.has(title)) {
                const existingEntry = titleMap.get(title);
                if (entry.content.length > existingEntry.content.length) {
                    titleMap.set(title, entry);
                }
            } else {
                titleMap.set(title, entry);
            }
        }
    }
    
    // 将Map转换为数组
    titleMap.forEach(entry => {
        uniqueEntries.push(entry);
    });
    
    console.log(`🔍 从页面文本中成功解析出 ${uniqueEntries.length} 个有效日记条目`);
    return uniqueEntries;
}

// 主提取函数
async function extractNotes() {
    console.log('🚀 开始有道云笔记日记提取...');
    console.log('==================================');
    
    let browser = null;
    let context = null;
    let page = null;
    
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
            viewport: { width: 1920, height: 1080 },
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        });
        
        // 创建新页面
        page = await context.newPage();
        
        // 导航到有道云笔记网页版
        console.log('🌐 导航到有道云笔记...');
        await page.goto('https://note.youdao.com/web/');
        console.log('✅ 已打开有道云笔记网页版');
        
        // 等待用户登录和导航到日记文件夹
    console.log('\n📝 请按照以下步骤操作:');
    console.log('1. 在打开的浏览器窗口中完成登录');
    console.log('2. 成功登录后，手动导航到"日记"文件夹');
    console.log('3. 确保所有日记条目都显示在页面上');
    console.log('\n⏳ 请等待60秒完成上述操作...');
    
    // 等待60秒让用户完成登录和导航
    console.log('正在等待用户登录...');
    await page.waitForTimeout(60000);
    
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
        
        // 添加页面滚动逻辑以确保内容完全加载
    console.log('\n🔄 正在滚动页面加载更多内容...');
    const scrollIterations = 40; // 进一步增加滚动次数
    const uniqueContents = new Set(); // 用于检测是否加载了新内容
    let noUpdateCount = 0;
    const MAX_NO_UPDATES = 3; // 连续几次无更新后才停止
    
    for (let i = 0; i < scrollIterations; i++) {
        // 获取当前可见内容，用于检测是否有新内容加载
        const contentLength = await page.evaluate(() => document.body.innerText.length);
        
        // 简单的内容哈希实现
        const contentHash = await page.evaluate(() => {
            const text = document.body.innerText.substring(0, 1000);
            let hash = 0;
            for (let i = 0; i < text.length; i++) {
                hash = ((hash << 5) - hash) + text.charCodeAt(i);
                hash = hash & hash; // Convert to 32bit integer
            }
            return hash;
        });
        
        // 检测内容是否更新
        if (uniqueContents.has(contentHash)) {
            noUpdateCount++;
            if (noUpdateCount >= MAX_NO_UPDATES && i > 10) {
                console.log(`  ⏸️  连续${MAX_NO_UPDATES}次无更新，提前结束滚动 (第${i}次)`);
                break;
            }
            console.log(`  ⏳ 内容未更新 (第${i}次, 连续未更新: ${noUpdateCount}次)`);
        } else {
            noUpdateCount = 0;
            uniqueContents.add(contentHash);
            console.log(`  ✅ 内容已更新 (长度: ${contentLength}字符, 第${i}次滚动)`);
        }
        
        // 改进的滚动策略：先到底部，再回到顶部，再到底部，增加触发加载的概率
        await page.evaluate(() => {
            // 先滚动到底部
            window.scrollTo(0, document.body.scrollHeight);
            
            // 然后滚动到顶部再到底部
            setTimeout(() => {
                window.scrollTo(0, 0);
                setTimeout(() => window.scrollTo(0, document.body.scrollHeight), 500);
            }, 500);
        });
        
        // 增加等待时间，确保内容充分加载
        await page.waitForTimeout(3000);
        
        // 使用更安全的方式来尝试加载更多内容
         try {
             if (i % 5 === 0) { // 降低点击频率
                 // 尝试点击滚动加载更多按钮（如果存在）
                 await page.evaluate(() => {
                     // 查找可能的加载更多按钮
                     const loadMoreButtons = document.querySelectorAll(
                         '.load-more, .loadMore, [class*="load"][class*="more"], [text*="加载"][text*="更多"]'
                     );
                     if (loadMoreButtons.length > 0) {
                         loadMoreButtons[0].click();
                     }
                     
                     // 也尝试点击一些可能触发内容加载的区域
                     const container = document.querySelector('.notes-container, .list-container, .main-content');
                     if (container) {
                         // 模拟用户滚动行为
                         const scrollEvent = new Event('scroll', { bubbles: true });
                         container.dispatchEvent(scrollEvent);
                     }
                 });
                 
                 console.log(`  🔄 触发内容加载机制 (第${i}次)`);
             }
         } catch (e) {
             // 静默忽略错误，继续执行
         }
    }
    
    console.log('✅ 页面滚动完成，已加载内容样本数:', uniqueContents.size);
    
    // 获取页面文本内容 - 增强版
    console.log('\n📋 获取页面文本...');
    console.time('页面文本获取');
    
    // 首先尝试获取所有笔记列表项
    const noteItems = await page.evaluate(() => {
        const items = [];
        // 查找所有可能的笔记项元素
        const noteElements = document.querySelectorAll(
          '.note-item, .list-item, .note-list-item, .file-item, .document-item'
        );
        
        noteElements.forEach(el => {
          const title = el.querySelector(
            '.note-item-title, .list-item-title, .title, .note-title, .file-name'
          )?.innerText || '';
          const content = el.innerText;
          items.push({ title, content });
        });
        return items;
    });
    
    // 增强的页面文本获取逻辑，特别优化长笔记内容获取
      let pageText = await page.evaluate(() => {
          try {
              // 使用多个策略获取完整文本
              let allText = '';
              
              // 策略1: 获取body文本作为基础
              if (document.body) {
                  allText += document.body.innerText + '\n';
              }
              
              // 策略2: 分别获取所有笔记项和笔记内容区域
              const noteContainers = document.querySelectorAll(
                  '.note-item, .list-item, .note-content, .article-content, .note-detail, .note-editor, ' +
                  '.document-content, .content-editor, .prose, .markdown-body'
              );
              
              noteContainers.forEach(container => {
                  try {
                      const text = container.innerText || container.textContent || '';
                      if (text.trim().length > 5) {
                          allText += '\n---NOTE CONTAINER---\n' + text;
                      }
                  } catch (e) {}
              });
              
              // 策略3: 专门处理标题和内容对
              const titles = document.querySelectorAll(
                  '.note-title, .note-item-title, .list-item-title, h1, h2, h3, h4, h5, h6'
              );
              
              titles.forEach(title => {
                  try {
                      const titleText = title.innerText || '';
                      // 检查是否是日记标题格式
                      if (/^\d{8}[-–]|^\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}[-–]/.test(titleText)) {
                          allText += '\n---FOUND DIARY TITLE---\n' + titleText;
                          
                          // 尝试获取标题后的内容
                          let nextEl = title.nextElementSibling;
                          let contentBuffer = [];
                          let count = 0;
                          
                          // 收集接下来的内容，直到遇到下一个标题或达到限制
                          while (nextEl && count < 30) { // 收集最多30个元素
                              const contentText = nextEl.innerText || nextEl.textContent || '';
                              if (contentText.trim()) {
                                  // 检查是否是新的标题，如果是则停止收集
                                  if (/^\d{8}[-–]|^\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}[-–]/.test(contentText)) {
                                      break;
                                  }
                                  contentBuffer.push(contentText);
                              }
                              nextEl = nextEl.nextElementSibling;
                              count++;
                          }
                          
                          if (contentBuffer.length > 0) {
                              allText += '\n' + contentBuffer.join('\n');
                          }
                      }
                  } catch (e) {}
              });
              
              // 策略4: 获取所有段落和文本元素
              const paragraphs = document.querySelectorAll('p, span, div, article, section');
              const longTexts = [];
              
              paragraphs.forEach(para => {
                  try {
                      const text = para.innerText || para.textContent || '';
                      if (text.trim().length > 50) { // 特别收集较长的文本段落
                          longTexts.push(text);
                      }
                  } catch (e) {}
              });
              
              if (longTexts.length > 0) {
                  allText += '\n---LONG PARAGRAPHS---\n' + longTexts.join('\n\n');
              }
              
              return allText;
          } catch (error) {
              console.error('获取页面文本时出错:', error);
              return document.body ? document.body.innerText || '' : '';
          }
      });
    
    console.timeEnd('页面文本获取');
    console.log(`📊 页面文本长度: ${pageText.length.toLocaleString()} 字符`);
    
    // 给内容提取一个预热过程，确保所有内容都已加载
    await page.waitForTimeout(5000);
        
        // 解析日记条目
        console.log('🔍 开始解析日记条目...');
        console.time('条目解析');
        const diaryEntries = parseDiaryEntriesFromPageText(pageText);
        console.timeEnd('条目解析');
        
        // 统计信息
        console.log('📊 解析统计:');
        console.log(`   - 原始文本行数: ${pageText.split('\n').length}`);
        console.log(`   - 解析到条目数: ${diaryEntries.length}`);
        
        // 准备输出内容
        let allNotesContent = '# 有道云笔记 - 日记内容汇总\n\n';
        allNotesContent += `导出时间: ${new Date().toLocaleString('zh-CN')}\n\n`;
        allNotesContent += `导出条目数: ${diaryEntries.length}\n\n`;
        allNotesContent += `==================================\n\n`;
        
        // 格式化日记条目
        let processedCount = 0;
        let totalContentLength = 0;
        
        console.log('📝 生成导出内容...');
        console.time('内容生成');
        
        diaryEntries.forEach((entry, index) => {
            // 清理和优化内容
            let processedContent = filterYoudaoContent(entry.content);
            processedContent = removeDuplicateParagraphs(processedContent);
            
            allNotesContent += `## ${entry.title}\n\n`;
            allNotesContent += processedContent + '\n\n';
            
            if (index < diaryEntries.length - 1) {
                allNotesContent += '---\n\n';
            }
            
            processedCount++;
            totalContentLength += processedContent.length;
            
            // 每处理10个条目显示一次进度
            if (processedCount % 10 === 0) {
                console.log(`✅ 已处理 ${processedCount}/${diaryEntries.length} 个条目`);
            } else {
                console.log(`✅ 已处理: ${entry.title}`);
            }
        });
        
        console.timeEnd('内容生成');
        
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