# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Deterministic Windows installer generation core. 确定性 Windows 安装器生成核心。"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass
from importlib import resources
from pathlib import Path, PureWindowsPath
from string import Template
from typing import Any, Dict, Optional

from ._windows_installer_manifest import (
    EXIT_IO,
    EXIT_MANIFEST,
    EXIT_STALE_OUTPUT,
    INSTALL_SCOPE_VALUES,
    VERSION_PATTERN,
    ManifestError,
    WindowsInstallerManifest,
    _manifest_error,
    _render_output_name,
    load_manifest,
)


@dataclass(frozen=True)
class InstallerResult:
    """One deterministic generation or check result. 一次确定性生成或检查结果。"""

    output: Path
    sha256: str
    changed: bool = False


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


def _template_text() -> str:
    template = resources.files("prismqml.python.tools").joinpath(
        "templates", "windows_app.iss.tmpl"
    )
    try:
        return template.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ManifestError(
            "io_error", f"cannot read installer template: {exc}", EXIT_IO
        ) from exc


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


def _generated_output_matches(output_path: Path, content: str) -> bool:
    if not output_path.is_file():
        return False
    try:
        return output_path.read_text(encoding="utf-8") == content
    except UnicodeDecodeError:
        return False
    except OSError as exc:
        raise ManifestError(
            "io_error", f"cannot read generated installer: {exc}", EXIT_IO
        ) from exc


def _cleanup_temporary_file(temporary_name: Optional[str]) -> str:
    if not temporary_name:
        return ""
    try:
        Path(temporary_name).unlink(missing_ok=True)
    except OSError as exc:
        return f"; temporary cleanup also failed: {exc}"
    return ""


def generate_installer(
    manifest: WindowsInstallerManifest, output_path: Path, version: str
) -> InstallerResult:
    """Atomically create or refresh one generated ISS. 原子创建或刷新 ISS。"""
    output_path = Path(output_path).resolve()
    content = render_installer(manifest, output_path, version)
    if _generated_output_matches(output_path, content):
        return InstallerResult(output_path, _content_sha256(content), False)
    temporary_name = None
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output_path.name}.", dir=output_path.parent
        )
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temporary_name, output_path)
    except OSError as exc:
        cleanup_detail = _cleanup_temporary_file(temporary_name)
        raise ManifestError(
            "io_error",
            f"cannot write generated installer: {exc}{cleanup_detail}",
            EXIT_IO,
        ) from exc
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


def _path_check(path: Path, expected: str) -> Dict[str, Any]:
    available = path.is_dir() if expected == "directory" else path.is_file()
    return {
        "available": available,
        "expected": expected,
        "path": str(path),
        "required": True,
    }


def _iscc_check() -> Dict[str, Any]:
    configured = os.environ.get("PRISMQML_ISCC", "").strip()
    if configured:
        path = Path(configured).resolve()
        return {
            "available": path.is_file(),
            "expected": "file",
            "path": str(path),
            "required": True,
            "source": "env",
        }
    discovered = shutil.which("ISCC.exe") or shutil.which("iscc")
    return {
        "available": discovered is not None,
        "expected": "file",
        "path": str(Path(discovered).resolve()) if discovered else None,
        "required": True,
        "source": "path" if discovered else "missing",
    }


def doctor_manifest(manifest: WindowsInstallerManifest) -> Dict[str, Any]:
    """Return non-mutating compile readiness diagnostics. 返回只读编译就绪诊断。"""
    dist_dir = _project_path(manifest, manifest.dist_dir)
    checks = {
        "dist_dir": _path_check(dist_dir, "directory"),
        "executable": _path_check(dist_dir / manifest.executable, "file"),
        "iscc": _iscc_check(),
    }
    if manifest.icon:
        checks["icon"] = _path_check(_project_path(manifest, manifest.icon), "file")
    if manifest.extension_include:
        checks["extension_include"] = _path_check(
            _project_path(manifest, manifest.extension_include), "file"
        )
    if not manifest.chinese_messages_file.lower().startswith("compiler:"):
        checks["chinese_messages_file"] = _path_check(
            _project_path(manifest, manifest.chinese_messages_file), "file"
        )
    return {
        "checks": checks,
        "ready_to_compile": all(check["available"] for check in checks.values()),
    }
