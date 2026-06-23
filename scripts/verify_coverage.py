# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
"""验证Python-QML桥接层的实际覆盖率

系统性地检查所有接口是否真的已实现
"""

import os
import re
from pathlib import Path

# 需要验证的接口
INTERFACES_TO_CHECK = {
    'QSlider': [
        'singleStep', 'setSingleStep', 'pageStep', 'setPageStep',
        'tickPosition', 'setTickPosition', 'tickInterval', 'setTickInterval',
        'setRange'
    ],
    'QLineEdit': [
        'selectedText', 'setMaxLength', 'maxLength', 'setValidator', 'validator'
    ],
    'QTextEdit': [
        'toHtml', 'setHtml', 'append'
    ],
    'QScrollArea': [
        'setHorizontalScrollBarPolicy', 'setVerticalScrollBarPolicy',
        'ensureVisible', 'ensureWidgetVisible'
    ],
    'QLayout': [
        'setContentsMargins', 'contentsMargins', 'insertWidget',
        'removeWidget', 'count', 'itemAt'
    ],
    'QListWidget': [
        'insertItem', 'insertItems', 'takeItem', 'clear', 'count',
        'currentItem', 'setCurrentItem', 'currentRow', 'setCurrentRow',
        'findItems', 'item'
    ],
    'QStackedWidget': [
        'insertWidget', 'removeWidget', 'count', 'widget', 'setCurrentWidget'
    ],
    'QTableWidget': [
        'item', 'setItem', 'takeItem', 'setHorizontalHeaderLabels',
        'setVerticalHeaderLabels', 'setColumnWidth', 'setRowHeight',
        'setSortingEnabled', 'sortByColumn'
    ],
    'QTreeWidget': [
        'addTopLevelItem', 'addTopLevelItems', 'insertTopLevelItem',
        'topLevelItemCount', 'topLevelItem', 'currentItem', 'setCurrentItem',
        'expandItem', 'collapseItem', 'expandAll', 'collapseAll',
        'setHeaderLabels', 'header', 'findItems'
    ],
    'QSplitter': [
        'addWidget', 'insertWidget', 'count', 'widget', 'sizes', 'setSizes',
        'setCollapsible', 'isCollapsible', 'handleWidth', 'setHandleWidth'
    ],
    'QSpinBox': [
        'wrapping', 'setWrapping', 'specialValueText', 'setSpecialValueText',
        'setRange'
    ],
    'QWidget': [
        'minimumSize', 'setMinimumSize', 'setMinimumWidth', 'setMinimumHeight',
        'maximumSize', 'setMaximumSize', 'setMaximumWidth', 'setMaximumHeight',
        'sizePolicy', 'setSizePolicy', 'toolTip', 'setToolTip',
        'font', 'setFont', 'hasFocus', 'setFocus', 'clearFocus',
        'objectName', 'setObjectName', 'setProperty', 'property',
        'setCursor', 'geometry', 'rect', 'pos', 'size', 'update', 'repaint'
    ],
}

def check_method_exists(file_path: Path, method_name: str) -> bool:
    """检查方法是否存在于文件中"""
    if not file_path.exists():
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 匹配 def method_name(
        pattern = rf'def {re.escape(method_name)}\s*\('
        return bool(re.search(pattern, content))

def verify_coverage():
    """验证覆盖率"""
    python_dir = Path(__file__).parent.parent / 'prismqml' / 'python'
    
    results = {}
    
    for qt_class, methods in INTERFACES_TO_CHECK.items():
        results[qt_class] = {'total': len(methods), 'implemented': 0, 'missing': []}
        
        # 确定要检查的文件
        files_to_check = list(python_dir.glob('*.py'))
        
        for method in methods:
            found = False
            for file_path in files_to_check:
                if check_method_exists(file_path, method):
                    found = True
                    break
            
            if found:
                results[qt_class]['implemented'] += 1
            else:
                results[qt_class]['missing'].append(method)
    
    # 打印结果
    print("=" * 80)
    print("Python-QML桥接层接口覆盖率验证")
    print("=" * 80)
    print()
    
    total_methods = 0
    total_implemented = 0
    
    for qt_class, data in results.items():
        total = data['total']
        implemented = data['implemented']
        coverage = (implemented / total * 100) if total > 0 else 0
        
        total_methods += total
        total_implemented += implemented
        
        status = "✅" if coverage == 100 else "⚠️"
        print(f"{qt_class:20s} {implemented:3d}/{total:3d} ({coverage:5.1f}%) {status}")
        
        if data['missing']:
            print(f"  缺失: {', '.join(data['missing'][:5])}")
            if len(data['missing']) > 5:
                print(f"        ... 还有 {len(data['missing']) - 5} 个")
        print()
    
    overall_coverage = (total_implemented / total_methods * 100) if total_methods > 0 else 0
    print("=" * 80)
    print(f"总体覆盖率: {total_implemented}/{total_methods} ({overall_coverage:.1f}%)")
    print("=" * 80)

if __name__ == '__main__':
    verify_coverage()
