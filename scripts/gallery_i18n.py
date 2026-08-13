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
    "chooseColorText",
)
PROPERTY_PATTERN = re.compile(
    rf"(?P<prefix>\b(?:{'|'.join(PROPERTY_NAMES)})\s*:\s*)"
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

    def item(value: str) -> GalleryString:
        result = GalleryString(translation_key(value), value)
        strings[result.key] = result
        return result

    def replace_property(match: re.Match[str]) -> str:
        value = _decode_qml_string(match.group("value"))
        if not _is_user_visible(value):
            return match.group(0)
        return match.group("prefix") + _tr_expression(item(value).key)

    localized = PROPERTY_PATTERN.sub(replace_property, content)

    def replace_dynamic(match: re.Match[str]) -> str:
        value = _decode_qml_string(match.group("value"))
        if not _is_user_visible(value):
            return match.group(0)
        return f'Fluent.Translator.tr("{item(value).key}") + {match.group("expression")}'

    localized = DYNAMIC_PATTERN.sub(replace_dynamic, localized)

    def replace_dynamic_suffix(match: re.Match[str]) -> str:
        value = _decode_qml_string(match.group("value"))
        if not _is_user_visible(value):
            return match.group(0)
        return f'{match.group("expression")} + Fluent.Translator.tr("{item(value).key}")'

    localized = DYNAMIC_SUFFIX_PATTERN.sub(replace_dynamic_suffix, localized)

    def replace_cjk_literal(match: re.Match[str]) -> str:
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
