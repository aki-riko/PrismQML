# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是PrismQML的一部分，采用MIT许可证授权。
"""复制全部Microsoft Fluent UI Icons到PrismQML"""
import os
import shutil
from pathlib import Path

# 使用相对路径，基于脚本位置 Use relative paths based on script location
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
SOURCE_DIR = PROJECT_ROOT / "fluentui-system-icons" / "assets"
TARGET_DIR = PROJECT_ROOT / "prismqml" / "PrismQML" / "controls" / "icons" / "fluent"

# 清空目标目录
if TARGET_DIR.exists():
    shutil.rmtree(TARGET_DIR)
TARGET_DIR.mkdir(parents=True, exist_ok=True)

copied = 0
icon_names = []

# 遍历所有图标文件夹
for icon_folder in sorted(SOURCE_DIR.iterdir()):
    if not icon_folder.is_dir():
        continue
    
    svg_folder = icon_folder / "SVG"
    if not svg_folder.exists():
        continue
    
    # 优先使用20尺寸的regular风格
    for size in [20, 24, 16]:
        svg_files = list(svg_folder.glob(f"*_{size}_regular.svg"))
        if svg_files:
            src_file = svg_files[0]
            # 使用文件夹名作为图标名（移除空格）
            icon_name = icon_folder.name.replace(" ", "")
            dst_file = TARGET_DIR / f"{icon_name}.svg"
            
            if not dst_file.exists():
                shutil.copy(src_file, dst_file)
                icon_names.append(icon_name)
                copied += 1
                if copied % 100 == 0:
                    print(f"已复制 {copied} 个图标...")
            break

print(f"\n复制完成: {copied} 个图标")

# 生成枚举文件
enum_file = TARGET_DIR.parent / "FluentIcons.qml"
with open(enum_file, "w", encoding="utf-8") as f:
    f.write('''import QtQuick 2.15

// FluentIcons - Fluent UI 图标枚举
// 来源: Microsoft Fluent UI System Icons (MIT License)
// 图标总数: ''' + str(copied) + '''
pragma Singleton

QtObject {
    id: root
    
    readonly property string basePath: "fluent/"
    
    // 获取图标路径
    function path(iconName) {
        return basePath + iconName + ".svg"
    }
    
    // 图标名称映射（大写枚举 -> 实际名称）
    readonly property var icons: ({
''')
    
    # 写入图标映射
    for name in sorted(icon_names):
        enum_name = name.upper()
        # 处理特殊字符
        enum_name = enum_name.replace("-", "_").replace(".", "_")
        f.write(f'        "{enum_name}": "{name}",\n')
    
    f.write('''    })
    
    // 图标列表（用于遍历）
    readonly property var allIcons: [
''')
    
    # 写入图标列表
    for i, name in enumerate(sorted(icon_names)):
        if i > 0:
            f.write(",\n")
        f.write(f'        "{name}"')
    
    f.write('''
    ]
}
''')

print(f"枚举文件已生成: {enum_file}")
