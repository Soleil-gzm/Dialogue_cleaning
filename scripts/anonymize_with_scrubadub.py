#!/usr/bin/env python3
"""
使用 scrubadub 进行数据脱敏，支持中文占位符：
- 工号 → {工号}
- 中文姓名（含"女士/先生"） → {姓名}
- 电话号码 → {电话}
- 邮箱 → {邮箱}
- 保留英文单词原样（不处理）
"""

import re
import json
from pathlib import Path
import scrubadub
from scrubadub.detectors import Detector, PhoneDetector, EmailDetector
from scrubadub.filth import Filth

# --- 1. 自定义工号检测器（不指定 replace_with）---
class EmployeeIDDetector(Detector):
    def __init__(self, name="employee_id", **kwargs):
        super().__init__(name=name, **kwargs)

    def iter_filth(self, text, document_name=None):
        pattern = r'(?:工号|ID|工号[:：]?)\s*(\d{4,8})'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            yield Filth(
                beg=match.start(),
                end=match.end(),
                text=match.group(),
                detector_name=self.name,
                document_name=document_name,
                # 不设置 replace_with，由 scrubber 统一配置
            )

# --- 2. 自定义中文姓名检测器（不指定 replace_with）---
class ChineseNameDetector(Detector):
    def __init__(self, name="chinese_name", **kwargs):
        super().__init__(name=name, **kwargs)
        self.surnames = ['李','王','张','刘','陈','杨','赵','黄','周','吴',
                         '徐','孙','胡','朱','高','林','何','郭','马','罗',
                         '梁','宋','郑','谢','韩','唐','冯','于','董','萧',
                         '程','曹','袁','邓','许','傅','沈','曾','彭','吕',
                         '苏','卢','蒋','蔡','贾','丁','魏','薛','叶','阎',
                         '余','潘','杜','戴','夏','钟','汪','田','任','姜',
                         '范','方','石','姚','谭','廖','邹','熊','金','陆',
                         '郝','孔','白','崔','康','毛','邱','秦','江','史',
                         '顾','侯','邵','孟','龙','万','段','雷','钱','汤',
                         '尹','黎','易','常','武','乔','贺','赖','龚','文']

    def iter_filth(self, text, document_name=None):
        # 匹配 "X女士" 或 "X先生"
        honorific_pattern = r'([\u4e00-\u9fa5]{1,2})(?:女士|先生)'
        for match in re.finditer(honorific_pattern, text):
            yield Filth(
                beg=match.start(),
                end=match.end(),
                text=match.group(),
                detector_name=self.name,
                document_name=document_name,
            )
        # 匹配姓氏+1~2个汉字
        for surname in self.surnames:
            fullname_pattern = surname + r'[\u4e00-\u9fa5]{1,2}'
            for match in re.finditer(fullname_pattern, text):
                yield Filth(
                    beg=match.start(),
                    end=match.end(),
                    text=match.group(),
                    detector_name=self.name,
                    document_name=document_name,
                )

# --- 3. 初始化 scrubber 并注册自定义检测器 ---
scrubber = scrubadub.Scrubber()
scrubber.add_detector(EmployeeIDDetector)
scrubber.add_detector(ChineseNameDetector)

# 通过 replace_with 方法为每个检测器指定替换文本（中文占位符）
scrubber.replace_with(EmployeeIDDetector, '{工号}')
scrubber.replace_with(ChineseNameDetector, '{姓名}')
scrubber.replace_with(PhoneDetector, '{电话}')
scrubber.replace_with(EmailDetector, '{邮箱}')

# --- 4. 主处理函数（不处理英文单词）---
def anonymize_text(text):
    if not isinstance(text, str):
        return text
    cleaned_text = scrubber.clean(text)
    return cleaned_text

# --- 5. 应用到 JSONL 文件 ---
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
    input_dir = "samples"            # 原始样本目录
    output_dir = "samples_anonymized" # 脱敏后输出目录
    process_files(input_dir, output_dir)