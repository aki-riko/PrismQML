# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是PrismQML的一部分，采用MIT许可证授权。
"""将 FluentTranslator.qml 中的翻译数据提取到外部 JSON 文件"""
import re
import json
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent

qml_path = _PROJECT_ROOT / "prismqml" / "PrismQML" / "FluentTranslator.qml"
output_dir = _PROJECT_ROOT / "prismqml" / "PrismQML" / "i18n"
output_dir.mkdir(exist_ok=True)

content = qml_path.read_text(encoding="utf-8")

# 找到 translations 属性的起始位置
match = re.search(r'readonly property var translations:\s*\(\{', content)
if not match:
    print("ERROR: translations not found")
    exit(1)

trans_start = match.start()
# 从 '({' 开始找匹配的 '})'
brace_start = content.index("({", trans_start) + 1  # skip the (
depth = 0
pos = brace_start
while pos < len(content):
    if content[pos] == '{':
        depth += 1
    elif content[pos] == '}':
        depth -= 1
        if depth == 0:
            break
    pos += 1
trans_end = pos + 1  # include the closing }

trans_block = content[brace_start:trans_end]

# 解析每个语言块
# 模式: "lang_code": { ... }
lang_pattern = re.compile(r'"(\w+)":\s*\{', re.MULTILINE)
langs = []

i = 0
while i < len(trans_block):
    m = lang_pattern.search(trans_block, i)
    if not m:
        break
    
    lang_code = m.group(1)
    
    # 找到这个语言块的起始 {
    block_start = m.end() - 1
    depth = 0
    j = block_start
    while j < len(trans_block):
        if trans_block[j] == '{':
            depth += 1
        elif trans_block[j] == '}':
            depth -= 1
            if depth == 0:
                break
        j += 1
    
    lang_block = trans_block[block_start:j+1]
    
    # 解析 key-value pairs
    kv_pattern = re.compile(r'"(\w+)":\s*"([^"]*)"')
    entries = {}
    for kv in kv_pattern.finditer(lang_block):
        entries[kv.group(1)] = kv.group(2)
    
    if entries:
        langs.append((lang_code, entries))
        # 写入单独的 JSON 文件
        json_path = output_dir / f"{lang_code}.json"
        json_path.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"  {lang_code}: {len(entries)} keys -> {json_path.name}")
    
    i = j + 1

print(f"\nTotal: {len(langs)} languages extracted to {output_dir}")
