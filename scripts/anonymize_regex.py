#!/usr/bin/env python3
"""
两阶段脱敏脚本：
1. 正则处理工号、电话、邮箱。
2. 正则处理称谓（X女士/X先生）→ 小红。
3. jieba 分词识别人名（词性 nr），过滤排除词表，替换为“小红”。
"""

import re
import json
from pathlib import Path
import jieba.posseg as pseg

# 排除词表：这些词即使被 jieba 标记为人名也不替换
EXCLUDE_WORDS = {
    '阳光', '华夏', '银行', '机构', '业务', '尾号', '委外', '信用卡',
    '宽限期', '还款日', '账单', '逾期', '卡片', '客服', '电话', '手机'
}

def anonymize_text(text):
    if not isinstance(text, str):
        return text

    # 1. 工号
    text = re.sub(r'(?:工号|ID|工号[:：]?)\s*(\d{4,8})', r'工号10058', text, flags=re.IGNORECASE)
    # 2. 电话号码
    text = re.sub(r'1[3-9]\d{9}', r'{电话}', text)
    text = re.sub(r'0\d{2,3}-\d{7,8}', r'{电话}', text)
    text = re.sub(r'0\d{2,3}-\d{7,8}-\d+', r'{电话}', text)
    # 3. 邮箱
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', r'{邮箱}', text)

    # 4. 称谓姓名（X女士/X先生）整体替换为“小红”
    text = re.sub(r'[\u4e00-\u9fa5]{1,2}(?:女士|先生)', r'[人名]', text)

    # 5. jieba 识别人名，过滤排除词表后替换为“小红”
    words = pseg.cut(text)
    # 收集所有需要替换的人名（原词）
    names_to_replace = set()
    for word, flag in words:
        if flag == 'nr' and word not in EXCLUDE_WORDS:
            # 避免替换已经处理过的“小红”占位符
            if word != '[人名]':
                names_to_replace.add(word)

    # 按长度降序排序，避免短词替换破坏长词
    for name in sorted(names_to_replace, key=len, reverse=True):
        text = text.replace(name, '[人名]')

    return text

def process_files(input_dir, output_dir):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for jsonl_file in input_path.glob("*.jsonl"):
        output_file = output_path / jsonl_file.name
        with open(jsonl_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            for line in infile:
                if not line.strip():
                    continue
                data = json.loads(line)
                if 'user_input' in data:
                    data['user_input'] = anonymize_text(data['user_input'])
                if 'target_output' in data:
                    data['target_output'] = anonymize_text(data['target_output'])
                outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
        print(f"处理完成: {jsonl_file.name}")

if __name__ == "__main__":
    input_dir = "samples"
    output_dir = "samples_anonymized"
    process_files(input_dir, output_dir)