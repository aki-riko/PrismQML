# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Image provider lifecycle regression tests. 图片提供器生命周期回归测试。"""

import logging
import runpy
import tempfile
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_PROCESS = runpy.run_path(str(REPO_ROOT / "scripts" / "test_process.py"))
prepare_automated_test_process = TEST_PROCESS["prepare_automated_test_process"]

prepare_automated_test_process()

import shiboken6
from PySide6.QtCore import QSize, qInstallMessageHandler
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlEngine
from PySide6.QtWidgets import QApplication

import prismqml.python.providers.qrcode_generator as qrcode_generator
from prismqml.python.providers.qrcode_generator import get_qrcode_provider
from prismqml.python.providers._qrcode_protocol import create_request, encode_provider_id
from prismqml.python.runtime.lazy_context import LazyQRCodeGenerator
from prismqml.python.providers.svg_provider import get_svg_provider
from prismqml.python.core.engine import EngineManager
from prismqml import register_types
from prismqml.python.window.mica_window import get_acrylic_helper


LIFECYCLE_CYCLES = 10
SVG_CONTENT = '<svg viewBox="0 0 8 8"><rect width="8" height="8"/></svg>'
DUPLICATE_WARNING_MARKERS = (
    "already has an image provider",
    "already registered",
    "duplicate",
)
LOGGER = logging.getLogger("prismqml.provider_lifecycle")


def _ensure_application() -> QApplication:
    """Return the process-wide GUI application. 返回进程级 GUI 应用。"""
    return QApplication.instance() or QApplication([])


def _create_providers():
    """Create one engine-owned provider set. 创建一组引擎持有的 provider。"""
    return {
        "acrylic": get_acrylic_helper().imageProvider,
        "svg": get_svg_provider(),
        "qrcode": get_qrcode_provider(),
    }


def _exercise_acrylic(provider, iteration: int, previous_id: int) -> int:
    """Write and read shared acrylic state. 写入并读取共享亚克力状态。"""
    image = QImage(8, 8, QImage.Format.Format_ARGB32)
    image.fill(QColor(iteration % 255, 32, 64, 255))
    provider.setImage(image)
    result = provider.requestImage(str(iteration), QSize(), QSize(8, 8))
    assert not result.isNull()
    assert result.size() == QSize(8, 8)
    assert provider.currentImageId > previous_id
    return provider.currentImageId


def _exercise_svg(provider, svg_path: Path) -> None:
    """Render a real SVG through the provider. 通过 provider 渲染真实 SVG。"""
    result = provider.requestImage(str(svg_path), QSize(), QSize(16, 16))
    assert not result.isNull()
    assert result.size() == QSize(16, 16)


def _exercise_qrcode(provider, iteration: int) -> None:
    """Render a real QR code through the provider. 通过 provider 渲染真实二维码。"""
    request_id = encode_provider_id(
        create_request(
            f"PrismQML lifecycle {iteration}",
            96,
            "#000000",
            "#ffffff",
            "M",
        )
    )
    result = provider.requestImage(request_id, QSize(), QSize(96, 96))
    assert not result.isNull()
    assert result.size() == QSize(96, 96)


def _exercise_cycle(svg_path: Path, iteration: int, previous_id: int) -> int:
    """Register, use, and destroy one real QML engine. 注册、使用并销毁引擎。"""
    engine = QQmlEngine()
    providers = _create_providers()
    try:
        for name, provider in providers.items():
            engine.addImageProvider(name, provider)
        current_id = _exercise_acrylic(providers["acrylic"], iteration, previous_id)
        _exercise_svg(providers["svg"], svg_path)
        _exercise_qrcode(providers["qrcode"], iteration)
    finally:
        shiboken6.delete(engine)
    assert all(not shiboken6.isValid(provider) for provider in providers.values())
    return current_id


def run_provider_lifecycle() -> int:
    """Run ten engine lifecycles and reject duplicate warnings. 执行十轮生命周期。"""
    _ensure_application()
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda _mode, _context, message: messages.append(str(message))
    )
    try:
        with tempfile.TemporaryDirectory(prefix="prism-provider-") as temp_dir:
            svg_path = Path(temp_dir) / "lifecycle.svg"
            svg_path.write_text(SVG_CONTENT, encoding="utf-8")
            acrylic_id = 0
            for iteration in range(LIFECYCLE_CYCLES):
                acrylic_id = _exercise_cycle(svg_path, iteration, acrylic_id)
    finally:
        qInstallMessageHandler(previous_handler)
    duplicate_messages = [
        message
        for message in messages
        if any(marker in message.lower() for marker in DUPLICATE_WARNING_MARKERS)
    ]
    assert not duplicate_messages
    return LIFECYCLE_CYCLES * 3


def _qrcode_binding(engine: QQmlEngine) -> LazyQRCodeGenerator:
    """Return the engine-bound lazy QR proxy. 返回引擎绑定的 QR 延迟代理。"""
    bindings = getattr(engine, "_prismqml_lazy_context_objects")
    return next(binding for binding in bindings if isinstance(binding, LazyQRCodeGenerator))


def run_engine_manager_reset() -> None:
    """Reset only the current engine binding. 只重置当前引擎绑定。"""
    _ensure_application()
    engine_a = QQmlEngine()
    engine_b = QQmlEngine()
    try:
        register_types(engine_a)
        register_types(engine_b)
        binding_a = _qrcode_binding(engine_a)
        binding_b = _qrcode_binding(engine_b)
        EngineManager.set_engine(engine_a)
        EngineManager.set_engine(engine_b)
        EngineManager.reset()
        assert binding_b._engine is None
        assert binding_a._engine is engine_a
        try:
            EngineManager.get_engine()
        except RuntimeError:
            pass
        else:
            raise AssertionError("EngineManager.reset() kept the current engine")
        EngineManager.set_engine(engine_a)
        EngineManager.reset()
        assert binding_a._engine is None
    finally:
        EngineManager.reset()
        shiboken6.delete(engine_b)
        shiboken6.delete(engine_a)


def run_reset_after_engine_delete() -> None:
    """Release bindings after explicit engine deletion. 显式销毁后释放绑定。"""
    engine = QQmlEngine()
    register_types(engine)
    binding = _qrcode_binding(engine)
    EngineManager.set_engine(engine)
    shiboken6.delete(engine)
    EngineManager.reset()
    assert binding._engine is None


def test_provider_lifecycle() -> None:
    """Verify all three providers across ten engines. 验证三类 provider 十轮切换。"""
    assert run_provider_lifecycle() == LIFECYCLE_CYCLES * 3


def test_engine_manager_reset() -> None:
    """Verify reset does not touch another engine. 验证 reset 不影响其他引擎。"""
    run_engine_manager_reset()


def test_reset_after_engine_delete() -> None:
    """Verify reset after explicit deletion. 验证显式销毁后的 reset。"""
    run_reset_after_engine_delete()


def test_lazy_qrcode_provider_registration_is_deferred_and_idempotent(
    qapp, monkeypatch
) -> None:
    """Keep QR provider registration lazy and one-shot. 保持二维码 provider 延迟且只注册一次。"""
    calls = []
    provider = object()

    class _Engine:
        def addImageProvider(self, name, value):
            calls.append((name, value))

    monkeypatch.setattr(
        qrcode_generator,
        "get_qrcode_provider",
        lambda: provider,
    )
    engine = _Engine()
    binding = LazyQRCodeGenerator(SimpleNamespace())
    binding._engine = engine
    second_binding = LazyQRCodeGenerator(SimpleNamespace())
    second_binding._engine = engine

    assert calls == []
    binding._ensure_provider()
    binding._ensure_provider()
    second_binding._ensure_provider()
    assert calls == [("qrcode", provider)]


def main() -> int:
    """Run the regression against an installed wheel/sdist. 验证安装态制品。"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    operations = run_provider_lifecycle()
    run_engine_manager_reset()
    run_reset_after_engine_delete()
    LOGGER.info("provider lifecycle operations passed: %s", operations)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
