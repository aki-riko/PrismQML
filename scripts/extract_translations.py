# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Extract legacy inline translations or validate external JSON. 提取或验证翻译。"""

import argparse
import json
import logging
import re
import tempfile
from pathlib import Path
from typing import Dict, Optional, Sequence

if __package__:
    from .maintenance_io import remove_path, replace_many
else:
    from maintenance_io import remove_path, replace_many


logger = logging.getLogger("prismqml.translations")
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_QML_INPUT = PROJECT_ROOT / "prismqml" / "PrismQML" / "Translator.qml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "prismqml" / "PrismQML" / "i18n"
TRANSLATIONS_PATTERN = re.compile(r"readonly property var translations:\s*\(\s*\{")
LANGUAGE_PATTERN = re.compile(r'"([A-Za-z_]+)"\s*:\s*\{')
PAIR_PATTERN = re.compile(r'"((?:\\.|[^"\\])*)"\s*:\s*"((?:\\.|[^"\\])*)"')


def _balanced_object(content: str, start: int) -> tuple[str, int]:
    depth = 0
    in_string = False
    escaped = False
    for position in range(start, len(content)):
        char = content[position]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return content[start : position + 1], position + 1
    raise ValueError("unterminated translation object")


def _decode_json_string(value: str) -> str:
    return json.loads(f'"{value}"')


def _parse_language_block(block: str, language: str) -> Dict[str, str]:
    entries = {
        _decode_json_string(match.group(1)): _decode_json_string(match.group(2))
        for match in PAIR_PATTERN.finditer(block)
    }
    if not entries:
        raise ValueError(f"translation language has no string entries: {language}")
    return entries


def extract_embedded_translations(content: str) -> Optional[Dict[str, Dict[str, str]]]:
    """Parse a legacy inline translations object. 解析旧版内联翻译对象。"""
    match = TRANSLATIONS_PATTERN.search(content)
    if match is None:
        return None
    outer, _ = _balanced_object(content, match.end() - 1)
    translations = {}
    position = 1
    while language_match := LANGUAGE_PATTERN.search(outer, position):
        language = language_match.group(1)
        block, position = _balanced_object(outer, language_match.end() - 1)
        translations[language] = _parse_language_block(block, language)
    if not translations:
        raise ValueError("inline translations object contains no languages")
    return translations


def _load_json_files(output_dir: Path) -> Dict[str, Dict[str, str]]:
    if not output_dir.is_dir():
        raise FileNotFoundError(f"translation directory does not exist: {output_dir}")
    translations = {}
    for path in sorted(output_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not data:
            raise ValueError(f"translation JSON must be a non-empty object: {path}")
        if not all(isinstance(key, str) and isinstance(value, str) for key, value in data.items()):
            raise ValueError(f"translation JSON values must be strings: {path}")
        translations[path.stem] = data
    if "en" not in translations:
        raise ValueError("translation directory must contain en.json")
    return translations


def validate_external_translations(qml_content: str, output_dir: Path) -> int:
    """Validate Translator language declarations against JSON files. 验证语言声明与 JSON。"""
    translations = _load_json_files(output_dir)
    declared = set(re.findall(r'code:\s*"([A-Za-z_]+)"', qml_content)) - {"auto"}
    if not declared:
        raise ValueError("Translator.qml declares no supported languages")
    missing = sorted(declared - set(translations))
    extra = sorted(set(translations) - declared)
    if missing or extra:
        raise ValueError(f"translation language mismatch: missing={missing}, extra={extra}")
    return len(translations)


def _render_json(entries: Dict[str, str]) -> str:
    return json.dumps(entries, ensure_ascii=False, indent=2) + "\n"


def _check_translation_outputs(
    translations: Dict[str, Dict[str, str]], output_dir: Path
) -> None:
    expected_names = {f"{language}.json" for language in translations}
    actual_names = (
        {path.name for path in output_dir.glob("*.json")}
        if output_dir.is_dir()
        else set()
    )
    mismatches = sorted(expected_names.symmetric_difference(actual_names))
    for language, entries in translations.items():
        path = output_dir / f"{language}.json"
        if not path.is_file() or path.read_text(encoding="utf-8") != _render_json(entries):
            mismatches.append(path.name)
    if mismatches:
        raise ValueError(f"translation outputs are stale: {sorted(set(mismatches))}")


def sync_translation_outputs(
    translations: Dict[str, Dict[str, str]], output_dir: Path, check: bool = False
) -> None:
    """Write or check extracted JSON as one directory transaction. 原子写入或检查 JSON。"""
    output_dir = Path(output_dir)
    if check:
        _check_translation_outputs(translations, output_dir)
        return
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".extract-translations-", dir=output_dir.parent))
    try:
        for language, entries in translations.items():
            path = stage / f"{language}.json"
            with path.open("w", encoding="utf-8", newline="\n") as stream:
                stream.write(_render_json(entries))
        _load_json_files(stage)
        replace_many([(stage, output_dir)])
    finally:
        remove_path(stage)


def run(input_path: Path, output_dir: Path, check: bool = False) -> int:
    """Extract legacy data or validate the current external layout. 执行提取或验证。"""
    input_path = Path(input_path)
    if not input_path.is_file():
        raise FileNotFoundError(f"Translator input does not exist: {input_path}")
    content = input_path.read_text(encoding="utf-8")
    translations = extract_embedded_translations(content)
    if translations is None:
        return validate_external_translations(content, Path(output_dir))
    sync_translation_outputs(translations, Path(output_dir), check)
    return len(translations)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments. 解析命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_QML_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run translation extraction or validation. 执行翻译提取或验证。"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args(argv)
    try:
        count = run(args.input, args.output_dir, args.check)
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError) as exc:
        logger.error("translation maintenance failed: %s", exc)
        return 1
    except Exception:
        logger.exception("unexpected translation maintenance failure")
        return 1
    logger.info("validated %s translation languages", count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
