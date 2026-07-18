# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Generate Python and QML icon registries from SVG assets. 生成图标注册表。"""

import argparse
import logging
import re
import uuid
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Optional, Sequence, Tuple

if __package__:
    from .maintenance_io import remove_path, replace_many
else:
    from maintenance_io import remove_path, replace_many


logger = logging.getLogger("prismqml.icons")
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_SVG_DIR = PROJECT_ROOT / "prismqml" / "PrismQML" / "controls" / "icons" / "fluent"
DEFAULT_PYTHON_OUTPUT = PROJECT_ROOT / "prismqml" / "python" / "core" / "icons.py"
DEFAULT_QML_OUTPUT = PROJECT_ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Icons.qml"

QML_RESERVED_WORDS = frozenset(
    "break case catch continue debugger default delete do else finally for function if in "
    "instanceof new return switch this throw try typeof var void while with class const enum "
    "export extends import super implements interface let package private protected public static "
    "yield true false null undefined NaN Infinity property signal readonly alias id parent root "
    "anchors width height print".split()
)


class GeneratedOutputMismatch(ValueError):
    """Raised when generated files differ in check mode. 检查模式产物不一致。"""


def to_enum_name(pascal_case: str) -> str:
    """Convert PascalCase to UPPER_SNAKE_CASE. 转为大写蛇形。"""
    result = re.sub(r"([A-Z])", r"_\1", pascal_case).upper().lstrip("_")
    return f"_{result}" if result[:1].isdigit() else result


def to_snake_case(pascal_case: str) -> str:
    """Convert PascalCase to lower_snake_case. 转为小写蛇形。"""
    result = re.sub(r"([A-Z])", r"_\1", pascal_case).lower().lstrip("_")
    return f"_{result}" if result[:1].isdigit() else result


def escape_qml_property_name(name: str) -> str:
    """Escape QML reserved property names. 转义 QML 保留字。"""
    return f"icon_{name}" if name in QML_RESERVED_WORDS else name


def restore_source_name(property_name: str) -> str:
    """Restore the default source name from a QML property. 恢复默认源名称。"""
    return "".join(
        part[:1].upper() + part[1:]
        for part in property_name.split("_")
        if part
    )


def validate_svg_file(svg_file: Path) -> None:
    try:
        root = ET.parse(svg_file).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"invalid SVG XML: {svg_file}: {exc}") from exc
    if root.tag.rsplit("}", 1)[-1].lower() != "svg":
        raise ValueError(f"SVG root element is not <svg>: {svg_file}")


def validate_icon_names(icons: Sequence[str]) -> None:
    """Validate source names and generated identifiers. 验证名称与生成标识符。"""
    if not icons:
        raise ValueError("no SVG icons found")
    groups = {
        "case-insensitive icon": [name.casefold() for name in icons],
        "Python enum": [to_enum_name(name) for name in icons],
        "QML property": [escape_qml_property_name(to_snake_case(name)) for name in icons],
    }
    patterns = {
        "Python enum": r"^[A-Z_][A-Z0-9_]*$",
        "QML property": r"^[a-z_][a-z0-9_]*$",
    }
    for label, pattern in patterns.items():
        invalid = sorted(
            value for value in groups[label] if re.fullmatch(pattern, value) is None
        )
        if invalid:
            raise ValueError(f"invalid {label} names: {invalid}")
    for label, values in groups.items():
        duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
        if duplicates:
            raise ValueError(f"duplicate {label} names: {duplicates}")


def get_icons_from_svg_folder(svg_dir: Path = DEFAULT_SVG_DIR) -> list[str]:
    """Read and validate icon names from an SVG directory. 读取并验证图标名。"""
    svg_dir = Path(svg_dir)
    if not svg_dir.is_dir():
        raise FileNotFoundError(f"SVG directory does not exist: {svg_dir}")
    svg_files = sorted(svg_dir.glob("*.svg"), key=lambda path: path.name.casefold())
    for svg_file in svg_files:
        validate_svg_file(svg_file)
    icons = [svg_file.stem for svg_file in svg_files]
    validate_icon_names(icons)
    return icons


def _python_header(count: int) -> str:
    return f'''# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Icon - Fluent UI icon enum 图标枚举

Auto-generated from SVG assets, do not edit manually! 自动生成，请勿手动编辑！
Total icons: {count}

Usage:
    from prismqml.python.core.icons import Icon
    icon = Icon.CALENDAR
"""

from enum import Enum
from typing import List

from ._icon_enum_runtime import _IconRuntimeMixin


class Icon(_IconRuntimeMixin, str, Enum):
    """Fluent UI icon name enum. Fluent UI 图标名称枚举。"""

'''


def generate_python_enum(icons: Sequence[str]) -> str:
    """Generate the Python icon enum source. 生成 Python 图标枚举源码。"""
    validate_icon_names(icons)
    members = [f'    {to_enum_name(icon)} = "{icon}"' for icon in icons]
    footer = '''

    def __str__(self) -> str:
        return self.value

    @classmethod
    def get_all(cls) -> List[str]:
        """Return all icon values. 返回全部图标值。"""
        return [icon.value for icon in cls]

    @classmethod
    def get_all_enum_names(cls) -> List[str]:
        """Return all enum member names. 返回全部枚举成员名。"""
        return [icon.name for icon in cls]
'''
    return _python_header(len(icons)) + "\n".join(members) + footer


def _qml_header(count: int) -> str:
    return f'''// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Icons - Fluent UI icon enum 图标枚举
// Auto-generated from SVG folder, do not edit manually! 自动生成，请勿手动编辑！
// Total icons: {count} 图标总数
// Usage: Enums.icon.chevron_up 使用方式
pragma Singleton

QtObject {{
    id: root

    // ==================== Public Props 公开属性 ====================
    readonly property string basePath: "fluent/"
    readonly property var resolver: _createResolver()

    // ==================== Internal Props 内部属性 ====================
    readonly property real _startupProfileStart: Date.now()
    readonly property bool _startupProfilingVerboseActive:
        (typeof PrismQmlStartupProfileVerbose !== "undefined" && PrismQmlStartupProfileVerbose)
    readonly property string _iconNames: "'''


def _qml_compact_names(icons: Sequence[str]) -> str:
    return "|" + "|".join(icons) + "|"


def _qml_property_exceptions(icons: Sequence[str]) -> str:
    exceptions = []
    for icon in icons:
        property_name = escape_qml_property_name(to_snake_case(icon))
        if restore_source_name(property_name) != icon:
            exceptions.append(f'        case "{property_name}": return "{icon}"')
    return "\n".join(exceptions)


def _qml_runtime(icons: Sequence[str]) -> str:
    exceptions = _qml_property_exceptions(icons)
    return f'''"
    property var _iconListCache: null

    // ==================== Public Methods 公开方法 ====================
    function path(iconName) {{
        return basePath + iconName + ".svg"
    }}

    // ==================== Internal Methods 内部方法 ====================
    function _propertyNameToSource(propertyName) {{
        switch (propertyName) {{
{exceptions}
        }}
        var parts = propertyName.split("_")
        var sourceName = ""
        for (var index = 0; index < parts.length; ++index) {{
            var part = parts[index]
            if (part.length > 0) {{
                sourceName += part.charAt(0).toUpperCase() + part.slice(1)
            }}
        }}
        return sourceName
    }}

    function _hasIcon(sourceName) {{
        return _iconNames.indexOf("|" + sourceName + "|") >= 0
    }}

    function _resolvePropertyName(propertyName) {{
        if (typeof propertyName !== "string") return undefined
        var sourceName = _propertyNameToSource(propertyName)
        return _hasIcon(sourceName) ? sourceName : undefined
    }}

    function _enumName(sourceName) {{
        var enumName = sourceName.replace(/([A-Z])/g, "_$1").toUpperCase()
        if (enumName.charAt(0) === "_") enumName = enumName.slice(1)
        if (/^[0-9]/.test(enumName)) enumName = "_" + enumName
        return enumName
    }}

    function _getIconList() {{
        if (_iconListCache !== null) return _iconListCache
        var iconList = {{}}
        var names = _iconNames.split("|")
        for (var index = 1; index < names.length - 1; ++index) {{
            var sourceName = names[index]
            iconList[_enumName(sourceName)] = sourceName
        }}
        _iconListCache = iconList
        return _iconListCache
    }}

    function _createResolver() {{
        var callable = function(enumKey) {{
            if (typeof enumKey !== "string") return ""
            var sourceName = root._resolvePropertyName(enumKey.toLowerCase())
            return sourceName === undefined ? "" : sourceName + ".svg"
        }}
        return new Proxy(callable, {{
            get: function(target, propertyName) {{
                if (propertyName === "basePath") return root.basePath
                if (propertyName === "path") return root.path
                if (propertyName === "iconList") return root._getIconList()
                return root._resolvePropertyName(propertyName)
            }}
        }})
    }}

    Component.onCompleted: {{
        if (_startupProfilingVerboseActive) {{
            console.debug("[启动剖析] Icons singleton completed: total " +
                         Math.round(Date.now() - _startupProfileStart) + "ms")
        }}
    }}
}}
'''


def generate_qml_icons(icons: Sequence[str]) -> str:
    """Generate the QML icon singleton source. 生成 QML 图标单例源码。"""
    validate_icon_names(icons)
    return (
        _qml_header(len(icons))
        + _qml_compact_names(icons)
        + _qml_runtime(icons)
    )


def render_outputs(icons: Sequence[str]) -> Tuple[str, str]:
    """Render Python and QML outputs. 渲染 Python 与 QML 产物。"""
    return generate_python_enum(icons), generate_qml_icons(icons)


def _stage_text(destination: Path, content: str) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = destination.with_name(f".{destination.name}.tmp-{uuid.uuid4().hex}")
    with staged.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
    return staged


def _check_outputs(outputs: Sequence[Tuple[Path, str]]) -> None:
    mismatches = []
    for path, expected in outputs:
        if not path.is_file() or path.read_text(encoding="utf-8") != expected:
            mismatches.append(str(path))
    if mismatches:
        raise GeneratedOutputMismatch(f"generated icon outputs are stale: {mismatches}")


def sync_generated_outputs(
    icons: Sequence[str],
    python_output: Path = DEFAULT_PYTHON_OUTPUT,
    qml_output: Path = DEFAULT_QML_OUTPUT,
    check: bool = False,
) -> None:
    """Write or check both generated registries transactionally. 事务写入或检查注册表。"""
    python_content, qml_content = render_outputs(icons)
    outputs = [(Path(python_output), python_content), (Path(qml_output), qml_content)]
    if check:
        _check_outputs(outputs)
        return
    staged = [(_stage_text(path, content), path) for path, content in outputs]
    try:
        replace_many(staged)
    finally:
        for staged_path, _ in staged:
            remove_path(staged_path)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments. 解析命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svg-dir", type=Path, default=DEFAULT_SVG_DIR)
    parser.add_argument("--python-output", type=Path, default=DEFAULT_PYTHON_OUTPUT)
    parser.add_argument("--qml-output", type=Path, default=DEFAULT_QML_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Generate or check icon registries. 生成或检查图标注册表。"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args(argv)
    try:
        icons = get_icons_from_svg_folder(args.svg_dir)
        sync_generated_outputs(icons, args.python_output, args.qml_output, args.check)
    except (FileNotFoundError, OSError, ValueError) as exc:
        logger.error("icon generation failed: %s", exc)
        return 1
    except Exception:
        logger.exception("unexpected icon generation failure")
        return 1
    logger.info("validated %s icons", len(icons))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
