import sqlite3
import jieba.posseg as pseg
import re

# 分句函数：将段落切分为句子
def split_sentences(text):
    return text.strip().split("。")

# 生成实体摘要
def generate_entity_summary(persons, locations, organizations, proper_nouns, title):
    """
    基于抽取的实体生成新闻摘要
    """
    summary_parts = []
    
    # 处理人名
    if persons:
        person_list = list(persons)[:3]  # 最多取3个主要人物
        if len(person_list) == 1:
            summary_parts.append(f"涉及{person_list[0]}")
        elif len(person_list) == 2:
            summary_parts.append(f"涉及{person_list[0]}、{person_list[1]}")
        else:
            summary_parts.append(f"涉及{person_list[0]}、{person_list[1]}等人")
    
    # 处理地点
    if locations:
        location_list = list(locations)[:2]  # 最多取2个主要地点
        if len(location_list) == 1:
            summary_parts.append(f"在{location_list[0]}")
        else:
            summary_parts.append(f"在{location_list[0]}、{location_list[1]}等地")
    
    # 处理机构
    if organizations:
        org_list = list(organizations)[:2]  # 最多取2个主要机构
        if len(org_list) == 1:
            summary_parts.append(f"关于{org_list[0]}")
        else:
            summary_parts.append(f"关于{org_list[0]}、{org_list[1]}等机构")
    
    # 如果没有足够的实体信息，使用标题关键词
    if not summary_parts:
        # 简单的标题关键词提取
        title_words = [word for word, flag in pseg.cut(title) if flag.startswith('n') and len(word) > 1]
        if title_words:
            summary_parts.append(f"关于{title_words[0]}")
    
    # 组合摘要
    if summary_parts:
        summary = "、".join(summary_parts) + "的相关新闻"
        # 限制摘要长度
        if len(summary) > 50:
            summary = summary[:47] + "..."
        return summary
    else:
        return "新闻摘要信息不足"

# 信息抽取主函数
def extract_information(records):
    results = []

    for idx, record in enumerate(records):
        year, month, day, url, title, content = record

        # 初始化结果行 - 添加摘要字段
        row = [year, month, day, title, '', '', '', '', '', '']

        persons = set()
        locations = set()
        organizations = set()
        proper_nouns = set()
        idioms = set()

        for sentence in split_sentences(content):
            for word, flag in pseg.cut(sentence):
                if flag.startswith('n'):
                    if flag == 'nr':
                        persons.add(word)
                    elif flag == 'ns':
                        locations.add(word)
                    elif flag == 'nt':
                        organizations.add(word)
                    elif flag == 'nz':
                        proper_nouns.add(word)
                    elif flag == 'j':
                        idioms.add(word)

        row[4] = ' '.join(persons)
        row[5] = ' '.join(locations)
        row[6] = ' '.join(organizations)
        row[7] = ' '.join(proper_nouns)
        row[8] = ' '.join(idioms)
        
        # 生成摘要
        row[9] = generate_entity_summary(persons, locations, organizations, proper_nouns, title)

        results.append(row)

    return results

# 主执行逻辑：连接数据库、获取数据、调用抽取
def main():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM texts")
    records = cursor.fetchall()
    conn.close()

    extracted_data = extract_information(records)
    return extracted_data

# 命令行测试入口
if __name__ == '__main__':
    final_result = main()
    for entry in final_result:
        print(entry)