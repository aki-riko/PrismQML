# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是PrismQML的一部分，采用MIT许可证授权。
"""图标枚举生成工具 - Python作为单一来源

从SVG图标文件夹读取所有图标，生成：
1. Python枚举文件 (prismqml/python/core/icons.py)
2. QML图标文件 (prismqml/PrismQML/FluentEnums/Icons.qml)

Usage:
    python tools/extract_icons.py
"""

import re
from pathlib import Path


# QML/JavaScript 保留字列表
QML_RESERVED_WORDS = {
    'break', 'case', 'catch', 'continue', 'debugger', 'default', 'delete',
    'do', 'else', 'finally', 'for', 'function', 'if', 'in', 'instanceof',
    'new', 'return', 'switch', 'this', 'throw', 'try', 'typeof', 'var',
    'void', 'while', 'with', 'class', 'const', 'enum', 'export', 'extends',
    'import', 'super', 'implements', 'interface', 'let', 'package', 'private',
    'protected', 'public', 'static', 'yield', 'true', 'false', 'null',
    'undefined', 'NaN', 'Infinity', 'property', 'signal', 'readonly',
    'alias', 'id', 'parent', 'root', 'anchors', 'width', 'height',
    'print',  # QML 中 print 是保留字
}


def get_icons_from_svg_folder() -> list:
    """从SVG文件夹读取所有图标名"""
    svg_dir = Path(__file__).parent.parent / 'prismqml/PrismQML/controls/icons/fluent'
    icons = []
    
    for svg_file in sorted(svg_dir.glob('*.svg')):
        # 文件名就是图标名（不含.svg后缀）
        icon_name = svg_file.stem
        icons.append(icon_name)
    
    return icons


def to_enum_name(pascal_case: str) -> str:
    """PascalCase -> UPPER_SNAKE_CASE"""
    result = re.sub(r'([A-Z])', r'_\1', pascal_case)
    return result.upper().lstrip('_')


def to_snake_case(pascal_case: str) -> str:
    """PascalCase -> lower_snake_case"""
    result = re.sub(r'([A-Z])', r'_\1', pascal_case)
    return result.lower().lstrip('_')


def escape_qml_property_name(name: str) -> str:
    """转义 QML 保留字属性名"""
    if name in QML_RESERVED_WORDS:
        return f'icon_{name}'
    return name


def generate_python_enum(icons: list) -> str:
    """生成Python枚举文件"""
    header = '''# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是PrismQML的一部分，采用MIT许可证授权。

"""Icon - Fluent UI图标枚举

自动生成，请勿手动编辑！
Auto-generated, do not edit manually!

Total icons: {count}

Usage:
    # Python
    from prismqml.python.core.icons import Icon
    icon = Icon.CALENDAR
    
    # QML (通过FluentEnums.icon)
    icon: FluentEnums.icon.calendar
"""

from enum import Enum
from typing import List


class Icon(str, Enum):
    """Fluent UI图标枚举
    
    继承str使得可以直接用于字符串场景：
        Button(icon=Icon.SETTINGS)  # 自动转为 "Settings"
    """
    
'''
    
    # 生成枚举成员
    members = []
    for icon in icons:
        enum_name = to_enum_name(icon)
        # 处理数字开头的情况（如 3D）
        if enum_name[0].isdigit():
            enum_name = '_' + enum_name
        members.append(f'    {enum_name} = "{icon}"')
    
    footer = '''
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def get_all(cls) -> List[str]:
        """获取所有图标名列表"""
        return [icon.value for icon in cls]
    
    @classmethod
    def get_all_enum_names(cls) -> List[str]:
        """获取所有枚举名列表"""
        return [icon.name for icon in cls]
'''
    
    return header.format(count=len(icons)) + '\n'.join(members) + footer


def generate_qml_icons(icons: list) -> str:
    """生成QML图标文件"""
    header = f'''import QtQuick

// FluentIcons - Fluent UI icon enum 图标枚举
// Auto-generated from SVG folder, do not edit manually!
// 自动生成，请勿手动编辑！
// Total icons: {len(icons)} 图标总数
// Usage: FluentEnums.icon.chevron_up 使用方式
pragma Singleton

QtObject {{
    id: root
    
    readonly property string basePath: "fluent/"
    
    // Get icon path 获取图标路径
    function path(iconName) {{
        return basePath + iconName + ".svg"
    }}
    
    // Icon list for iteration 图标列表（用于遍历）
    readonly property var iconList: {{
'''
    
    # 生成iconList对象
    icon_list_items = []
    for icon in icons:
        enum_name = to_enum_name(icon)
        if enum_name[0].isdigit():
            enum_name = '_' + enum_name
        icon_list_items.append(f'        "{enum_name}": "{icon}"')
    
    middle = '''    }
    
    // ==================== Icon Properties 图标属性 ====================
'''
    
    # 生成属性
    properties = []
    for icon in icons:
        snake_name = to_snake_case(icon)
        # 处理数字开头
        if snake_name[0].isdigit():
            snake_name = '_' + snake_name
        # 处理 QML 保留字
        snake_name = escape_qml_property_name(snake_name)
        properties.append(f'    readonly property string {snake_name}: "{icon}"')
    
    footer = '''
}
'''
    
    return (header + 
            ',\n'.join(icon_list_items) + 
            middle + 
            '\n'.join(properties) + 
            footer)


if __name__ == '__main__':
    icons = get_icons_from_svg_folder()
    print(f'Total icons from SVG folder: {len(icons)}')
    
    # 生成Python枚举文件
    py_output = Path(__file__).parent.parent / 'prismqml/python/core/icons.py'
    py_output.parent.mkdir(parents=True, exist_ok=True)
    py_content = generate_python_enum(icons)
    py_output.write_text(py_content, encoding='utf-8')
    print(f'Generated Python: {py_output} ({len(py_content)} bytes)')
    
    # 生成QML图标文件
    qml_output = Path(__file__).parent.parent / 'prismqml/PrismQML/FluentEnums/Icons.qml'
    qml_content = generate_qml_icons(icons)
    qml_output.write_text(qml_content, encoding='utf-8')
    print(f'Generated QML: {qml_output} ({len(qml_content)} bytes)')
