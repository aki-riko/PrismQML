# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""
测试窗口按钮点击功能
用于验证 FluentQML 窗口的最小化、最大化、关闭按钮是否可正常交互
"""
import sys
import os

# 确保可以导入 prismqml
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from prismqml import App, Window, WindowType

def main():
    app = App(sys.argv)
    
    # 创建一个简单的 BAR 类型窗口
    window = Window(window_type=WindowType.BAR)
    window.setWindowTitle("窗口按钮测试")
    window.resize(800, 600)
    
    # 添加一个简单页面
    window.addPage(None, "", "测试页面")
    
    window.show()
    
    print("窗口已显示。请测试最小化、最大化、关闭按钮是否可点击。")
    print("按钮位于窗口右上角。")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
