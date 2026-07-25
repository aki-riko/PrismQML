# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Explicit Inno Setup compilation workflow. 显式 Inno Setup 编译流程。"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from ._windows_installer_core import (
    ManifestError,
    WindowsInstallerManifest,
    _project_path,
    _render_output_name,
    doctor_manifest,
    generate_installer,
    render_installer,
)


EXIT_COMPILE = 6
COMPILER_DIAGNOSTIC_LIMIT = 2000


@dataclass(frozen=True)
class InstallerCompileResult:
    """One compile plan or completed compile. 一次编译计划或已完成编译。"""

    script: Path
    installer: Path
    compiler: Path
    argv: Tuple[str, ...]
    script_sha256: str
    installer_sha256: Optional[str]
    dry_run: bool
    compiled: bool


def _compile_error(code: str, message: str) -> ManifestError:
    return ManifestError(code, message, EXIT_COMPILE)


def _compile_paths(
    manifest: WindowsInstallerManifest, output_path: Path, version: str
) -> Tuple[Path, Path, Path]:
    diagnostics = doctor_manifest(manifest)
    missing = sorted(
        name
        for name, check in diagnostics["checks"].items()
        if not check["available"]
    )
    if missing:
        raise _compile_error(
            "compile_not_ready", f"missing compile prerequisites: {missing}"
        )
    compiler = Path(diagnostics["checks"]["iscc"]["path"]).resolve()
    script = Path(output_path).resolve()
    output_dir = _project_path(manifest, manifest.installer_output_dir)
    installer_name = f"{_render_output_name(manifest, version)}.exe"
    installer = (output_dir / installer_name).resolve()
    return compiler, script, installer


def _compiler_diagnostic(completed: subprocess.CompletedProcess) -> str:
    diagnostic = (completed.stderr or completed.stdout or "").strip()
    if len(diagnostic) > COMPILER_DIAGNOSTIC_LIMIT:
        return diagnostic[:COMPILER_DIAGNOSTIC_LIMIT] + "..."
    return diagnostic


def _run_compiler(compiler: Path, script: Path) -> None:
    argv = [str(compiler), str(script)]
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            check=False,
            cwd=script.parent,
            encoding="utf-8",
            errors="replace",
            text=True,
        )
    except OSError as exc:
        raise _compile_error("compile_failed", f"cannot launch ISCC: {exc}") from exc
    if completed.returncode == 0:
        return
    diagnostic = _compiler_diagnostic(completed)
    detail = f"ISCC exited with code {completed.returncode}"
    if diagnostic:
        detail = f"{detail}: {diagnostic}"
    raise _compile_error("compile_failed", detail)


def _artifact_state(path: Path) -> Optional[Tuple[int, int, int]]:
    """Return fields that prove the compiler refreshed an artifact. 返回产物刷新证据。"""
    try:
        status = path.stat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise _compile_error(
            "compile_failed", f"cannot inspect expected installer: {path}: {exc}"
        ) from exc
    if not path.is_file():
        return None
    return status.st_size, status.st_mtime_ns, status.st_ctime_ns


def _installer_sha256(path: Path) -> str:
    """Hash the compiled installer artifact. 计算已编译安装包摘要。"""
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise _compile_error(
            "compile_failed", f"cannot hash expected installer: {path}: {exc}"
        ) from exc
    return digest.hexdigest()


def _compile_result(
    script: Path,
    installer: Path,
    compiler: Path,
    argv: Tuple[str, ...],
    script_sha256: str,
    installer_sha256: Optional[str],
    compiled: bool,
) -> InstallerCompileResult:
    """Build one immutable compile result. 构建不可变编译结果。"""
    return InstallerCompileResult(
        script=script,
        installer=installer,
        compiler=compiler,
        argv=argv,
        script_sha256=script_sha256,
        installer_sha256=installer_sha256,
        dry_run=not compiled,
        compiled=compiled,
    )


def _require_refreshed_installer(
    installer: Path, artifact_before: Optional[Tuple[int, int, int]]
) -> None:
    """Require a newly created or refreshed installer. 要求安装包已创建或刷新。"""
    artifact_after = _artifact_state(installer)
    if not artifact_after:
        raise _compile_error(
            "compile_failed", f"ISCC did not create expected installer: {installer}"
        )
    if artifact_before and artifact_after == artifact_before:
        raise _compile_error(
            "compile_failed", f"ISCC did not refresh expected installer: {installer}"
        )


def compile_installer(
    manifest: WindowsInstallerManifest,
    output_path: Path,
    version: str,
    dry_run: bool = False,
) -> InstallerCompileResult:
    """Plan or explicitly compile one generated ISS. 规划或显式编译 ISS。"""
    content = render_installer(manifest, output_path, version)
    compiler, script, installer = _compile_paths(manifest, output_path, version)
    argv = (str(compiler), str(script))
    script_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if dry_run:
        return _compile_result(
            script, installer, compiler, argv, script_sha256, None, False
        )
    generate_installer(manifest, script, version)
    artifact_before = _artifact_state(installer)
    _run_compiler(compiler, script)
    _require_refreshed_installer(installer, artifact_before)
    installer_sha256 = _installer_sha256(installer)
    return _compile_result(
        script, installer, compiler, argv, script_sha256, installer_sha256, True
    )
