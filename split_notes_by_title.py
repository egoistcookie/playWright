#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分割有道云笔记导出文件，按标题生成单独的txt文件

功能：
    1. 读取有道云笔记导出的汇总文件
    2. 按###标题###标记分割文件内容
    3. 为每个标题创建对应的txt文件
    4. 将正文内容写入对应的文件中
"""

import os
import re


def split_notes_by_title(input_file_path):
    """
    按标题分割笔记内容并生成单独的文件
    
    Args:
        input_file_path: 输入文件路径
    """
    # 确保输入文件存在
    if not os.path.exists(input_file_path):
        print(f"错误：找不到输入文件 {input_file_path}")
        return
    
    # 获取输入文件所在目录，并创建输出目录
    input_dir = os.path.dirname(input_file_path)
    output_dir = os.path.join(input_dir, "分割后的笔记")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"开始处理文件：{input_file_path}")
    print(f"输出目录：{output_dir}")
    
    # 读取文件内容
    with open(input_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用正则表达式分割标题和内容
    # 匹配###标题###[标题内容]格式
    pattern = r'###标题###\[(.*?)\]\s+'
    matches = list(re.finditer(pattern, content))
    
    if not matches:
        print("未找到标题标记###标题###")
        return
    
    file_count = 0
    # 处理每个标题及其内容
    for i, match in enumerate(matches):
        title = match.group(1)
        # 获取当前标题的开始位置
        start_pos = match.end()
        # 获取下一个标题的开始位置，如果是最后一个则到文件末尾
        end_pos = matches[i + 1].start() if i < len(matches) - 1 else len(content)
        # 提取正文内容，去除首尾空白
        text = content[start_pos:end_pos].strip()
        
        # 清理标题中的非法字符，确保文件名有效
        valid_title = re.sub(r'[\\/:*?"<>|]', '_', title)
        # 创建文件路径
        file_path = os.path.join(output_dir, f"{valid_title}.txt")
        
        # 写入文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            file_count += 1
            print(f"创建文件 {i+1}/{len(matches)}: {valid_title}.txt")
        except Exception as e:
            print(f"创建文件 {valid_title}.txt 失败: {e}")
    
    print(f"\n处理完成！")
    print(f"成功创建 {file_count} 个文件")
    print(f"所有文件已保存至: {output_dir}")


if __name__ == "__main__":
    # 输入文件路径
    input_file = "d:/AiProject/traeWorkspace/playWright/笔记导出/有道云笔记_日记_2025-10-24T23-10-35-563486.txt"
    
    # 执行分割操作
    split_notes_by_title(input_file)