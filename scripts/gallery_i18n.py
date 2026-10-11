# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Offline Gallery i18n extraction and coverage checks. 离线提取并校验 Gallery 国际化。"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

if __package__:
    from ._qml_lint.qml_lexer import sanitize_qml
else:
    from _qml_lint.qml_lexer import sanitize_qml


logger = logging.getLogger("prismqml.gallery_i18n")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
GALLERY_ROOT = PROJECT_ROOT / "examples"
CPP_GALLERY_SOURCE = PROJECT_ROOT / "cpp" / "gallery" / "main.cpp"
I18N_ROOT = PROJECT_ROOT / "prismqml" / "PrismQML" / "i18n"
SOURCE_LANGUAGE = "zh_CN"
PROPERTY_NAMES = (
    "text", "title", "subtitle", "description", "content", "label",
    "placeholderText", "buttonText", "onText", "offText", "emptyText",
    "loadingText", "splashSubtitle", "windowTitle", "message",
    "donutCenterSubtext", "defaultColorText", "customColorText",
    "chooseColorText", "hintText", "section", "name", "actionText",
    "confirmText", "cancelText", "okText", "closeText", "retryText",
    "toolTipText", "headerText", "footerText", "captionText", "statusText",
    "heading", "notes",
)
PROPERTY_PATTERN = re.compile(
    rf"(?P<prefix>[\"']?\b(?:{'|'.join(PROPERTY_NAMES)})[\"']?\s*:\s*)"
    r'(?P<quote>")(?P<value>(?:\\.|[^"\\])*)(?P=quote)'
)
DYNAMIC_PATTERN = re.compile(
    r'(?P<quote>")(?P<value>(?:\\.|[^"\\])*)(?P=quote)'
    r"\s*\+\s*(?P<expression>[A-Za-z_][A-Za-z0-9_.]*)"
)
DYNAMIC_SUFFIX_PATTERN = re.compile(
    r"(?P<expression>[A-Za-z_][A-Za-z0-9_.]*)\s*\+\s*"
    r'(?P<quote>")(?P<value>(?:\\.|[^"\\])*)(?P=quote)'
)
ALL_STRING_PATTERN = re.compile(r'(?P<quote>")(?P<value>(?:\\.|[^"\\])*)(?P=quote)')
TRANSLATION_PATTERN = re.compile(
    r'Fluent\.Translator\.tr\("(?P<key>gallery_[a-f0-9]{16})"'
)
CPP_TRANSLATION_PATTERN = re.compile(r'"(?P<key>gallery_[a-f0-9]{16})"')
TECHNICAL_VALUE_PATTERN = re.compile(
    r"^(?:"
    r"-?\d+(?:\.\d+)?%?|#[0-9A-Fa-f]{3,8}|[A-Z](?:\d+)?|"
    r"[a-z][A-Za-z0-9_.-]*(?::\s*-?\d+(?:\.\d+)?)?|"
    r"[A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z][A-Za-z0-9]*)+|"
    r"[A-Za-z][A-Za-z0-9]*\([^\n]*\)|"
    r"[A-Za-z0-9_./+-]+\s*[:=]\s*[A-Za-z0-9_./+-]+)$"
)


@dataclass(frozen=True)
class GalleryString:
    key: str
    source: str


def translation_key(source: str) -> str:
    return f"gallery_{hashlib.sha256(source.encode('utf-8')).hexdigest()[:16]}"


def _decode_qml_string(value: str) -> str:
    return json.loads(f'"{value}"')


def _is_user_visible(value: str) -> bool:
    stripped = value.strip()
    if not stripped or TECHNICAL_VALUE_PATTERN.fullmatch(stripped):
        return False
    if "/" in stripped or "\\" in stripped or stripped.endswith(".svg"):
        return False
    if re.search(r"(?:^|\s)[0-9a-f]{7,40}\s*[·-]", stripped, re.IGNORECASE):
        return False
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", stripped) and "_" in stripped:
        return False
    if re.fullmatch(r"[A-Za-z0-9_+./:=() -]+", stripped):
        return False
    return bool(re.search(r"[A-Za-z\u0080-\uffff]", stripped))


# Gallery copy policy: every visible-text literal that reads as a phrase must be
# authored in the source language (zh_CN) and consumed through Fluent.Translator.
# Single identifiers, API signatures, paths and protected product terms stay English
# in every catalog, so they never enter the pipeline.
# Gallery 文案策略：凡是读起来像短语的可见文案，都必须以源语言（zh_CN）编写并经
# Fluent.Translator 消费；单词标识符、API 签名、路径与受保护产品术语在所有语言目录
# 中都保持英文，因此不进入流水线。
STRUCTURAL_CHARACTERS = frozenset("_+/\\().:=·[]{}<>@#*|&^%~`")
FUNCTION_WORDS = frozenset(
    """the a an of to in on for with and or is are be by from at this that
    you your it its not no as into over when then if else than
    down up out only first next last each every some any all""".split()
)
PROTECTED_TERMS = frozenset(
    term.lower()
    for term in (
        "PrismQML", "Gallery", "C++", "DRY", "GitHub Releases", "GitHub", "Release",
        "Updater", "UpdateDialog", "ProgressDialog", "Toast", "InfoBar", "Inno Setup",
        "ToolButton", "PushButton", "Button", "PipsPager", "HorizontalPipsPager",
        "VerticalPipsPager", "Carousel", "FlowLayout", "MatrixRain", "TeachingTip",
        "TeachingTour", "StateWidget", "DateTimePicker", "ScrollBar", "ShortcutEditor",
        "AvatarSelector", "Badge", "ContextMenu", "ImageWidget", "Timeline", "ListView",
        "TableView", "TreeView", "BreadcrumbBar", "StackedWidget", "Stepper", "DWM",
        "Windows", "DPI", "Mica", "API", "QML", "ISS",
        # Skin display names are proper nouns 皮肤显示名是专有名词
        "Fluent", "Neo", "Ticket", "Neobrutalism", "Vintage Ticket",
    )
)
CAMEL_TOKEN = re.compile(r"[a-z][A-Z]")
HAN_CHARACTER = re.compile(r"[\u3400-\u9fff]")
CAPITALIZED_TOKEN = re.compile(r"[A-Z][A-Za-z0-9]*$")
QML_MODULE_ROOT = PROJECT_ROOT / "prismqml" / "PrismQML"


def _registered_component_names() -> frozenset[str]:
    """Collect every registered QML type name. 收集全部已注册 QML 类型名。"""
    names: set[str] = set()
    for qmldir in QML_MODULE_ROOT.rglob("qmldir"):
        for line in qmldir.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if not parts or parts[0].startswith("#") or not parts[-1].endswith(".qml"):
                continue
            names.add(parts[1] if parts[0] in {"singleton", "internal"} else parts[0])
    return frozenset(names)


COMPONENT_NAMES = _registered_component_names()


@dataclass(frozen=True)
class GalleryCopy:
    """One untranslated copy literal and its position. 一条未本地化文案及其位置。"""

    path: str
    line: int
    source: str


def is_translatable_copy(value: str) -> bool:
    """Return True when a literal reads as copy that must be localized.

    判定字面量是否为必须本地化的文案。单词标识符、受保护术语、结构符号标记的 API
    签名与 camelCase/缩写标识都不算文案；首字母大写的单词只要不是已注册组件名或
    受保护术语，就是按钮/选项一类的内容标签。
    """
    stripped = value.strip()
    if not stripped or HAN_CHARACTER.search(stripped):
        return False
    if not re.search(r"[A-Za-z]", stripped):
        return False
    tokens = re.findall(r"[A-Za-z]+", stripped)
    if len(stripped.split()) == 1:
        # Single tokens are API value captions when lowercase, and component, skin,
        # acronym or camelCase names when they look like identifiers; every other
        # capitalized word is a content label such as a button or option caption.
        # 单词级：小写是 API 取值标签，组件/皮肤/缩写/camelCase 是标识符，其余首字母
        # 大写的单词才是按钮、选项一类的内容文案。
        if not CAPITALIZED_TOKEN.fullmatch(stripped):
            return False
        if len(stripped) == 1 or stripped.isupper() or CAMEL_TOKEN.search(stripped):
            return False
        return (
            stripped not in COMPONENT_NAMES
            and stripped.lower() not in PROTECTED_TERMS
        )
    if all(token.lower() in PROTECTED_TERMS or token.isdigit() for token in tokens):
        return False
    words = [word for word in stripped.split() if word.isalpha()]
    if any(word.lower() in FUNCTION_WORDS for word in words):
        return True
    if any(character in STRUCTURAL_CHARACTERS for character in stripped):
        return False
    if any(token.isupper() and len(token) >= 2 for token in tokens):
        return False
    if any(CAMEL_TOKEN.search(token) for token in tokens):
        return False
    return True


def _is_code_literal(code_mask: str, match: re.Match[str]) -> bool:
    """Return True when a match sits in real code rather than a comment. 判定匹配位于代码而非注释。"""
    return "v" in code_mask[match.start() : match.end()]


def _is_untranslated_literal(value: str) -> bool:
    """Return True when one literal must be localized. 判定单条字面量是否需要本地化。"""
    if is_translatable_copy(value):
        return True
    # Label prefixes such as "mode: " stay readable only when the label is localized.
    # "mode: " 这类标签前缀只有本地化后才可读。
    return value.strip().endswith(":") and bool(re.search(r"[A-Za-z]{2,}", value))


def _is_untranslated_fragment(value: str) -> bool:
    """Return True when a concatenated label fragment must be localized.

    判定拼接片段（如 "invoked " + index）是否为需要本地化的标签；对象名与路径前缀不算。
    """
    stripped = value.strip()
    if " " not in value or len(re.findall(r"[A-Za-z]", stripped)) < 3:
        return False
    return not any(character in STRUCTURAL_CHARACTERS for character in stripped)


def find_untranslated_copy(root: Path = GALLERY_ROOT) -> list[GalleryCopy]:
    """List visible-text literals that still carry untranslated copy.

    列出仍以英文文案形式硬编码的可见字面量；注释中的同名文本不算。
    """
    found: dict[tuple[str, int, str], GalleryCopy] = {}
    for path in _gallery_files(root):
        content = path.read_text(encoding="utf-8")
        code_mask = sanitize_qml(content, mask_strings=True, mark_values=True)
        relative = path.relative_to(root).as_posix()

        def record(match: re.Match[str], value: str) -> None:
            item = GalleryCopy(
                relative, content.count("\n", 0, match.start()) + 1, value
            )
            found[(item.path, item.line, item.source)] = item

        for match in PROPERTY_PATTERN.finditer(content):
            if not _is_code_literal(code_mask, match):
                continue
            value = _decode_qml_string(match.group("value"))
            if _is_untranslated_literal(value):
                record(match, value)
        for pattern in (DYNAMIC_PATTERN, DYNAMIC_SUFFIX_PATTERN):
            for match in pattern.finditer(content):
                if not _is_code_literal(code_mask, match):
                    continue
                value = _decode_qml_string(match.group("value"))
                if _is_untranslated_literal(value) or _is_untranslated_fragment(value):
                    record(match, value)
    return sorted(found.values(), key=lambda item: (item.path, item.line, item.source))


def _gallery_files(root: Path = GALLERY_ROOT) -> list[Path]:
    return sorted(root.rglob("*.qml"))


def _source_values(content: str) -> Iterable[str]:
    for pattern in (PROPERTY_PATTERN, DYNAMIC_PATTERN, DYNAMIC_SUFFIX_PATTERN):
        for match in pattern.finditer(content):
            value = _decode_qml_string(match.group("value"))
            if _is_user_visible(value):
                yield value
    for match in ALL_STRING_PATTERN.finditer(content):
        value = _decode_qml_string(match.group("value"))
        if re.search(r"[\u3400-\u9fff]", value) and _is_user_visible(value):
            yield value


def extract_source_strings(root: Path = GALLERY_ROOT) -> list[GalleryString]:
    values = {
        value for path in _gallery_files(root)
        for value in _source_values(path.read_text(encoding="utf-8"))
    }
    return [GalleryString(translation_key(value), value) for value in sorted(values)]


def _tr_expression(key: str) -> str:
    return f'Fluent.Translator.tr("{key}", Fluent.Translator._v)'


def _localize_content(content: str) -> tuple[str, list[GalleryString]]:
    strings: dict[str, GalleryString] = {}
    code_mask = sanitize_qml(content, mask_strings=True, mark_values=True)

    def is_code_match(match: re.Match[str]) -> bool:
        return "v" in code_mask[match.start() : match.end()]

    def item(value: str) -> GalleryString:
        result = GalleryString(translation_key(value), value)
        strings[result.key] = result
        return result

    def replace_property(match: re.Match[str]) -> str:
        if not is_code_match(match):
            return match.group(0)
        value = _decode_qml_string(match.group("value"))
        if not _is_user_visible(value):
            return match.group(0)
        return match.group("prefix") + _tr_expression(item(value).key)

    localized = PROPERTY_PATTERN.sub(replace_property, content)
    code_mask = sanitize_qml(localized, mask_strings=True, mark_values=True)

    def replace_dynamic(match: re.Match[str]) -> str:
        if not is_code_match(match):
            return match.group(0)
        value = _decode_qml_string(match.group("value"))
        if not _is_user_visible(value):
            return match.group(0)
        return f'Fluent.Translator.tr("{item(value).key}") + {match.group("expression")}'

    localized = DYNAMIC_PATTERN.sub(replace_dynamic, localized)
    code_mask = sanitize_qml(localized, mask_strings=True, mark_values=True)

    def replace_dynamic_suffix(match: re.Match[str]) -> str:
        if not is_code_match(match):
            return match.group(0)
        value = _decode_qml_string(match.group("value"))
        if not _is_user_visible(value):
            return match.group(0)
        return f'{match.group("expression")} + Fluent.Translator.tr("{item(value).key}")'

    localized = DYNAMIC_SUFFIX_PATTERN.sub(replace_dynamic_suffix, localized)
    code_mask = sanitize_qml(localized, mask_strings=True, mark_values=True)

    def replace_cjk_literal(match: re.Match[str]) -> str:
        if not is_code_match(match):
            return match.group(0)
        value = _decode_qml_string(match.group("value"))
        if not re.search(r"[\u3400-\u9fff]", value):
            return match.group(0)
        return _tr_expression(item(value).key)

    localized = ALL_STRING_PATTERN.sub(replace_cjk_literal, localized)
    return localized, sorted(strings.values(), key=lambda value: value.key)


def _update_source_catalog(strings: dict[str, GalleryString]) -> None:
    path = I18N_ROOT / f"{SOURCE_LANGUAGE}.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    catalog.update({key: value.source for key, value in strings.items()})
    path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )


def localize_sources(root: Path = GALLERY_ROOT, check: bool = False) -> int:
    changed: list[Path] = []
    strings: dict[str, GalleryString] = {}
    for path in _gallery_files(root):
        content = path.read_text(encoding="utf-8")
        localized, extracted = _localize_content(content)
        strings.update({value.key: value for value in extracted})
        if localized != content:
            changed.append(path)
            if not check:
                path.write_text(localized, encoding="utf-8", newline="\n")
    if check and changed:
        names = [path.relative_to(root).as_posix() for path in changed]
        raise ValueError(f"Gallery contains untranslated UI literals: {names}")
    if not check:
        _update_source_catalog(strings)
    return len(strings)


def load_catalogs(i18n_root: Path = I18N_ROOT) -> dict[str, dict[str, str]]:
    catalogs = {}
    for path in sorted(i18n_root.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"translation catalog is not an object: {path}")
        catalogs[path.stem] = data
    if SOURCE_LANGUAGE not in catalogs:
        raise ValueError(f"missing source catalog: {SOURCE_LANGUAGE}.json")
    return catalogs


def referenced_keys(root: Path = GALLERY_ROOT) -> set[str]:
    keys = {
        match.group("key")
        for path in _gallery_files(root)
        for match in TRANSLATION_PATTERN.finditer(path.read_text(encoding="utf-8"))
    }
    if CPP_GALLERY_SOURCE.exists():
        keys.update(
            match.group("key")
            for match in CPP_TRANSLATION_PATTERN.finditer(
                CPP_GALLERY_SOURCE.read_text(encoding="utf-8")
            )
        )
    return keys


def validate_catalogs(root: Path = GALLERY_ROOT, i18n_root: Path = I18N_ROOT) -> int:
    referenced = referenced_keys(root)
    failures = []
    for language, catalog in load_catalogs(i18n_root).items():
        missing = sorted(referenced - set(catalog))
        empty = sorted(key for key in referenced if not catalog.get(key, "").strip())
        if missing or empty:
            failures.append(f"{language}: missing={missing}, empty={empty}")
    if failures:
        raise ValueError("Gallery translation coverage failed: " + "; ".join(failures))
    return len(referenced)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--localize", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args(argv)
    try:
        if args.localize:
            logger.info("processed %s Gallery source strings", localize_sources(check=args.check))
        if args.check or not args.localize:
            logger.info("validated %s Gallery translation keys", validate_catalogs())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        logger.error("Gallery i18n maintenance failed: %s", exc)
        return 1
    except Exception:
        logger.exception("unexpected Gallery i18n maintenance failure")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
