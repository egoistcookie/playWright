#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分割有道云笔记导出文件，按标题生成单独的txt文件

功能：
    1. 读取有道云笔记导出的汇总文件
    2. 按###标题###标记分割文件内容
    3. 为每个标题创建对应的txt文件，文件名以日期前缀开头
    4. 将正文内容写入对应的文件中
"""

import os
import re
from datetime import datetime

def extract_date_from_text(text):
    """
    从文本中提取日期格式（YYYYMMDD格式）
    
    Args:
        text: 待检查的文本
    
    Returns:
        提取到的日期字符串，如"20251025"，如果未找到则返回None
    """
    print(f"[日志] 开始从文本提取日期: {text[:30]}...")
    
    # 优先匹配最后修改时间格式：[最后修改时间YYYYMMDD]
    last_modified_pattern = re.compile(r'最后修改时间(20\d{6})')
    match = last_modified_pattern.search(text)
    if match:
        date_str = match.group(1)
        print(f"[日志] 匹配到最后修改时间格式: {date_str}")
        return date_str
    
    # 匹配YYYYMMDD格式的日期
    yyyymmdd_pattern = re.compile(r'\b(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\b')
    match = yyyymmdd_pattern.search(text)
    if match:
        date_str = f"{match.group(1)}{match.group(2)}{match.group(3)}"
        print(f"[日志] 匹配到YYYYMMDD格式: {date_str}")
        return date_str
    
    # 匹配YYYY-MM-DD格式
    yyyymmdd_dash_pattern = re.compile(r'\b(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b')
    match = yyyymmdd_dash_pattern.search(text)
    if match:
        date_str = f"{match.group(1)}{match.group(2)}{match.group(3)}"
        print(f"[日志] 匹配到YYYY-MM-DD格式: {date_str}")
        return date_str
    
    # 匹配YYYY.MM.DD格式
    yyyymmdd_dot_pattern = re.compile(r'\b(20\d{2})\.(0[1-9]|1[0-2])\.(0[1-9]|[12]\d|3[01])\b')
    match = yyyymmdd_dot_pattern.search(text)
    if match:
        date_str = f"{match.group(1)}{match.group(2)}{match.group(3)}"
        print(f"[日志] 匹配到YYYY.MM.DD格式: {date_str}")
        return date_str
    
    # 匹配YYYY年MM月DD日格式
    chinese_date_pattern = re.compile(r'\b(20\d{2})年(0[1-9]|1[0-2])月(0[1-9]|[12]\d|3[01])日\b')
    match = chinese_date_pattern.search(text)
    if match:
        date_str = f"{match.group(1)}{match.group(2)}{match.group(3)}"
        print(f"[日志] 匹配到中文日期格式: {date_str}")
        return date_str
    
    print(f"[日志] 未在文本中找到日期格式")
    return None

def get_file_modification_date(file_path):
    """
    获取文件的最后修改时间并格式化为YYYYMMDD格式
    
    Args:
        file_path: 文件路径
    
    Returns:
        格式化的日期字符串，如"20251025"
    """
    print(f"[日志] 获取文件修改时间: {file_path}")
    try:
        # 获取文件修改时间
        mtime = os.path.getmtime(file_path)
        # 转换为datetime对象
        dt = datetime.fromtimestamp(mtime)
        # 格式化为YYYYMMDD
        date_str = dt.strftime('%Y%m%d')
        print(f"[日志] 文件修改时间为: {date_str}")
        return date_str
    except Exception as e:
        print(f"[日志] 获取文件修改时间失败: {e}")
        # 如果失败，返回当前日期
        date_str = datetime.now().strftime('%Y%m%d')
        print(f"[日志] 使用当前日期作为备选: {date_str}")
        return date_str

def normalize_title_and_date(title_text):
    """
    规范化标题和日期格式，处理标题中已有的日期格式
    1. 如果标题已有YYYYMMDD-格式前缀，则保留该日期
    2. 如果标题只有YYYYMMDD格式，则添加-符号
    3. 如果是YYYY年MM月DD日格式，则转换为YYYYMMDD-格式
    4. 处理其他日期格式（YYYY-MM-DD, YYYY.MM.DD）
    5. 否则返回None和原始标题
    
    Args:
        title_text: 原始标题文本
    
    Returns:
        tuple: (date_str, normalized_title) - 提取的日期和规范化后的标题
    """
    print(f"[日志] 开始规范化标题和日期: {title_text}")
    
    # 首先检查标题是否已经包含 "YYYYMMDD-" 格式前缀
    date_prefix_match = re.match(r'(20\d{6})-(.+)', title_text)
    if date_prefix_match:
        # 已经包含正确的日期前缀格式，直接返回
        date_str = date_prefix_match.group(1)
        normalized_title = date_prefix_match.group(2).strip()
        print(f"[日志] 标题已包含正确日期前缀: {date_str}-{normalized_title}")
        return date_str, normalized_title
    
    # 检查标题是否以 "YYYYMMDD" 开头但没有连字符
    date_no_dash_match = re.match(r'(20\d{6})(.*)', title_text)
    if date_no_dash_match:
        # 有日期但没有连字符，需要添加连字符
        date_str = date_no_dash_match.group(1)
        normalized_title = date_no_dash_match.group(2).strip()
        print(f"[日志] 标题包含日期但无连字符，添加连字符: {date_str}-{normalized_title}")
        return date_str, normalized_title
    
    # 检查标题中是否包含 "YYYY年MM月DD日" 格式
    chinese_date_match = re.search(r'(20\d{2})年(0[1-9]|1[0-2])月(0[1-9]|[12]\d|3[01])日', title_text)
    if chinese_date_match:
        # 提取日期并格式化为 YYYYMMDD
        year, month, day = chinese_date_match.groups()
        date_str = f"{year}{month}{day}"
        # 从标题中移除中文日期
        normalized_title = re.sub(r'(20\d{2})年(0[1-9]|1[0-2])月(0[1-9]|[12]\d|3[01])日', '', title_text, count=1).strip()
        print(f"[日志] 处理中文日期格式: {date_str}-{normalized_title}")
        return date_str, normalized_title
    
    # 检查标题中是否包含 "YYYY-MM-DD" 格式
    dash_date_match = re.search(r'(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])', title_text)
    if dash_date_match:
        year, month, day = dash_date_match.groups()
        date_str = f"{year}{month}{day}"
        # 从标题中移除YYYY-MM-DD格式
        normalized_title = re.sub(r'(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])', '', title_text, count=1).strip()
        print(f"[日志] 处理YYYY-MM-DD格式: {date_str}-{normalized_title}")
        return date_str, normalized_title
    
    # 检查标题中是否包含 "YYYY.MM.DD" 格式
    dot_date_match = re.search(r'(20\d{2})\.(0[1-9]|1[0-2])\.(0[1-9]|[12]\d|3[01])', title_text)
    if dot_date_match:
        year, month, day = dot_date_match.groups()
        date_str = f"{year}{month}{day}"
        # 从标题中移除YYYY.MM.DD格式
        normalized_title = re.sub(r'(20\d{2})\.(0[1-9]|1[0-2])\.(0[1-9]|[12]\d|3[01])', '', title_text, count=1).strip()
        print(f"[日志] 处理YYYY.MM.DD格式: {date_str}-{normalized_title}")
        return date_str, normalized_title
    
    # 检查标题中是否包含 "最后修改时间YYYYMMDD" 格式
    last_modified_match = re.search(r'最后修改时间(20\d{6})', title_text)
    if last_modified_match:
        # 提取日期部分
        date_str = last_modified_match.group(1)
        # 从标题中移除"最后修改时间"和日期
        normalized_title = re.sub(r'最后修改时间(20\d{6})', '', title_text, count=1).strip()
        print(f"[日志] 处理'最后修改时间'格式: {date_str}-{normalized_title}")
        return date_str, normalized_title
    
    # 尝试从标题中提取其他日期格式
    extracted_date = extract_date_from_text(title_text)
    if extracted_date:
        # 创建一个清理后的标题，移除所有可能的日期格式
        clean_title = title_text.strip()
        
        # 定义所有可能的日期格式模式
        date_patterns = [
            re.compile(r'(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])'),  # YYYY-MM-DD
            re.compile(r'(20\d{2})\.(0[1-9]|1[0-2])\.(0[1-9]|[12]\d|3[01])'),  # YYYY.MM.DD
            re.compile(r'(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])')  # YYYYMMDD
        ]
        
        # 尝试移除每种日期格式
        for pattern in date_patterns:
            if pattern.search(clean_title):
                clean_title = pattern.sub('', clean_title, count=1).strip()
                print(f"[日志] 清理标题中的日期格式: {clean_title}")
                break  # 只移除第一个匹配的日期
        
        print(f"[日志] 提取到其他日期格式: {extracted_date}-{clean_title}")
        return extracted_date, clean_title
    
    # 没有找到日期，返回None和原始标题
    print(f"[日志] 标题中未找到日期，返回原始标题")
    return None, title_text.strip()

def split_notes_by_title(input_file_path):
    """
    按标题分割笔记内容并生成单独的文件
    
    Args:
        input_file_path: 输入文件路径
    """
    print(f"[日志] 开始分割笔记：{input_file_path}")
    
    # 确保输入文件存在
    if not os.path.exists(input_file_path):
        print(f"[错误] 找不到输入文件 {input_file_path}")
        return
    
    # 获取输入文件所在目录，并创建输出目录
    input_dir = os.path.dirname(input_file_path)
    output_dir = os.path.join(input_dir, "分割后的笔记")
    print(f"[日志] 创建输出目录: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取文件的最后修改时间作为备选日期
    file_mod_date = get_file_modification_date(input_file_path)
    print(f"[日志] 开始处理文件：{input_file_path}")
    print(f"[日志] 输出目录：{output_dir}")
    print(f"[日志] 文件最后修改时间：{file_mod_date}")
    
    # 读取文件内容
    print(f"[日志] 读取文件内容")
    with open(input_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"[日志] 文件读取完成，共 {len(content)} 字符")
    
    # 使用正则表达式分割标题和内容
    print(f"[日志] 使用正则表达式分割标题和内容")
    pattern = r'###标题###((?:\[.*?\]\s*)+)\s*'
    matches = list(re.finditer(pattern, content))
    print(f"[日志] 找到 {len(matches)} 个标题标记")
    
    if not matches:
        print("[警告] 未找到标题标记###标题###")
        return
    
    file_count = 0
    # 处理每个标题及其内容
    print(f"[日志] 开始处理每个标题及其内容")
    for i, match in enumerate(matches):
        print(f"\n[日志] 处理第 {i+1}/{len(matches)} 个标题")
        # 提取所有方括号内容
        brackets_content = match.group(1)
        print(f"[日志] 提取到方括号内容: {brackets_content}")
        
        # 使用正则表达式提取每个方括号内的内容
        bracket_contents = re.findall(r'\[(.*?)\]', brackets_content)
        print(f"[日志] 提取到 {len(bracket_contents)} 个方括号内的内容")
        
        # 初始化日期和标题
        date_str = None
        title_str = ""
        
        if bracket_contents:
            # 第一个方括号内容作为候选标题
            first_content = bracket_contents[0]
            print(f"[日志] 第一个方括号内容(候选标题): {first_content}")
            
            # 使用新的规范化函数处理标题和日期
            extracted_date, normalized_title = normalize_title_and_date(first_content)
            
            if extracted_date:
                # 如果从标题中提取到了日期
                date_str = extracted_date
                title_str = normalized_title
                print(f"[日志] 从标题中提取到日期: {date_str}, 规范化标题: {title_str}")
            else:
                # 如果没有从标题中提取到日期，继续搜索其他方括号内容
                title_str = first_content
                print(f"[日志] 从第一个方括号内容未提取到日期，使用原始内容作为标题: {title_str}")
                
                # 检查其他方括号内容是否包含日期
                print(f"[日志] 检查后续方括号内容 ({len(bracket_contents) - 1} 个) 是否包含日期")
                for j, bracket_content in enumerate(bracket_contents[1:], 2):
                    print(f"[日志] 检查第 {j} 个方括号内容: {bracket_content}")
                    # 也使用规范化函数处理其他方括号内容
                    temp_date, _ = normalize_title_and_date(bracket_content)
                    if temp_date:
                        date_str = temp_date
                        print(f"[日志] 从第 {j} 个方括号内容中提取到日期: {date_str}")
                        break
                
                # 如果仍然没有找到日期，尝试从所有方括号内容中联合提取
                if not date_str and len(bracket_contents) > 1:
                    combined_content = ' '.join(bracket_contents)
                    print(f"[日志] 从单个方括号内容未提取到日期，尝试联合提取: {combined_content[:50]}...")
                    combined_date, _ = normalize_title_and_date(combined_content)
                    if combined_date:
                        date_str = combined_date
                        print(f"[日志] 从联合方括号内容中提取到日期: {date_str}")
        
        # 如果仍然没有找到日期，使用文件的最后修改时间
        if not date_str:
            date_str = file_mod_date
            print(f"[日志] 未找到日期，使用文件修改时间: {date_str}")
        
        # 获取当前标题的开始位置
        start_pos = match.end()
        # 获取下一个标题的开始位置，如果是最后一个则到文件末尾
        end_pos = matches[i + 1].start() if i < len(matches) - 1 else len(content)
        # 提取正文内容，去除首尾空白
        text = content[start_pos:end_pos].strip()
        print(f"[日志] 提取正文内容，长度: {len(text)} 字符")
        
        # 构建文件名：日期-标题.txt
        file_name = f"{date_str}-{title_str}"
        print(f"[日志] 构建文件名: {file_name}")
        # 清理文件名中的非法字符
        valid_file_name = re.sub(r'[\\/:*?\"<>|]', '_', file_name)
        print(f"[日志] 清理非法字符后的文件名: {valid_file_name}")
        # 限制文件名长度，避免操作系统限制
        if len(valid_file_name) > 200:
            valid_file_name = valid_file_name[:197] + "..."
            print(f"[日志] 文件名过长，截断为: {valid_file_name}")
        
        # 创建文件路径
        file_path = os.path.join(output_dir, f"{valid_file_name}.txt")
        print(f"[日志] 创建文件路径: {file_path}")
        
        # 写入文件
        try:
            print(f"[日志] 写入文件内容")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            file_count += 1
            print(f"[日志] 创建文件成功: {i+1}/{len(matches)}: {valid_file_name}.txt")
        except Exception as e:
            print(f"[错误] 创建文件 {valid_file_name}.txt 失败: {e}")
    
    print(f"\n[日志] 处理完成！")
    print(f"[日志] 成功创建 {file_count} 个文件")
    print(f"[日志] 所有文件已保存至: {output_dir}")


if __name__ == "__main__":
    print("[日志] 开始执行笔记分割脚本")
    # 设置笔记导出目录
    notes_dir = os.path.join(os.getcwd(), "笔记导出")
    print(f"[日志] 笔记目录: {notes_dir}")
    
    # 检查目录是否存在
    if not os.path.exists(notes_dir):
        print(f"[错误] 笔记目录不存在: {notes_dir}")
        print(f"[日志] 脚本执行失败")
        exit(1)
    
    # 获取目录下所有以"合集.txt"结尾的文件
    collection_files = [f for f in os.listdir(notes_dir) if f.endswith("合集.txt")]
    print(f"[日志] 找到 {len(collection_files)} 个合集文件")
    
    if not collection_files:
        print(f"[警告] 未找到任何合集.txt文件")
        print(f"[日志] 脚本执行完毕")
        exit(0)
    
    # 依次处理每个合集文件
    total_processed = 0
    for i, file_name in enumerate(collection_files, 1):
        input_file = os.path.join(notes_dir, file_name)
        print(f"\n[日志] ============= 开始处理文件 {i}/{len(collection_files)}: {file_name} =============")
        print(f"[日志] 目标输入文件: {input_file}")
        
        # 执行分割操作
        print(f"[日志] 开始执行分割操作")
        split_notes_by_title(input_file)
        total_processed += 1
        print(f"[日志] 文件 {file_name} 处理完成")
    
    print(f"\n[日志] ============= 所有文件处理完毕 =============")
    print(f"[日志] 成功处理 {total_processed} 个合集文件")
    print(f"[日志] 脚本执行完毕")