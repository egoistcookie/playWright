import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# 导入Playwright库
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page, Frame

# 自定义日志类 - 重定向打印输出到文件
class Logger:
    _instance = None
    
    def __new__(cls):
        # 单例模式，避免创建多个日志器导致重复输出
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 防止重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # 创建日志文件路径
        timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
        self.log_file_path = Path(__file__).parent / f'执行日志_{timestamp}.txt'
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        # 打开日志文件
        self.log_file = open(self.log_file_path, 'w', encoding='utf-8')
        self._initialized = True
        self._printed_log_path = False
    
    def write(self, message):
        # 写入到控制台
        self.original_stdout.write(message)
        self.original_stdout.flush()
        # 写入到文件
        self.log_file.write(message)
        self.log_file.flush()
    
    def error_write(self, message):
        # 错误信息特殊处理
        error_message = f'[ERROR] {message}'
        self.original_stderr.write(error_message)
        self.original_stderr.flush()
        self.log_file.write(error_message)
        self.log_file.flush()
    
    def print_log_path(self):
        # 只打印一次日志路径
        if not self._printed_log_path:
            # 使用old_print直接输出到控制台
            import builtins
            builtins.print(f'🔍 日志将同时保存到: {self.log_file_path}')
            self._printed_log_path = True
            # 写入到日志文件
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(f'🔍 日志将同时保存到: {self.log_file_path}\n')
    
    def __del__(self):
        # 关闭文件
        if hasattr(self, 'log_file') and not self.log_file.closed:
            self.log_file.close()

# 先保存原始print
old_print = print

# 重定向标准输出
def print(*args, **kwargs):
    # 将参数转换为字符串
    message = ' '.join(str(arg) for arg in args)
    # 写入日志
    if hasattr(logger, 'log_file_path'):
        with open(logger.log_file_path, 'a', encoding='utf-8') as f:
            f.write(message + '\n')
    # 调用原始print
    old_print(*args, **kwargs)

# 创建日志记录器
logger = Logger()
logger.print_log_path()  # 打印日志路径

# 确保导出目录存在
def ensure_export_dir() -> Path:
    export_dir = Path(__file__).parent / '笔记导出'
    if not export_dir.exists():
        export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir

# 生成带时间戳的文件名
def generate_file_name(prefix: str = '日记') -> Path:
    export_dir = ensure_export_dir()
    timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
    return export_dir / f'有道云笔记_{prefix}_{timestamp}.txt'

# 主提取函数
async def extract_notes():
    print('🚀 开始有道云笔记日记提取...')
    print('==================================')

    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None
    cookie_path = Path(__file__).parent / 'cookies.json'

    try:
        # 启动Playwright
        async with async_playwright() as playwright:
            # 启动浏览器
            print('🔧 启动浏览器...')
            browser = await playwright.chromium.launch(
                headless=False,
                slow_mo=100,
                args=['--start-maximized']
            )

            # 创建上下文
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 880},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
            )
            
            cookies = None
            # 尝试加载保存的cookies
            if cookie_path.exists():
                try:
                    print('🍪 尝试加载保存的cookie...')
                    with open(cookie_path, 'r', encoding='utf-8') as f:
                        cookies = json.load(f)
                    await context.add_cookies(cookies)
                    print('✅ Cookie加载成功')
                except Exception as err:
                    print(f'⚠️ Cookie加载失败: {err}')
            else:
                print('ℹ️  Cookie文件不存在，将在登录后创建')

            # 创建新页面
            page = await context.new_page()

            # 导航到有道云笔记网页版
            print('🌐 导航到有道云笔记...')
            # 增加超时时间到60秒，并使用wait_until='domcontentloaded'以更早加载
            await page.goto('https://note.youdao.com/web/', timeout=60000, wait_until='domcontentloaded')
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
                        json.dump(cookies, f, indent=2, ensure_ascii=False)
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
                # 改进的滚动策略：先到底部，再回到顶部，再到底部
                result = await page.evaluate('''() => {
                    const scrollableContainer = document.querySelector('.list-bd.topNameTag');
                    if (scrollableContainer) {
                        scrollableContainer.scrollTop = scrollableContainer.scrollHeight;
                        return '⏳ 成功获取可滚动容器并滚动';
                    } else {
                        return '❌ 未找到可滚动容器';
                    }
                }''')
                print(result)

                # 增加等待时间，确保内容充分加载
                await page.wait_for_timeout(1000)

            print(f'✅ 页面滚动完成，已加载内容样本数: {len(unique_contents)}')

            # 二、逐一点击页面中所有笔记
            list_items = await page.locator('.list-bd.topNameTag li.list-li.file-item').all()
            print(f'✅ 找到 {len(list_items)} 个符合条件的 li 元素')
            output_values = []
            content = ""
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

                # 2. 等待 iframe 加载
                iframe_el = await page.query_selector('#bulb-editor')
                if not iframe_el:
                    print('❌ 未找到 iframe（#bulb-editor）')
                    output_values.append('未找到 iframe')
                    continue
                
                # 3. 获取 iframe 的 frame 对象
                frame = await iframe_el.content_frame()
                if not frame:
                    print('❌ 无法获取 iframe 的 contentFrame')
                    output_values.append('未获取到 iframe 上下文')
                    continue
                
                try:
                    # 4. 等待 iframe 内的输入框出现
                    await page.wait_for_selector('pre.top-title-placeholder', timeout=5000)

                    # 5. 获取标题
                    pre_el = await page.query_selector('pre.top-title-placeholder')
                    if pre_el:
                        val = await pre_el.text_content()
                        print(f'📝 获取到的输入框值: {val}')
                        content += f'###标题###[{val}] \n\n'
                        processed_count += 1
                        output_values.append(val)
                    else:
                        print('❌ 在 iframe 中未找到 input 元素')
                        output_values.append('未找到输入框（iframe内未找到）')
                    
                    # 6. 找到正文所有段落
                    # 定义可能的选择器（按优先级排序）
                    SELECTORS = [
                        'div[data-block-type="paragraph"].css-1xgc5oj',
                        'span.css-wc3k03',
                        'div.css-1eawncy > span'
                    ]
                    
                    paragraphs = []
                    for selector in SELECTORS:
                        paragraphs = await frame.locator(selector).all()
                        if len(paragraphs) > 0:
                            print(f'✅ 使用选择器 "{selector}" 找到 {len(paragraphs)} 个段落')
                            break
                        print(f'❌ 使用选择器 "{selector}" 未找到段落')
                    
                    if len(paragraphs) == 0:
                        print('❌ 所有选择器均未找到段落')
                    
                    all_text_parts = []
                    for para in paragraphs:
                        try:
                            # 使用count()检查元素是否存在
                            span_wrappers = para.locator('span[data-bulb-node-id]')
                            count = await span_wrappers.count()
                            if count > 0:
                                # 获取第一个匹配的元素
                                span_wrapper = span_wrappers.first
                                text = await span_wrapper.text_content()
                                # 检查是否有嵌套的span
                                text_spans = span_wrapper.locator('span')
                                if await text_spans.count() > 0:
                                    inner_text = await text_spans.first.text_content()
                                    if inner_text and inner_text.strip():
                                        text = inner_text
                                trimmed = text.strip() if text else ''
                                if trimmed:
                                    all_text_parts.append(trimmed)
                            else:
                                # 如果没有找到指定的span，尝试获取段落本身的文本
                                para_text = await para.text_content()
                                trimmed = para_text.strip() if para_text else ''
                                if trimmed:
                                    all_text_parts.append(trimmed)
                        except Exception as e:
                            print(f'⚠️  处理段落时出错: {e}')
                            # 出错时尝试获取段落文本作为后备
                            try:
                                para_text = await para.text_content()
                                trimmed = para_text.strip() if para_text else ''
                                if trimmed:
                                    all_text_parts.append(trimmed)
                            except:
                                pass
                    
                    combined_text = '\n\n'.join(all_text_parts)
                    print(f'🔗 拼接后的全文内容:\n {combined_text}')
                    content += combined_text + '\n\n'
                    
                except Exception as err:
                    print(f'❌ 在 iframe 中等待输入框超时或出错：{err}')
                    output_values.append('未找到输入框（iframe内等待超时）')
            
            print(f'🎉 所有操作完成，获取的输入框值列表: {output_values}')

            page_text = content
            # 获取页面文本内容
            print('\n📋 获取页面文本...')
            import time
            start_time = time.time()

            end_time = time.time()
            print(f'页面文本获取耗时: {end_time - start_time:.2f} 秒')
            total_content_length = len(page_text)
            print(f'📊 页面文本长度: {total_content_length:,} 字符')

            # 给内容提取一个预热过程，确保所有内容都已加载
            await page.wait_for_timeout(5000)

            # 统计信息
            print(f'   - 原始文本行数: {len(page_text.split("\n"))}')

            # 准备输出内容
            all_notes_content = '# 有道云笔记 - 日记内容汇总\n\n'
            all_notes_content += f'导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n'
            all_notes_content += f'导出条目数: {processed_count}\n\n'
            all_notes_content += '==================================\n\n'
            all_notes_content += page_text + '\n\n'

            # 保存提取的内容
            if len(all_notes_content) > 100:
                output_file = generate_file_name('日记')
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(all_notes_content)

                # 最终统计信息
                print('\n🎉 提取完成！')
                print('==================================')
                print(f'✅ 成功提取 {processed_count} 个日记条目')
                if processed_count > 0:
                    print(f'📊 平均每个条目内容长度: {total_content_length // processed_count} 字符')
                print(f'📄 输出文件大小: {len(all_notes_content) // 1024} KB')
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
                    print(f'❌ 替代方法也失败: {e}')

    except Exception as error:
        print(f'\n❌ 发生错误: {error}')

        # 尝试获取页面文本作为备选
        try:
            if page:
                print('🔄 尝试获取页面文本作为备选...')
                page_text = await page.evaluate('() => document.body.innerText')
                output_file = generate_file_name('日记_替代方法')
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(page_text)
                print(f'📄 备选文本已保存到: {output_file}')
        except Exception as alt_error:
            print(f'❌ 保存备选文本失败: {alt_error}')
    finally:
        # 等待用户查看结果 - 改进版：减少等待时间并增加健壮性
        try:
            if browser and browser.is_connected():
                print('\n🔄 浏览器将在10秒后自动关闭...')
                try:
                    # 减少等待时间，避免长时间占用资源
                    if page:
                        await page.wait_for_timeout(10000)
                except:
                    # 忽略等待过程中的错误
                    pass
                
                print('👋 正在关闭浏览器...')
                await browser.close()
                print('✅ 浏览器已关闭')
        except Exception as close_error:
            print(f'⚠️  浏览器关闭过程中出错: {close_error}')
            print('💡 提示：浏览器可能已经被手动关闭')

# 运行主函数
if __name__ == '__main__':
    try:
        asyncio.run(extract_notes())
    except Exception as err:
        print(f'程序执行出错: {err}')
        sys.exit(1)