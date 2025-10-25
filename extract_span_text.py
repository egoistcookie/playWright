import asyncio
from playwright.async_api import async_playwright
import os

async def extract_span_texts():
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建HTML文件的绝对路径
    html_file_path = os.path.join(current_dir, '有道云-网站-片段节选.html')
    # 将路径转换为file://协议格式
    file_url = f'file:///{html_file_path.replace("\\", "/")}'
    
    print(f'📄 要加载的HTML文件路径: {html_file_path}')
    print(f'🌐 转换后的file URL: {file_url}')
    
    async with async_playwright() as playwright:
        # 启动浏览器（设置为非无头模式以便查看执行过程）
        browser = await playwright.chromium.launch(
            headless=False,
            slow_mo=100
        )
        
        # 创建新页面
        page = await browser.new_page()
        
        try:
            # 加载HTML文件
            print('🔄 正在加载HTML文件...')
            await page.goto(file_url, wait_until='domcontentloaded')
            print('✅ HTML文件加载完成')
            
            # 等待一下确保DOM完全渲染
            await page.wait_for_timeout(2000)
            
            # 方法1: 获取所有带有data-bulb-node-id属性的span元素
            print('\n🔍 方法1: 获取所有带有data-bulb-node-id属性的span元素')
            span_elements = await page.locator('span[data-bulb-node-id]').all()
            print(f'📊 找到 {len(span_elements)} 个带有data-bulb-node-id属性的span元素')
            
            for i, span in enumerate(span_elements):
                # 获取节点ID
                node_id = await span.get_attribute('data-bulb-node-id')
                # 获取文本内容
                text = await span.text_content()
                # 清理文本
                trimmed_text = text.strip() if text else ''
                
                print(f'\n📋 Span #{i+1}:')
                print(f'   - Node ID: {node_id}')
                print(f'   - 原始文本: "{text}"')
                print(f'   - 清理后文本: "{trimmed_text}"')
            
            # 方法2: 获取所有嵌套的span元素文本
            print('\n🔍 方法2: 获取所有嵌套的span元素文本')
            # 定位到li元素
            li_elements = await page.locator('li.css-55830i').all()
            
            if len(li_elements) > 0:
                li_element = li_elements[0]
                # 获取li下所有的span元素
                all_spans_in_li = await li_element.locator('span').all()
                print(f'📊 在li元素下找到 {len(all_spans_in_li)} 个span元素')
                
                for i, span in enumerate(all_spans_in_li):
                    # 获取文本内容
                    text = await span.text_content()
                    # 清理文本
                    trimmed_text = text.strip() if text else ''
                    # 获取类名
                    class_name = await span.get_attribute('class')
                    
                    print(f'\n📋 嵌套Span #{i+1}:')
                    print(f'   - 类名: {class_name}')
                    print(f'   - 清理后文本: "{trimmed_text}"')
                    # 只有当文本非空时才输出，避免输出空文本
                    if trimmed_text:
                        print(f'   - 有意义的文本: "{trimmed_text}"')
            
            # 方法3: 获取特定嵌套结构的文本（用于获取链接文本）
            print('\n🔍 方法3: 获取特定嵌套结构的文本')
            link_spans = await page.locator('a.css-1lw0h1r span.underline.color').all()
            print(f'📊 找到 {len(link_spans)} 个链接文本span元素')
            
            for i, span in enumerate(link_spans):
                text = await span.text_content()
                trimmed_text = text.strip() if text else ''
                print(f'\n📋 链接文本 #{i+1}: "{trimmed_text}"')
            
            # 方法4: 获取所有有实际文本内容的span元素
            print('\n🔍 方法4: 获取所有有实际文本内容的span元素')
            # 使用evaluate来筛选有非空文本的span
            meaningful_spans = await page.evaluate('''() => {
                const spans = document.querySelectorAll('span');
                const result = [];
                
                spans.forEach(span => {
                    const text = span.textContent?.trim();
                    if (text && text.length > 0) {
                        result.push({
                            text: text,
                            class: span.className,
                            nodeId: span.getAttribute('data-bulb-node-id')
                        });
                    }
                });
                
                return result;
            }''')
            
            print(f'📊 找到 {len(meaningful_spans)} 个有实际文本内容的span元素')
            for i, span_data in enumerate(meaningful_spans):
                print(f'\n📋 有效文本Span #{i+1}:')
                print(f'   - 文本: "{span_data["text"]}"')
                print(f'   - 类名: {span_data["class"]}')
                print(f'   - Node ID: {span_data["nodeId"]}')
            
        except Exception as e:
            print(f'❌ 发生错误: {e}')
        finally:
            # 等待用户查看结果
            print('\n⏳ 按Enter键关闭浏览器...')
            await asyncio.sleep(5)
            # 关闭浏览器
            await browser.close()
            print('✅ 浏览器已关闭')

# 运行主函数
if __name__ == '__main__':
    print('🚀 开始提取HTML中的span文本...')
    print('==================================')
    asyncio.run(extract_span_texts())
    print('==================================')
    print('🎉 文本提取完成！')