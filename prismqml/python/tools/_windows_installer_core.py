# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Deterministic Windows installer generation core. 确定性 Windows 安装器生成核心。"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from importlib import resources
from pathlib import Path, PureWindowsPath
from string import Template
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
INVALID_NAME_CHARS = frozenset('<>:"/\\|?*')
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


@dataclass(frozen=True)
class InstallerResult:
    """One deterministic generation or check result. 一次确定性生成或检查结果。"""

    output: Path
    sha256: str
    changed: bool = False


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


def _relative_path(data: Mapping[str, Any], field: str, default: Optional[str] = None) -> str:
    value = _literal(data, field, default).replace("\\", "/")
    path = Path(value)
    windows_path = PureWindowsPath(value)
    if path.is_absolute() or windows_path.is_absolute() or ".." in path.parts:
        raise _manifest_error(field, "must be a project-relative path without '..'")
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
    name = _literal(data, "name")
    if any(char in name for char in INVALID_NAME_CHARS):
        raise _manifest_error("name", "contains characters invalid in install paths")
    executable = _literal(data, "executable")
    if PureWindowsPath(executable).name != executable or not executable.lower().endswith(".exe"):
        raise _manifest_error("executable", "must be one .exe file name without directories")
    aumid = _literal(data, "aumid")
    if AUMID_PATTERN.fullmatch(aumid) is None:
        raise _manifest_error("aumid", "must contain only letters, digits, dot, dash, or underscore")
    return {
        "app_id": app_id,
        "name": name,
        "publisher": _literal(data, "publisher"),
        "executable": executable,
        "aumid": aumid,
    }


def _validate_homepage(data: Mapping[str, Any]) -> str:
    homepage = _optional_literal(data, "homepage")
    if not homepage:
        return ""
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
    if "/" in value or "\\" in value:
        raise _manifest_error("output_name", "must be a file name pattern without directories")
    try:
        value.format(name="App", version="1.0.0")
    except (KeyError, ValueError) as exc:
        raise _manifest_error("output_name", f"invalid format pattern: {exc}") from exc
    return value


def _validate_messages_file(data: Mapping[str, Any]) -> str:
    value = _literal(data, "chinese_messages_file", DEFAULT_CHINESE_MESSAGES_FILE)
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


def default_output_path(manifest: WindowsInstallerManifest) -> Path:
    """Return the generated ISS path beside the manifest. 返回清单旁的生成路径。"""
    return manifest.source_path.with_name("installer.generated.iss")


def _project_path(manifest: WindowsInstallerManifest, value: str) -> Path:
    return (manifest.source_path.parent / Path(value)).resolve()


def _path_for_output(
    manifest: WindowsInstallerManifest, output_path: Path, value: str
) -> str:
    target = _project_path(manifest, value)
    try:
        relative = os.path.relpath(target, Path(output_path).resolve().parent)
    except ValueError as exc:
        raise _manifest_error("output", "must be on the same drive as manifest paths") from exc
    return str(PureWindowsPath(relative))


def _messages_for_output(
    manifest: WindowsInstallerManifest, output_path: Path
) -> str:
    value = manifest.chinese_messages_file
    if value.lower().startswith("compiler:"):
        return value
    return _path_for_output(manifest, output_path, value)


def _render_output_name(manifest: WindowsInstallerManifest, version: str) -> str:
    rendered = manifest.output_name.format(name=manifest.name, version=version)
    if not rendered or any(char in rendered for char in INVALID_NAME_CHARS):
        raise _manifest_error("output_name", "renders an invalid Windows file name")
    return rendered


def _template_text() -> str:
    template = resources.files("prismqml.python.tools").joinpath(
        "templates", "windows_app.iss.tmpl"
    )
    return template.read_text(encoding="utf-8")


def _optional_template_values(
    manifest: WindowsInstallerManifest, output_path: Path
) -> Dict[str, str]:
    url_define = f'#define PrismAppURL "{manifest.homepage}"' if manifest.homepage else ""
    url_lines = (
        "AppPublisherURL={#PrismAppURL}\n"
        "AppSupportURL={#PrismAppURL}\n"
        "AppUpdatesURL={#PrismAppURL}"
        if manifest.homepage
        else ""
    )
    icon_define = (
        f'#define PrismSetupIcon "{_path_for_output(manifest, output_path, manifest.icon)}"'
        if manifest.icon
        else ""
    )
    icon_line = "SetupIconFile={#PrismSetupIcon}" if manifest.icon else ""
    extension = (
        f'#include "{_path_for_output(manifest, output_path, manifest.extension_include)}"'
        if manifest.extension_include
        else ""
    )
    return {
        "APP_URL_DEFINE": url_define,
        "APP_URL_LINES": url_lines,
        "SETUP_ICON_DEFINE": icon_define,
        "SETUP_ICON_LINE": icon_line,
        "EXTENSION_INCLUDE": extension,
    }


def render_installer(
    manifest: WindowsInstallerManifest, output_path: Path, version: str
) -> str:
    """Render one portable deterministic ISS file. 渲染可移植的确定性 ISS。"""
    if VERSION_PATTERN.fullmatch(version) is None:
        raise _manifest_error("version", "must contain three or four numeric components")
    output_path = Path(output_path).resolve()
    default_dir, privileges = INSTALL_SCOPE_VALUES[manifest.install_scope]
    values = {
        "MANIFEST_NAME": manifest.source_path.name,
        "APP_ID": manifest.app_id,
        "APP_NAME": manifest.name,
        "APP_VERSION": version,
        "APP_PUBLISHER": manifest.publisher,
        "APP_EXECUTABLE": manifest.executable,
        "APP_USER_MODEL_ID": manifest.aumid,
        "DIST_DIR": _path_for_output(manifest, output_path, manifest.dist_dir),
        "INSTALLER_OUTPUT_DIR": _path_for_output(
            manifest, output_path, manifest.installer_output_dir
        ),
        "OUTPUT_NAME": _render_output_name(manifest, version),
        "CHINESE_MESSAGES_FILE": _messages_for_output(manifest, output_path),
        "DEFAULT_DIR": default_dir,
        "PRIVILEGES": privileges,
        **_optional_template_values(manifest, output_path),
    }
    return Template(_template_text()).substitute(values).rstrip() + "\n"


def _content_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_installer(
    manifest: WindowsInstallerManifest, output_path: Path, version: str
) -> InstallerResult:
    """Atomically create or refresh one generated ISS. 原子创建或刷新 ISS。"""
    output_path = Path(output_path).resolve()
    content = render_installer(manifest, output_path, version)
    if output_path.is_file() and output_path.read_text(encoding="utf-8") == content:
        return InstallerResult(output_path, _content_sha256(content), False)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output_path.name}.", dir=output_path.parent
        )
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temporary_name, output_path)
    except OSError as exc:
        temporary = locals().get("temporary_name")
        if temporary:
            Path(temporary).unlink(missing_ok=True)
        raise ManifestError("io_error", f"cannot write generated installer: {exc}", EXIT_IO) from exc
    return InstallerResult(output_path, _content_sha256(content), True)


def check_installer(
    manifest: WindowsInstallerManifest, output_path: Path, version: str
) -> InstallerResult:
    """Verify one generated ISS without writing. 只读校验生成的 ISS。"""
    output_path = Path(output_path).resolve()
    expected = render_installer(manifest, output_path, version)
    if not output_path.is_file():
        raise ManifestError(
            "stale_output",
            f"generated installer is missing: {output_path}",
            EXIT_STALE_OUTPUT,
        )
    try:
        actual = output_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ManifestError(
            "stale_output",
            f"generated installer is unreadable: {output_path}: {exc}",
            EXIT_STALE_OUTPUT,
        ) from exc
    if actual != expected:
        raise ManifestError(
            "stale_output",
            f"generated installer is stale: {output_path}",
            EXIT_STALE_OUTPUT,
        )
    return InstallerResult(output_path, _content_sha256(expected), False)


def _path_check(path: Path, required: bool = True) -> Dict[str, Any]:
    return {
        "available": path.exists(),
        "path": str(path),
        "required": required,
    }


def _iscc_check() -> Dict[str, Any]:
    configured = os.environ.get("PRISMQML_ISCC", "").strip()
    if configured:
        path = Path(configured).resolve()
        return {"available": path.is_file(), "path": str(path), "source": "env"}
    discovered = shutil.which("ISCC.exe") or shutil.which("iscc")
    return {
        "available": discovered is not None,
        "path": str(Path(discovered).resolve()) if discovered else None,
        "source": "path" if discovered else "missing",
    }


def doctor_manifest(manifest: WindowsInstallerManifest) -> Dict[str, Any]:
    """Return non-mutating compile readiness diagnostics. 返回只读编译就绪诊断。"""
    dist_dir = _project_path(manifest, manifest.dist_dir)
    checks = {
        "dist_dir": _path_check(dist_dir),
        "executable": _path_check(dist_dir / manifest.executable),
        "iscc": _iscc_check(),
    }
    if manifest.icon:
        checks["icon"] = _path_check(_project_path(manifest, manifest.icon))
    if manifest.extension_include:
        checks["extension_include"] = _path_check(
            _project_path(manifest, manifest.extension_include)
        )
    if not manifest.chinese_messages_file.lower().startswith("compiler:"):
        checks["chinese_messages_file"] = _path_check(
            _project_path(manifest, manifest.chinese_messages_file)
        )
    return {
        "checks": checks,
        "ready_to_compile": all(check["available"] for check in checks.values()),
    }
