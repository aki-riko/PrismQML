# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Build manually curated Gallery locale catalogs. 构建人工校订的 Gallery 语言目录。"""

from __future__ import annotations

import json
import re
from pathlib import Path

from _manual_gallery_locale_data import LOCALE_DATA


ROOT = Path(__file__).resolve().parents[1]
I18N_ROOT = ROOT / "prismqml" / "PrismQML" / "i18n"
PROTECTED_TERMS = (
    "PrismQML", "Gallery", "C++", "DRY", "GitHub Releases", "GitHub", "Release",
    "Updater", "UpdateDialog", "ProgressDialog", "Toast", "InfoBar", "Inno Setup",
    "ToolButton", "PushButton", "Button", "PipsPager", "HorizontalPipsPager",
    "VerticalPipsPager", "Carousel", "FlowLayout", "MatrixRain", "TeachingTip",
    "TeachingTour", "StateWidget", "DateTimePicker", "ScrollBar", "ShortcutEditor",
    "AvatarSelector", "Badge", "ContextMenu", "ImageWidget", "Timeline", "ListView",
    "TableView", "TreeView", "BreadcrumbBar", "StackedWidget", "Stepper", "DWM",
    "Windows", "DPI", "Mica", "API", "QML", "ISS",
)


def _replace_words(value: str, replacements: dict[str, str]) -> str:
    protected: dict[str, str] = {}
    result = value
    for index, term in enumerate(sorted(PROTECTED_TERMS, key=len, reverse=True)):
        marker = f"@@{index}@@"
        if term in result:
            protected[marker] = term
            result = result.replace(term, marker)
    for source, target in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        result = re.sub(rf"\b{re.escape(source)}\b", target, result, flags=re.IGNORECASE)
    for marker, term in protected.items():
        result = result.replace(marker, term)
    return result


def _localize_patterns(value: str, data: dict[str, object]) -> str:
    patterns = (
        (r"^Multi-select (\d+)$", lambda m: f"{data['multi']} {m.group(1)}"),
        (r"^Option (\d+)$", lambda m: f"{data['option']} {m.group(1)}"),
        (r"^Option ([A-Z])$", lambda m: f"{data['option']} {m.group(1)}"),
        (r"^Tag (\d+)$", lambda m: f"{data['tag']} {m.group(1)}"),
        (r"^Content (\d+)$", lambda m: f"{data['content']} {m.group(1)}"),
        (r"^Help (\d+)$", lambda m: f"{data['help']} {m.group(1)}"),
        (r"^Product ([A-E])$", lambda m: f"{data['product']} {m.group(1)}"),
    )
    for pattern, replacement in patterns:
        match = re.fullmatch(pattern, value)
        if match:
            return replacement(match)
    return _replace_words(value, data["replacements"])


def main() -> int:
    english = json.loads((I18N_ROOT / "en.json").read_text(encoding="utf-8"))
    source = json.loads((I18N_ROOT / "zh_CN.json").read_text(encoding="utf-8"))
    keys = [key for key in source if key.startswith("gallery_")]
    for language, data in LOCALE_DATA.items():
        path = I18N_ROOT / f"{language}.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        existing = {
            key: catalog[key] for key in keys
            if catalog[key] != source[key]
        }
        for key in keys:
            catalog[key] = _localize_patterns(english[key], data)
        catalog.update(existing)
        path.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
