# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Validate PrismQML wheel and sdist release artifacts. 验证发布制品。"""

import argparse
import glob
import logging
import re
import tarfile
import zipfile
from pathlib import Path
from typing import Optional


logger = logging.getLogger("prismqml.dist")
REQUIRED_SDIST_FILES = {
    "pyproject.toml",
    "rust/Cargo.toml",
    "rust/Cargo.lock",
    "rust/src/lib.rs",
    "rust/src/shard.rs",
}
CRASH_RUNTIME_DIR = "prismqml/_native/crash/"
# Wheel platform tag prefix -> bundled crash runtime files; mirrors
# build_crash_runtime.RUNTIME_FILES (kept in sync by a tooling test)
# wheel 平台标签前缀 -> 内置崩溃运行时文件；与 build_crash_runtime.RUNTIME_FILES 一致
CRASH_RUNTIME_FILES = {
    "win_": ("sentry.dll", "crashpad_handler.exe", "crashpad_wer.dll"),
    "manylinux": ("libsentry.so", "crashpad_handler"),
    "macosx_": ("libsentry.dylib", "crashpad_handler"),
}
POSIX_HANDLER = "crashpad_handler"
FORBIDDEN_SDIST_PREFIXES = (".artifacts/", "build/", "dist/", CRASH_RUNTIME_DIR)


def parse_args():
    """Parse artifact expectations. 解析制品预期。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("patterns", nargs="+", help="Artifact paths or glob patterns")
    parser.add_argument("--expect-sdist", action="store_true")
    parser.add_argument("--expect-wheels", type=int)
    parser.add_argument(
        "--expect-crash-runtime",
        action="store_true",
        help="Require every wheel to bundle the crash runtime 要求 wheel 内置崩溃运行时",
    )
    return parser.parse_args()


def expand_paths(patterns: list[str]) -> list[Path]:
    """Expand shell-independent glob patterns. 展开跨 shell 通配符。"""
    paths = []
    for pattern in patterns:
        matches = [Path(match) for match in glob.glob(pattern)]
        if not matches and Path(pattern).is_file():
            matches = [Path(pattern)]
        paths.extend(matches)
    return sorted(set(path.resolve() for path in paths))


def validate_counts(paths: list[Path], expect_sdist: bool, expect_wheels: Optional[int]):
    """Validate artifact counts. 验证制品数量。"""
    sdist_count = sum(path.name.endswith(".tar.gz") for path in paths)
    wheel_count = sum(path.suffix == ".whl" for path in paths)
    if expect_sdist and sdist_count != 1:
        raise ValueError(f"expected exactly 1 sdist, found {sdist_count}")
    if expect_wheels is not None and wheel_count != expect_wheels:
        raise ValueError(f"expected {expect_wheels} wheels, found {wheel_count}")


def validate_sdist(path: Path):
    """Validate source distribution contents. 验证源码包内容。"""
    with tarfile.open(path, "r:gz") as archive:
        names = set(archive.getnames())
    roots = {name.split("/", 1)[0] for name in names if name}
    if len(roots) != 1:
        raise ValueError(f"sdist must have one root directory, found {sorted(roots)}")
    root = next(iter(roots))
    missing = sorted(item for item in REQUIRED_SDIST_FILES if f"{root}/{item}" not in names)
    if missing:
        raise ValueError(f"sdist missing required files: {missing}")
    forbidden = sorted(
        name for name in names
        if any(f"{name}/".startswith(f"{root}/{prefix}") for prefix in FORBIDDEN_SDIST_PREFIXES)
    )
    if forbidden:
        raise ValueError(f"sdist contains build artifacts: {forbidden}")


def _crash_runtime_files(wheel_name: str) -> tuple:
    platform_tag = wheel_name[: -len(".whl")].rsplit("-", 1)[-1]
    for prefix, files in CRASH_RUNTIME_FILES.items():
        if platform_tag.startswith(prefix):
            return files
    raise ValueError(f"no crash runtime defined for platform tag {platform_tag}")


def validate_crash_runtime(path: Path, archive: zipfile.ZipFile):
    """Validate the bundled crash runtime. 验证内置崩溃运行时。"""
    expected = _crash_runtime_files(path.name)
    entries = {
        info.filename[len(CRASH_RUNTIME_DIR):]: info
        for info in archive.infolist()
        if info.filename.startswith(CRASH_RUNTIME_DIR) and not info.is_dir()
    }
    if sorted(entries) != sorted(expected):
        raise ValueError(f"expected crash runtime {sorted(expected)}, found {sorted(entries)}")
    if "-win_" not in path.name:
        mode = entries[POSIX_HANDLER].external_attr >> 16
        if not mode & 0o100:
            raise ValueError(f"{POSIX_HANDLER} is not executable in {path.name}")


def validate_wheel(path: Path, expect_crash_runtime: bool = False):
    """Validate abi3 wheel tag, extension name and crash runtime. 验证 abi3 wheel。"""
    if "-cp39-abi3-" not in path.name:
        raise ValueError("wheel filename is not tagged cp39-abi3")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        basenames = [Path(name).name for name in names]
        # A partial runtime is always an error; a missing one only when required
        # 运行时不完整一律报错；缺失只在要求时报错
        if expect_crash_runtime or any(name.startswith(CRASH_RUNTIME_DIR) for name in names):
            validate_crash_runtime(path, archive)
    extensions = [name for name in basenames if re.match(r"^prismqml_rs.*\.(?:pyd|so)$", name)]
    expected = "prismqml_rs.pyd" if "-win_" in path.name else "prismqml_rs.abi3.so"
    if extensions != [expected]:
        raise ValueError(f"expected extension {expected}, found {extensions}")
    if any(re.search(r"\.cp\d+", name) for name in extensions):
        raise ValueError(f"version-specific extension found: {extensions}")


def validate_path(path: Path, expect_crash_runtime: bool = False):
    """Dispatch validation by artifact type. 按制品类型验证。"""
    if path.name.endswith(".tar.gz"):
        validate_sdist(path)
    elif path.suffix == ".whl":
        validate_wheel(path, expect_crash_runtime)
    else:
        raise ValueError(f"unsupported artifact type: {path.name}")
    logger.info("validated %s", path.name)


def main() -> int:
    """Run artifact validation. 执行制品验证。"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    paths = expand_paths(args.patterns)
    if not paths:
        logger.error("no artifacts matched: %s", args.patterns)
        return 1
    try:
        validate_counts(paths, args.expect_sdist, args.expect_wheels)
        for path in paths:
            validate_path(path, args.expect_crash_runtime)
    except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile) as error:
        logger.error("artifact validation failed: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
