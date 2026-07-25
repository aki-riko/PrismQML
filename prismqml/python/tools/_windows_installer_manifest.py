# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Windows installer manifest validation. Windows 安装器清单校验。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from string import Formatter
from typing import Any, Dict, Mapping, Optional
from urllib.parse import urlparse


SCHEMA_VERSION = 1
EXIT_MANIFEST = 3
EXIT_STALE_OUTPUT = 4
EXIT_IO = 5
DEFAULT_OUTPUT_NAME = "{name}-Setup-{version}"
DEFAULT_INSTALLER_OUTPUT_DIR = "dist_installer"
DEFAULT_CHINESE_MESSAGES_FILE = "compiler:Languages\\ChineseSimplified.isl"
VERSION_PATTERN = re.compile(r"[0-9]+(?:\.[0-9]+){2,3}\Z")
AUMID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{1,127}\Z")
UUID_PATTERN = re.compile(
    r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-"
    r"[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\Z"
)
INVALID_NAME_CHARS = frozenset('<>:"/\\|?*')
INVALID_PATH_CHARS = frozenset('<>:"|?*{}')
INNO_CONSTANT_CHARS = frozenset("{}")
WINDOWS_RESERVED_STEMS = frozenset({
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
})
OUTPUT_NAME_FIELDS = frozenset({"name", "version"})
INSTALL_SCOPE_VALUES = {
    "user": ("{localappdata}\\Programs\\{#PrismAppName}", "lowest"),
    "machine": ("{autopf}\\{#PrismAppName}", "admin"),
}
REQUIRED_FIELDS = frozenset({
    "schema",
    "app_id",
    "name",
    "publisher",
    "executable",
    "aumid",
    "install_scope",
    "dist_dir",
})
OPTIONAL_FIELDS = frozenset({
    "homepage",
    "icon",
    "extension_include",
    "installer_output_dir",
    "output_name",
    "chinese_messages_file",
})


class ManifestError(ValueError):
    """Stable manifest or generated-output failure. 稳定的清单或生成输出错误。"""

    def __init__(self, code: str, message: str, exit_code: int = EXIT_MANIFEST):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


@dataclass(frozen=True)
class WindowsInstallerManifest:
    """Validated application-specific installer fields. 已校验的应用安装字段。"""

    source_path: Path
    app_id: str
    name: str
    publisher: str
    executable: str
    aumid: str
    install_scope: str
    dist_dir: str
    homepage: str = ""
    icon: str = ""
    extension_include: str = ""
    installer_output_dir: str = DEFAULT_INSTALLER_OUTPUT_DIR
    output_name: str = DEFAULT_OUTPUT_NAME
    chinese_messages_file: str = DEFAULT_CHINESE_MESSAGES_FILE


def _manifest_error(field: str, detail: str) -> ManifestError:
    return ManifestError("invalid_manifest", f"{field}: {detail}")


def _literal(data: Mapping[str, Any], field: str, default: Optional[str] = None) -> str:
    value = data.get(field, default)
    if not isinstance(value, str) or not value.strip():
        raise _manifest_error(field, "must be a non-empty string")
    value = value.strip()
    if any(char in value for char in ('"', "\r", "\n")):
        raise _manifest_error(field, "contains unsupported Inno Setup characters")
    return value


def _optional_literal(data: Mapping[str, Any], field: str) -> str:
    value = data.get(field, "")
    if value == "":
        return ""
    return _literal(data, field)


def _reject_inno_constants(field: str, value: str) -> str:
    if any(char in value for char in INNO_CONSTANT_CHARS):
        raise _manifest_error(field, "contains unsupported Inno Setup constants")
    return value


def _inno_literal(
    data: Mapping[str, Any], field: str, default: Optional[str] = None
) -> str:
    return _reject_inno_constants(field, _literal(data, field, default))


def _validate_windows_segment(field: str, value: str) -> str:
    if value in {".", ".."}:
        raise _manifest_error(field, "must not be '.' or '..'")
    if value.endswith((" ", ".")):
        raise _manifest_error(field, "must not end with a space or dot")
    stem = value.split(".", 1)[0].upper()
    if stem in WINDOWS_RESERVED_STEMS:
        raise _manifest_error(field, f"uses reserved Windows name '{stem}'")
    return value


def _relative_path(data: Mapping[str, Any], field: str, default: Optional[str] = None) -> str:
    value = _literal(data, field, default).replace("\\", "/")
    path = Path(value)
    windows_path = PureWindowsPath(value)
    if path.is_absolute() or windows_path.is_absolute() or ".." in path.parts:
        raise _manifest_error(field, "must be a project-relative path without '..'")
    if any(
        char in INVALID_PATH_CHARS
        for part in windows_path.parts
        for char in part
    ):
        raise _manifest_error(field, "contains characters invalid in Windows paths")
    for part in windows_path.parts:
        _validate_windows_segment(field, part)
    return path.as_posix()


def _optional_relative_path(data: Mapping[str, Any], field: str) -> str:
    if data.get(field, "") == "":
        return ""
    return _relative_path(data, field)


def _validate_schema(data: Mapping[str, Any]) -> None:
    if data.get("schema") != SCHEMA_VERSION:
        raise _manifest_error("schema", f"must equal {SCHEMA_VERSION}")
    unknown = sorted(set(data) - REQUIRED_FIELDS - OPTIONAL_FIELDS)
    if unknown:
        raise _manifest_error("unknown", f"unsupported fields: {unknown}")
    missing = sorted(REQUIRED_FIELDS - set(data))
    if missing:
        raise _manifest_error("manifest", f"missing required fields: {missing}")


def _validate_identity(data: Mapping[str, Any]) -> Dict[str, str]:
    app_id = _literal(data, "app_id")
    if "{" in app_id or "}" in app_id:
        raise _manifest_error("app_id", "store the identifier without braces")
    if UUID_PATTERN.fullmatch(app_id) is None:
        raise _manifest_error("app_id", "must be a canonical UUID without braces")
    name = _inno_literal(data, "name")
    if any(char in name for char in INVALID_NAME_CHARS):
        raise _manifest_error("name", "contains characters invalid in install paths")
    _validate_windows_segment("name", name)
    executable = _inno_literal(data, "executable")
    if PureWindowsPath(executable).name != executable or not executable.lower().endswith(".exe"):
        raise _manifest_error("executable", "must be one .exe file name without directories")
    _validate_windows_segment("executable", executable)
    aumid = _literal(data, "aumid")
    if AUMID_PATTERN.fullmatch(aumid) is None:
        raise _manifest_error("aumid", "must contain only letters, digits, dot, dash, or underscore")
    return {
        "app_id": app_id,
        "name": name,
        "publisher": _inno_literal(data, "publisher"),
        "executable": executable,
        "aumid": aumid,
    }


def _validate_homepage(data: Mapping[str, Any]) -> str:
    homepage = _optional_literal(data, "homepage")
    if not homepage:
        return ""
    _reject_inno_constants("homepage", homepage)
    parsed = urlparse(homepage)
    if parsed.scheme != "https" or not parsed.netloc:
        raise _manifest_error("homepage", "must be an absolute HTTPS URL")
    return homepage


def _validate_scope(data: Mapping[str, Any]) -> str:
    install_scope = _literal(data, "install_scope")
    if install_scope not in {"user", "machine"}:
        raise _manifest_error("install_scope", "must be 'user' or 'machine'")
    return install_scope


def _validate_output_name(data: Mapping[str, Any]) -> str:
    value = _literal(data, "output_name", DEFAULT_OUTPUT_NAME)
    try:
        fields = list(Formatter().parse(value))
    except (KeyError, ValueError) as exc:
        raise _manifest_error("output_name", f"invalid format pattern: {exc}") from exc
    for _literal_text, field_name, format_spec, conversion in fields:
        if field_name is not None and field_name not in OUTPUT_NAME_FIELDS:
            raise _manifest_error("output_name", "only {name} and {version} are allowed")
        if format_spec or conversion:
            raise _manifest_error("output_name", "format specifiers and conversions are not allowed")
    rendered = value.format(name="App", version="1.0.0")
    if any(char in rendered for char in INVALID_NAME_CHARS):
        raise _manifest_error("output_name", "renders an invalid Windows file name")
    _reject_inno_constants("output_name", rendered)
    _validate_windows_segment("output_name", rendered)
    if rendered.lower().endswith(".exe"):
        raise _manifest_error("output_name", "must omit the compiler-added .exe suffix")
    return value


def _validate_messages_file(data: Mapping[str, Any]) -> str:
    value = _literal(data, "chinese_messages_file", DEFAULT_CHINESE_MESSAGES_FILE)
    _reject_inno_constants("chinese_messages_file", value)
    if value.lower().startswith("compiler:"):
        return value.replace("/", "\\")
    normalized = dict(data)
    normalized["chinese_messages_file"] = value
    return _relative_path(normalized, "chinese_messages_file")


def load_manifest(path: Path) -> WindowsInstallerManifest:
    """Load and validate one schema-v1 JSON manifest. 加载并校验清单。"""
    source_path = Path(path).resolve()
    try:
        data = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestError("invalid_manifest", f"cannot read manifest: {exc}") from exc
    if not isinstance(data, dict):
        raise _manifest_error("manifest", "root must be a JSON object")
    _validate_schema(data)
    identity = _validate_identity(data)
    return WindowsInstallerManifest(
        source_path=source_path,
        install_scope=_validate_scope(data),
        dist_dir=_relative_path(data, "dist_dir"),
        homepage=_validate_homepage(data),
        icon=_optional_relative_path(data, "icon"),
        extension_include=_optional_relative_path(data, "extension_include"),
        installer_output_dir=_relative_path(
            data, "installer_output_dir", DEFAULT_INSTALLER_OUTPUT_DIR
        ),
        output_name=_validate_output_name(data),
        chinese_messages_file=_validate_messages_file(data),
        **identity,
    )


def _render_output_name(manifest: WindowsInstallerManifest, version: str) -> str:
    rendered = manifest.output_name.format(name=manifest.name, version=version)
    if not rendered or any(char in rendered for char in INVALID_NAME_CHARS):
        raise _manifest_error("output_name", "renders an invalid Windows file name")
    _reject_inno_constants("output_name", rendered)
    _validate_windows_segment("output_name", rendered)
    return rendered
