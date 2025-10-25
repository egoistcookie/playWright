import re

def count_characters_between_titles(file_path):
    """
    扫描文件，计算标题之间的字符数，并标注空笔记
    """
    title_pattern = r'^###标题###\['  # 标题行的正则表达式
    title_info = []  # 存储标题信息：(行号, 标题文本)
    
    # 第一遍扫描：找到所有标题行
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            stripped_line = line.strip()
            if re.match(title_pattern, stripped_line):
                title_info.append((i, stripped_line))
    
    print(f"总共找到 {len(title_info)} 个标题")
    print("\n标题之间的字符统计:")
    print("-" * 100)
    print(f"{'起始标题':<30} {'结束标题':<30} {'字符数':<10} {'状态'}")
    print("-" * 100)
    
    empty_notes = []  # 存储空笔记信息
    
    # 计算每个标题之间的字符数
    with open(file_path, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
    
    for i in range(len(title_info) - 1):
        current_line, current_title = title_info[i]
        next_line, next_title = title_info[i + 1]
        
        # 提取标题内容部分用于显示
        current_title_short = current_title.replace('###标题###[', '').replace(']', '')
        next_title_short = next_title.replace('###标题###[', '').replace(']', '')
        
        # 计算两个标题之间的字符数（排除空行）
        total_characters = 0
        
        # 遍历两个标题之间的所有行
        for j in range(current_line, next_line - 1):
            if j < len(all_lines):
                # 获取行内容，去除前后空白
                line_content = all_lines[j].strip()
                # 只计算非空行的字符数
                if line_content:
                    total_characters += len(line_content)
        
        # 判断是否为空笔记
        is_empty = total_characters == 0
        status = "⚠️ 空笔记" if is_empty else "正常"
        
        # 记录空笔记
        if is_empty:
            empty_notes.append({
                'current_title': current_title,
                'next_title': next_title,
                'current_line': current_line,
                'next_line': next_line
            })
        
        print(f"{current_title_short[:25]:<30} {next_title_short[:25]:<30} {total_characters:<10} {status}")
    
    print("-" * 100)
    
    # 输出空笔记统计
    print(f"\n发现 {len(empty_notes)} 个空笔记:")
    if empty_notes:
        print("-" * 100)
        for idx, note in enumerate(empty_notes, 1):
            current_title_short = note['current_title'].replace('###标题###[', '').replace(']', '')
            print(f"{idx}. 从 '{current_title_short}' 开始的笔记为空 (行 {note['current_line']})")
        print("-" * 100)
    
    return {
        'total_titles': len(title_info),
        'title_pairs': len(title_info) - 1,
        'empty_notes': len(empty_notes)
    }

if __name__ == "__main__":
    file_path = "d:/AiProject/traeWorkspace/playWright/笔记导出/工作笔记合集.txt"
    stats = count_characters_between_titles(file_path)
    
    print(f"\n统计总结:")
    print(f"- 标题总数: {stats['total_titles']}")
    print(f"- 笔记总数: {stats['title_pairs']}")
    print(f"- 空笔记数: {stats['empty_notes']}")
    print(f"- 空笔记比例: {stats['empty_notes'] / stats['title_pairs'] * 100:.1f}%")

# 工作笔记合集 统计结果
# 发现 2 个空笔记:
# ----------------------------------------------------------------------------------------------------
# 1. 从 '案例评审记录 [最后修改时间20250227' 开始的笔记为空 (行 1177)
# 2. 从 '统一授信会议纪要 [最后修改时间20220216' 开始的笔记为空 (行 2015)
# ----------------------------------------------------------------------------------------------------

# 统计总结:
# - 标题总数: 61
# - 笔记总数: 60
# - 空笔记数: 2
# - 空笔记比例: 3.3%