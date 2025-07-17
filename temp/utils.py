# 读取PDF
import os

# 从PDF的表格中提取文本
import pdfplumber

# 分析PDF的layout，提取文本
from pdfminer.layout import LTChar, LTTextContainer


def text_extraction(element):
    # 从行元素中提取文本
    line_text = element.get_text()

    # 探析文本的格式
    # 用文本行中出现的所有格式初始化列表
    line_formats = []
    for text_line in element:
        if isinstance(text_line, LTTextContainer):
            # 遍历文本行中的每个字符
            for character in text_line:
                if isinstance(character, LTChar):
                    # 追加字符的font-family
                    line_formats.append(character.fontname)
                    # 追加字符的font-size
                    line_formats.append(character.size)
    # 找到行中唯一的字体大小和名称
    format_per_line = list(set(line_formats))

    # 返回包含每行文本及其格式的元组
    return (line_text, format_per_line)


def extract_table(pdf_path, page_num, table_num):
    # 打开PDF文件
    pdf = pdfplumber.open(pdf_path)
    # 查找已检查的页面
    table_page = pdf.pages[page_num]
    # 提取适当的表格
    table = table_page.extract_tables()[table_num]
    return table


# 将表格转换为适当的格式
def table_converter(table):
    table_string = ''
    # 遍历表格的每一行
    for row_num in range(len(table)):
        row = table[row_num]
        # 从warp的文字删除线路断路器
        cleaned_row = [item.replace('\n', ' ') if item is not None and '\n' in item else 'None' if item is None else item for item in row]
        # 将表格转换为字符串，注意'|'、'\n'
        table_string += ('|' + '|'.join(cleaned_row) + '|' + '\n')
    # 删除最后一个换行符
    table_string = table_string[:-1]
    return table_string
