import asyncio
import json
import os
import sys
import time
from datetime import datetime

from playwright.async_api import async_playwright

# 日志文件路径
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"执行日志_{datetime.now().isoformat().replace(':', '-').replace('.', '-')}.txt")

# 使用专门的日志函数，不替换原始print函数
# 保留原始print行为，同时使用log_info/log_error/log_warn记录日志到文件

def log_error(*args, **kwargs):
    log_message = '[ERROR] ' + ' '.join(str(arg) for arg in args)
    with open(log_file_path, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')
    print('[ERROR]', *args, **kwargs)

def log_warn(*args, **kwargs):
    log_message = '[WARN] ' + ' '.join(str(arg) for arg in args)
    with open(log_file_path, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')
    print('[WARN]', *args, **kwargs)

def log_info(*args, **kwargs):
    log_message = '[INFO] ' + ' '.join(str(arg) for arg in args)
    with open(log_file_path, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')
    print('[INFO]', *args, **kwargs)

print(f'🔍 日志将同时保存到: {log_file_path}')

# 确保导出目录存在
export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '笔记导出')
if not os.path.exists(export_dir):
    os.makedirs(export_dir, exist_ok=True)

# 生成带时间戳的文件名
def generate_file_name(prefix='日记'):
    timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
    return os.path.join(export_dir, f'有道云笔记_{prefix}_{timestamp}.txt')

# 主提取函数
async def extract_notes():
    print('🚀 开始有道云笔记日记提取...')
    print('==================================')

    browser = None
    context = None
    page = None
    cookie_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.json')
    cookies = None

    try:
        # 启动浏览器
        print('🔧 启动浏览器...')
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=100,
                args=['--start-maximized']
            )

            # 创建上下文
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 880},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
            )
            
            # 尝试加载保存的cookies
            if os.path.exists(cookie_path):
                try:
                    log_info('🍪 尝试加载保存的cookie...')
                    with open(cookie_path, 'r', encoding='utf-8') as f:
                        cookies = json.load(f)
                    await context.add_cookies(cookies)
                    log_info('✅ Cookie加载成功')
                except Exception as err:
                    log_warn(f'⚠️ Cookie加载失败: {err}')
            else:
                log_info('ℹ️  Cookie文件不存在，将在登录后创建')

            # 创建新页面
            page = await context.new_page()

            # 导航到有道云笔记网页版
            print('🌐 导航到有道云笔记...')
            await page.goto('https://note.youdao.com/web/')
            print('✅ 已打开有道云笔记网页版')

            # 等待一段时间让页面加载
            await page.wait_for_timeout(3000)

            if cookies is None:
                # 等待用户登录和导航到日记文件夹
                print('\n📝 请按照以下步骤操作:')
                print('1. 在打开的浏览器窗口中完成登录')
                print('2. 成功登录后，手动导航到"日记"文件夹')
                print('3. 确保所有日记条目都显示在页面上')
                print('\n⏳ 请等待40秒完成上述操作...')
                # 等待40秒让用户完成登录和导航
                print('正在等待用户登录...')
                await page.wait_for_timeout(40000)
                # 登录成功后保存cookies
                try:
                    cookies = await context.cookies()
                    with open(cookie_path, 'w', encoding='utf-8') as f:
                        json.dump(cookies, f, ensure_ascii=False, indent=2)
                    print('✅ Cookie已保存，下次运行将自动登录')
                except Exception as err:
                    print(f'❌ Cookie保存失败: {err}')

            else:
                print('✅ 检测到已登录状态，跳过手动登录步骤')
                # 给已登录的页面一些加载时间
                await page.wait_for_timeout(10000)

            # 检查当前页面状态
            current_url = page.url
            page_title = await page.title()
            print(f'\n📊 页面状态检查:')
            print(f'  - 当前URL: {current_url}')
            print(f'  - 页面标题: {page_title}')

            # 尝试检查是否在日记页面
            has_notes = await page.evaluate('''() => {
                const diaryElements = document.querySelectorAll(
                    '.note-item, .list-item, [class*="diary"], [class*="journal"]'
                );
                return diaryElements.length > 0;
            }''')

            if not has_notes:
                print('⚠️  警告: 可能不在日记页面，继续尝试提取...')
            else:
                print('✅ 检测到笔记元素，继续提取...')

            # 一、添加页面滚动逻辑以确保内容完全加载
            print('\n🔄 正在滚动页面加载更多内容...')
            scroll_iterations = 10
            unique_contents = set()
            no_update_count = 0
            MAX_NO_UPDATES = 3

            for i in range(scroll_iterations):
                # 改进的滚动策略：先到底部，再回到顶部，再到底部，增加触发加载的概率
                scroll_result = await page.evaluate('''() => {
                    const scrollableContainer = document.querySelector('.list-bd.topNameTag');
                    if (scrollableContainer) {
                        scrollableContainer.scrollTop = scrollableContainer.scrollHeight;
                        return '⏳ 成功获取可滚动容器并滚动';
                    } else {
                        return '❌ 未找到可滚动容器';
                    }
                }''')
                print(scroll_result)

                # 增加等待时间，确保内容充分加载
                await page.wait_for_timeout(1000)

            print(f'✅ 页面滚动完成，已加载内容样本数: {len(unique_contents)}')

            # 二、逐一点击页面中所有笔记
            list_items = await page.locator('.list-bd.topNameTag li.list-li.file-item').all()
            print(f'✅ 找到 {len(list_items)} 个符合条件的 li 元素')
            output_values = []
            notes_content = ""
            processed_count = 0
            total_content_length = 0

            for item in list_items:
                print('---')
                print('🔸 准备点击一个 li 元素')
                # 1. 点击这个 li
                await item.click()
                print('✅ 已点击一个 li')
                # 增加等待时间，确保内容充分加载
                await page.wait_for_timeout(1000)

                # 2. 等待 iframe 加载 - 尝试多种可能的iframe选择器
                iframe_found = False
                iframe_selectors = [
                    '#bulb-editor',
                    'iframe[id*="editor"]',
                    'iframe[src*="editor"]',
                    'iframe:nth-child(1)',
                    'iframe'
                ]
                
                iframe_el = None
                for iframe_selector in iframe_selectors:
                    try:
                        print(f'🔍 尝试用选择器 "{iframe_selector}" 查找iframe...')
                        iframe_el = await page.locator(iframe_selector).first.element_handle(timeout=3000)
                        if iframe_el:
                            iframe_found = True
                            print(f'✅ 成功找到iframe: {iframe_selector}')
                            break
                    except:
                        continue
                        
                if not iframe_found:
                    print('❌ 未找到任何iframe')
                    output_values.append('未找到 iframe')
                    continue
                
                # 3. 获取 iframe 的 frame 对象
                frame = await iframe_el.content_frame()
                if not frame:
                    print('❌ 无法获取 iframe 的 contentFrame')
                    output_values.append('未获取到 iframe 上下文')
                    continue
                
                try:
                    # 4. 等待 iframe 内的输入框出现 - 增加超时时间并尝试多个可能的选择器
                    found = False
                    selectors_to_try = [
                        'pre.top-title-placeholder',
                        'h1',
                        'h2',
                        'div.title',
                        'span.title'
                    ]
                    
                    for selector in selectors_to_try:
                        try:
                            await frame.wait_for_selector(selector, timeout=8000)
                            found = True
                            break
                        except:
                            continue
                    
                    # 5. 获取标题
                    try:
                        if found:
                            pre_el = await frame.locator(selector).first.element_handle()
                        else:
                            # 尝试获取任何可见的标题元素
                            pre_el = await frame.locator('h1, h2, pre, div.title, span.title').first.element_handle(timeout=3000)
                    except:
                        pre_el = None
                    if pre_el:
                        val = await pre_el.text_content()
                        print(f'📝 获取到的输入框值: {val}')
                        notes_content += f'###标题###[{val}] \n\n'
                        processed_count += 1
                        output_values.append(val)
                    else:
                        print('❌ 在 iframe 中未找到 input 元素')
                        output_values.append('未找到输入框（iframe内未找到）')
                    
                    # 6. 找到正文所有段落 div
                    # 定义可能的选择器（按优先级排序）
                    selectors = [
                        'div[data-block-type="paragraph"].css-1xgc5oj',
                        'span.css-wc3k03',
                        'div.css-1eawncy > span'
                    ]
                    paragraphs = []
                    for selector in selectors:
                        paragraphs = await frame.locator(selector).all()
                        if len(paragraphs) > 0:
                            print(f'✅ 使用选择器 "{selector}" 找到 {len(paragraphs)} 个段落')
                            break
                        print(f'❌ 使用选择器 "{selector}" 未找到段落')
                    
                    if len(paragraphs) == 0:
                        print('❌ 所有选择器均未找到段落')
                    
                    all_text_parts = []
                    for para in paragraphs:
                        # 查找子元素
                        try:
                            span_wrapper = await para.locator('span[data-bulb-node-id]').first.element_handle()
                            if span_wrapper:
                                text = await span_wrapper.text_content()
                                try:
                                    text_span = await span_wrapper.locator('span').first.element_handle()
                                    # 如果最内层span包含文本，就用最内层span的文本
                                    if text_span:
                                        text = await text_span.text_content()
                                except:
                                    pass  # 如果没有找到text_span，就使用span_wrapper的文本
                                trimmed = text.strip() if text else ''
                                if trimmed:
                                    all_text_parts.append(trimmed)
                        except:
                            pass  # 忽略无法处理的段落
                    
                    combined_text = '\n\n'.join(all_text_parts)
                    print(f'🔗 拼接后的全文内容:\n{combined_text}')
                    notes_content += combined_text + '\n\n'
                    
                except Exception as err:
                    print(f'❌ 在 iframe 中等待输入框超时或出错：{err}')
                    output_values.append('未找到输入框（iframe内等待超时）')
            
            print(f'🎉 所有操作完成，获取的输入框值列表: {output_values}')

            page_text = notes_content
            # 获取页面文本内容 - 增强版
            print('\n📋 获取页面文本...')
            start_time = time.time()

            end_time = time.time()
            print(f'页面文本获取耗时: {end_time - start_time:.2f} 秒')
            total_content_length = len(page_text)
            print(f'📊 页面文本长度: {total_content_length:,} 字符')

            # 给内容提取一个预热过程，确保所有内容都已加载
            await page.wait_for_timeout(5000)

            # 统计信息
            print(f'   - 原始文本行数: {len(page_text.splitlines())}')

            # 准备输出内容
            all_notes_content = '# 有道云笔记 - 日记内容汇总\n\n'
            all_notes_content += f'导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n'
            all_notes_content += f'导出条目数: {processed_count}\n\n'
            all_notes_content += '==================================\n\n'
            all_notes_content += page_text + '\n\n'

            # 保存提取的内容
            if len(all_notes_content) > 100:  # 确保有实际内容
                output_file = generate_file_name('日记')
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(all_notes_content)

                # 最终统计信息
                print('\n🎉 提取完成！')
                print('==================================')
                print(f'✅ 成功提取 {processed_count} 个日记条目')
                avg_length = round(total_content_length / processed_count) if processed_count > 0 else 0
                print(f'📊 平均每个条目内容长度: {avg_length} 字符')
                print(f'📄 输出文件大小: {round(len(all_notes_content) / 1024)} KB')
                print(f'📂 内容已保存到: {output_file}')
                print('==================================')
            else:
                print('\n❌ 未能提取到有效内容')

                # 当没有提取到内容时，尝试替代方法
                print('\n🔄 尝试替代提取方法...')
                try:
                    print(f'获取到页面文本内容 (长度: {len(page_text)})')
                    output_file = generate_file_name('日记_替代方法')
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(f'# 页面文本内容\n\n{page_text[:10000]}')
                    print(f'📄 替代内容已保存到: {output_file}')
                except Exception as e:
                    log_error(f'❌ 替代方法也失败: {e}')

    except Exception as error:
        import traceback
        log_error('\n❌ 发生错误: ' + str(error))
        log_error('错误类型: ' + str(type(error).__name__))
        log_error('错误位置: ' + str(traceback.format_exc()))

        # 尝试获取页面文本作为备选
        try:
            if page and not page.is_closed():
                print('🔄 尝试获取页面文本作为备选...')
                page_text = await page.evaluate('() => document.body.innerText')
                output_file = generate_file_name('日记_替代方法')
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(page_text)
                print(f'📄 备选文本已保存到: {output_file}')
            else:
                print('🔄 页面已关闭，无法获取备选文本')
        except Exception as alt_error:
            log_error(f'❌ 保存备选文本失败: {alt_error}')
    finally:
        # 等待用户查看结果
        try:
            if browser:
                print('\n🔄 浏览器将在10秒后自动关闭...')
                if page and not page.is_closed():
                    await page.wait_for_timeout(10000)
                print('👋 正在关闭浏览器...')
                await browser.close()
                print('✅ 浏览器已关闭')
        except Exception as close_error:
            log_error(f'❌ 关闭浏览器时出错: {close_error}')

# 运行提取器
async def main():
    await extract_notes()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n用户中断了程序')
    except Exception as e:
        log_error(f'程序执行出错: {e}')
        sys.exit(1)