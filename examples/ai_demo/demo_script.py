# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Canned content for the Gallery assistant page. Gallery 助手页的固定演示内容。

🔴 演示内容（会话正文、气泡矩阵的行标签）一律留在这里，不写进 QML：Gallery 的 i18n 门禁会把
   QML 里的中文与面向用户的英文串全部登记成待翻译项，演示话术不该逼着 20 份语言目录各翻一遍。
   页面只负责渲染，文案从这里取。
"""

from __future__ import annotations

# 静态会话：一条自己的提问 + 一条带推理与代码块的助手回答 + 一条系统消息。
PREVIEW_MESSAGES: tuple[dict[str, str], ...] = (
    {
        "role": "user",
        "content": "消息气泡的表面、圆角、描边和阴影，是每个界面自己画吗？",
        "reasoning": "",
        "timestamp": "21:24",
    },
    {
        "role": "assistant",
        "content": (
            "不用。外壳由引擎统一提供：\n\n"
            "- **表面色 / 圆角 / 尖角**：`ChatBubbleSurface`\n"
            "- **描边与阴影层级**：按 `role` 分流，系统消息不挂阴影\n"
            "- **皮肤、深色模式、主题色**：全部跟随令牌，界面只提供内容\n\n"
            "```qml\n"
            "ChatBubbleSurface {\n"
            "    role: \"assistant\"\n"
            "    tail: true\n"
            "}\n"
            "```"
        ),
        "reasoning": "先区分「外壳」与「内容」，再说明外壳的取色来源是令牌而不是字面量。",
        "timestamp": "21:24",
    },
    {
        "role": "system",
        "content": "以上内容由固定话术演示，未接入任何模型。",
        "reasoning": "",
        "timestamp": "",
    },
)

# 气泡壳矩阵：role × 尖角 × 用户侧浮起，三列各自展示一种取舍。
SURFACE_SHOWCASE: tuple[dict[str, object], ...] = (
    {"role": "user", "tail": True, "elevationOnUser": True, "label": "role: user · tail"},
    {"role": "assistant", "tail": True, "elevationOnUser": True, "label": "role: assistant · tail"},
    {"role": "system", "tail": False, "elevationOnUser": True, "label": "role: system · no tail"},
    {"role": "user", "tail": False, "elevationOnUser": False, "label": "tail: false"},
    {"role": "assistant", "tail": True, "elevationOnUser": False, "label": "elevationOnUser: false"},
    {"role": "user", "tail": False, "elevationOnUser": False, "label": "chromeless: true"},
)
