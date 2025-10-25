import re

def count_empty_lines_between_titles(file_path):
    """
    扫描文件，找到所有标题之间为空的行数
    """
    title_pattern = r'^###标题###\['  # 标题行的正则表达式
    title_positions = []  # 存储标题行的行号
    titles = []  # 存储标题文本
    
    # 一遍扫描：找到所有标题行的位置和文本
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            stripped_line = line.strip()
            if re.match(title_pattern, stripped_line):
                title_positions.append(i)
                titles.append(stripped_line)
    
    print(f"总共找到 {len(title_positions)} 个标题")
    print("\n标题之间的空行数:")
    print("-" * 80)
    print(f"{'起始标题':<40} {'结束标题':<40} {'空行数'}")
    print("-" * 80)
    
    # 计算标题之间的空行数
    results = []
    for i in range(len(title_positions) - 1):
        current_title_line = title_positions[i]
        next_title_line = title_positions[i + 1]
        current_title = titles[i]
        next_title = titles[i + 1]
        
        empty_line_count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # 只检查两个标题之间的行
            for j in range(current_title_line, next_title_line):
                if j < len(lines) and lines[j].strip() == '':
                    empty_line_count += 1
        
        # 简化显示，只显示标题内容部分
        current_title_short = current_title.replace('###标题###[', '').replace(']', '')
        next_title_short = next_title.replace('###标题###[', '').replace(']', '')
        
        print(f"{current_title_short[:35]:<40} {next_title_short[:35]:<40} {empty_line_count}")
        
        results.append({
            'current_title': current_title,
            'next_title': next_title,
            'empty_lines': empty_line_count
        })
    
    print("-" * 80)
    return results

if __name__ == "__main__":
    file_path = "d:/AiProject/traeWorkspace/playWright/笔记导出/有道云笔记_日记_2025-10-25T20-52-22-972116.txt"
    count_empty_lines_between_titles(file_path)