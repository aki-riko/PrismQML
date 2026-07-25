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
from typing import Tuple

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
    sha256: str
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
    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if dry_run:
        return InstallerCompileResult(
            script, installer, compiler, argv, sha256, True, False
        )
    generate_installer(manifest, script, version)
    _run_compiler(compiler, script)
    if not installer.is_file():
        raise _compile_error(
            "compile_failed", f"ISCC did not create expected installer: {installer}"
        )
    return InstallerCompileResult(
        script, installer, compiler, argv, sha256, False, True
    )
