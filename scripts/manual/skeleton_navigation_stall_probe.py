# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Real-window skeleton lazy-loading stall probe. 真实窗口骨架懒加载停留探针。

Launches the real Gallery on a visible Direct3D11 window, switches the page stack
from index 0 to the NavigationPage (index 6) once per configured lazy-loading
style, and records the full stage timeline of the wait overlay: overlay visible
interval, ``_displayIndex`` convergence, helper pending/switching state, target
Loader status sequence, and main-thread timer jitter.

在真实可见 Direct3D11 窗口上启动真实 Gallery, 按配置的懒加载样式把页面栈从下标 0
切到 NavigationPage(下标 6), 并记录等待遮罩的完整阶段时间线: 遮罩 visible 区间、
``_displayIndex`` 收敛、helper 待处理/切换状态、目标 Loader 状态序列, 以及主线程
定时器节拍抖动。

The three candidate stall mechanisms are separated by what is recorded while the
overlay is still on screen:
  (a) exit condition never satisfied -> the overlay stays visible with a live
      pending target, ``stageTimer`` parked, and normal timer jitter;
  (b) main thread blocked -> one tick gap of the same order as the stall, and the
      overlay flips visible=false immediately after that gap;
  (c) target Loader never ready -> Loader status parked in Loading while the 1ms
      poll keeps ticking normally.
覆盖层仍在屏上时所记录的数据可区分三种候选卡死机制: (a) 退场条件永不满足 ->
遮罩持续可见且待处理目标仍存活、阶段计时器停摆、节拍正常; (b) 主线程阻塞 ->
出现与停留同量级的单次节拍间隔, 遮罩在该间隔后立刻转为不可见; (c) 目标 Loader
未就绪 -> Loader 状态停在 Loading 而 1ms 轮询节拍正常。

Run one style per process; only one visible probe window may exist at a time.
每个进程只跑一种样式; 同一时刻只允许一个真实可见窗口探针在跑。
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path

# QUrl is used by the runtime page-source override helper, so it must be importable
# at module scope rather than only inside main().
# 运行时页面源替换助手需要 QUrl, 因此必须在模块级可导入, 而非只在 main() 内。
from PySide6.QtCore import QUrl


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Keep bytecode under the shared artifact root before importing the package.
# 导入项目包前把字节码缓存集中到统一产物根目录。
_ARTIFACT_ROOT = Path(os.environ.get("PRISM_ARTIFACT_ROOT", str(ROOT / ".artifacts")))
_CACHE_PATH = _ARTIFACT_ROOT / "python" / "pycache"
os.environ["PYTHONPYCACHEPREFIX"] = str(_CACHE_PATH)
sys.pycache_prefix = str(_CACHE_PATH)

ARTIFACT_DIR = _ARTIFACT_ROOT / "python" / "skeleton-stall"
CONFIG_DIR = ARTIFACT_DIR / "configs"
RESULT_PREFIX = "PRISMQML_SKELETON_STALL_PROBE="
DIAGNOSTIC_MARKERS = ("[懒加载诊断]", "[启动剖析]", "[Incubation]")
LOADER_STATUS_NAMES = {0: "Null", 1: "Ready", 2: "Loading", 3: "Error"}
TARGET_INDEX = 6
SAMPLE_INTERVAL_MS = 2
TICK_INTERVALS_MS = {"1ms": 1, "16ms": 16}
STALL_THRESHOLD_FACTOR = 5
DIAGNOSTIC_CAP = 3000
TIMELINE_CAP = 6000
TICK_EVENT_CAP = 200
COMPLETION_GRACE_MS = 600
OVERLAY_ABSENT_GRACE_MS = 2500
STATUS_INDEX = 22  # targetLoaderReady position in the state snapshot 状态快照中的位置
SKELETON_ROWS_INDEX = 24  # skeletonRowsVisible position 可见骨架块数在状态快照中的位置

_T0_NS = time.perf_counter_ns()
_HARD_TIMEOUT_MS = 240_000
_PROGRESS_PATH: Path | None = None


def _now_ms() -> float:
    """Return process-relative milliseconds. 返回相对探针启动的毫秒数。"""
    return (time.perf_counter_ns() - _T0_NS) / 1_000_000


def _progress(message: str) -> None:
    """Append one phase marker so a hang is diagnosable. 追加阶段标记以便诊断挂死。"""
    line = f"[{_now_ms():10.2f}ms] {message}"
    print("PROGRESS " + line, file=sys.stderr, flush=True)
    if _PROGRESS_PATH is None:
        return
    try:
        with _PROGRESS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        pass


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--style", type=int, choices=(0, 1), required=True)
    parser.add_argument("--run", type=int, default=1)
    # Target page index. Defaults to the NavigationPage (6) reported by the user;
    # other indexes discriminate "the skeleton overlay stalls every page" from
    # "this particular page stalls".
    # 目标页下标。默认是用户反馈的 NavigationPage(6); 换别的下标可以区分
    # "骨架覆盖层拖慢所有页面" 与 "只有这个页面卡"。
    parser.add_argument("--target-index", type=int, default=TARGET_INDEX)
    parser.add_argument("--timeout-ms", type=int, default=90_000)
    parser.add_argument("--ready-timeout-ms", type=int, default=60_000)
    parser.add_argument("--settle-ms", type=int, default=1_000)
    # Window height override. The skeleton row count is derived from the available
    # height (QMLPageSkeleton._rowCount), so shrinking the window is the dose knob
    # for "does the stall scale with the number of skeleton blocks".
    # 窗口高度覆盖。骨架行数由可用高度推导(QMLPageSkeleton._rowCount), 因此缩小窗口
    # 就是"卡顿是否随骨架块数缩放"的剂量旋钮。
    parser.add_argument("--window-height", type=int, default=0)
    # Decisive experiment switch: force the framework page Loaders to load
    # synchronously by publishing PrismQmlAsynchronousPageLoaderEnabled=false.
    # The skeleton style is the only consumer that keeps a 1ms repeat timer alive
    # while the target page incubates, so comparing async on/off isolates
    # "incubation starved by the poll" from "the page itself is slow".
    # 决定性实验开关: 通过发布 PrismQmlAsynchronousPageLoaderEnabled=false 强制框架
    # 页面 Loader 同步加载。骨架样式是唯一在目标页孵化期间仍保持 1ms 重复定时器的消费方,
    # 因此对比异步开/关可把"轮询饿死孵化"与"页面本身慢"分开。
    parser.add_argument("--sync-pages", action="store_true")
    # Split the two effects that --sync-pages conflates (see the patch below).
    # 拆开 --sync-pages 混淆的两个效果(见下方补丁)。
    parser.add_argument("--no-incubation-controller", action="store_true")
    # Acrylic hypothesis switch. NavigationPage is the only measured target that
    # stalls, and it is also the only page that calls AcrylicHelper (a synchronous
    # screen grab + blur) from NavigationPanelShowcase. Returning "" from the grab
    # makes that call a no-op, which isolates "the capture is the stall" from
    # "NavigationPage is simply heavy". Calls are counted so a retry loop shows up.
    # 亚克力假设开关。NavigationPage 是唯一被测出卡死的目标, 也是唯一从
    # NavigationPanelShowcase 调用 AcrylicHelper(同步截屏+模糊)的页面。让抓图返回 ""
    # 即可把"截图导致卡死"与"NavigationPage 本身就重"分开。同时计数调用次数,
    # 若存在重试循环会直接暴露。
    parser.add_argument("--no-acrylic", action="store_true")
    # The user runs with default INFO logging (no verbose diagnostics). The probe
    # turns verbose on to capture stage traces, and verbose logging happens inside
    # the 1ms poll path, so this arm proves the stall is not a probe artifact.
    # 用户以默认 INFO 级别运行(无详细诊断)。探针为抓阶段轨迹会打开 verbose, 而 verbose
    # 日志正落在 1ms 轮询路径上, 因此本开关用于证明卡死不是探针自身造成的假象。
    parser.add_argument("--no-verbose", action="store_true")
    # Non-invasive bisection: replace the target page's source at runtime, leaving
    # every product file untouched. This is how the stall gets narrowed to a
    # specific part of NavigationPage without editing examples/.
    # 非侵入式二分: 运行时替换目标页源码, 完全不碰产品文件。这样就能在不编辑
    # examples/ 的前提下把卡死收敛到 NavigationPage 的某个具体部分。
    parser.add_argument("--override-target-source", type=Path, default=None)
    # Decisive isolation: keep the skeleton overlay but force the page transition
    # back to lazy_circle, so `animationType` is no longer `none`. If the stall
    # disappears, the `none` path is the cause; if it persists, the skeleton
    # overlay is. The Binding that sets `none` only re-asserts when
    # `_lazySkeletonStyle` changes, which this arm never touches.
    # 决定性隔离: 保留骨架覆盖层, 但把页面过渡强制改回 lazy_circle, 使 animationType
    # 不再是 none。若卡死消失, 则原因是 none 路径; 若仍卡, 则原因是骨架覆盖层本身。
    # 把 animationType 设为 none 的 Binding 只在 _lazySkeletonStyle 变化时重申,
    # 而本开关不会触碰它。
    parser.add_argument("--force-circle", action="store_true")
    # Reverse arm of the same isolation: keep the RING style but force the
    # transition to `none`. If ring + none also stalls, the `none` path is the
    # cause regardless of which overlay style is configured.
    # 同一隔离的反向臂: 保留环形样式, 但把过渡强制为 none。若"环形 + none"同样卡死,
    # 则无论配置哪种覆盖层样式, 原因都在 none 路径。
    parser.add_argument("--force-none", action="store_true")
    # Interaction hypothesis: with `animationType = none` the collapse completes
    # synchronously, so the target Loader is activated ~420ms earlier than with the
    # circle transition. That early activation races the skeleton overlay's own
    # instantiation during startup. Delaying activation tests exactly that.
    # 交互假设: animationType=none 时收紧同步完成, 目标 Loader 比圆圈过渡提前约 420ms
    # 被激活; 这次提前激活与骨架覆盖层自身的实例化在启动期相撞。推迟激活即可验证。
    parser.add_argument("--activation-delay-ms", type=int, default=-1)
    # Decisive competitor test: keep skeleton style and everything else, but force
    # the wait overlay off screen on every sample. If the target page then loads,
    # the overlay's presence/rendering is what starves incubation; if it still
    # never loads, the overlay is not the competitor.
    # 决定性竞争测试: 保留骨架样式与其它一切, 但每个采样都把等待覆盖层强制移出画面。
    # 若目标页随后能加载, 则覆盖层的存在/渲染就是饿死孵化的原因; 若仍不加载,
    # 则覆盖层不是竞争者。
    parser.add_argument("--hide-overlay", action="store_true")
    # Decisive P1 split: keep `lazyLoadingStyle = skeleton` (so the StackedWidget
    # still takes the `none` transition path and all skeleton branching), but make
    # the wait overlay itself render the cheap ring. If the stall clears, the
    # skeleton's own rendering is the competitor; if it persists, the `none` path
    # is. Breaks the overlay's style binding on purpose, for diagnosis only.
    # 决定性 P1 拆分: 保持 lazyLoadingStyle=skeleton(因此 StackedWidget 仍走 none 过渡
    # 与全部骨架分支), 但让等待覆盖层本身渲染廉价的环形。若卡死消失, 则骨架自身的渲染
    # 就是竞争者; 若仍卡, 则是 none 路径。故意打断覆盖层的样式绑定, 仅用于诊断。
    parser.add_argument("--overlay-ring", action="store_true")
    # Confound test for --overlay-ring: write the overlay's CURRENT style value
    # back at the same moment. If this no-op write also clears the stall, then the
    # trigger is the runtime property write (and its effect on binding/polish
    # order), not the ring content itself.
    # --overlay-ring 的混淆测试: 在同一时刻把覆盖层当前的 style 值原样写回。若这个
    # 空操作写入也能消除卡死, 则触发条件是"运行期属性写入"(及其对绑定/打磨顺序的
    # 影响), 而不是环形内容本身。
    parser.add_argument("--overlay-touch-style", action="store_true")
    # Bisect the skeleton overlay's own cost. `--skeleton-loading-off` stops the
    # infinite shimmer and hides the blocks; `--skeleton-layers-off` keeps them
    # visible but disables the per-block layer + MultiEffect mask. Diagnosis only.
    # 二分骨架覆盖层自身的开销。--skeleton-loading-off 停掉无限闪光并隐藏块;
    # --skeleton-layers-off 保持可见但关掉每块的 layer + MultiEffect 遮罩。仅诊断用。
    parser.add_argument("--skeleton-loading-off", action="store_true")
    parser.add_argument("--skeleton-layers-off", action="store_true")
    # Targeted P1 candidate: the lazy helper subtree (which carries the whole
    # skeleton overlay) is itself created through an asynchronous Loader
    # (`StackedLazyHelperLoader.asynchronous: host._asynchronousPageLoaderEnabled`),
    # so it shares the page incubation queue. Reloading that helper synchronously
    # reserves the queue for the page Loaders without making page creation
    # synchronous. Product files are untouched.
    # P1 定向候选: 懒加载辅助器子树(承载整个骨架覆盖层)本身也是经异步 Loader 创建的
    # (`StackedLazyHelperLoader.asynchronous: host._asynchronousPageLoaderEnabled`),
    # 因此与页面共用孵化队列。把该辅助器改为同步重载, 即可把队列留给页面 Loader,
    # 而不必把页面创建也变成同步。不修改产品文件。
    parser.add_argument("--helper-sync", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=ARTIFACT_DIR)
    parser.add_argument("--result-file", type=Path, default=None)
    return parser.parse_args(argv)


def _write_config(style: int) -> Path:
    """Write the temporary app config selecting the lazy-loading style."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = CONFIG_DIR / f"app-style{style}.json"
    path.write_text(
        json.dumps(
            {"Window": {"LazyLoading": True, "LazyLoadingStyle": style}},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _as_list(value) -> list:
    """Convert a QJSValue array or Python sequence into a list. 把 QJSValue/序列转为列表。"""
    if value is None:
        return []
    to_variant = getattr(value, "toVariant", None)
    if callable(to_variant):
        try:
            value = to_variant()
        except (TypeError, RuntimeError):
            return []
    try:
        return list(value)
    except TypeError:
        return []


def _enum_name(value) -> str:
    name = getattr(value, "name", None)
    return str(name if name is not None else value)


def _loader_status(loader) -> int | None:
    """Read a Loader status as an int, or None when PySide cannot marshal it.

    以 int 读取 Loader 状态; PySide 无法编排该枚举时返回 None。

    PySide6 6.11 registers ``QQuickLoader::Status`` without a converter, so
    ``loader.property("status")``, ``QMetaProperty.read`` and ``loader.status``
    all raise ``RuntimeError: Can't find converter`` (verified on this machine).
    ``None`` therefore means "unreadable here", NOT "Null". Callers that must
    gate on readiness use :func:`_loader_ready` instead, which asks QML.
    / PySide6 6.11 未给 ``QQuickLoader::Status`` 注册转换器, 因此
    ``loader.property("status")``、``QMetaProperty.read`` 与 ``loader.status``
    在本机均抛 ``RuntimeError: Can't find converter``。故 ``None`` 表示"此处读不到",
    而不是 "Null"。需要就绪门禁的调用方请改用 :func:`_loader_ready`(由 QML 求值)。
    """
    if loader is None:
        return None
    try:
        raw = loader.property("status")
    except (RuntimeError, AttributeError):
        return None
    if raw is None:
        return None
    if isinstance(raw, int):
        return raw
    value = getattr(raw, "value", None)
    if isinstance(value, int):
        return value
    try:
        return int(raw)
    except (TypeError, ValueError, RuntimeError):
        return None


def _qt_version() -> str:
    try:
        from PySide6.QtCore import qVersion

        return qVersion()
    except Exception:  # noqa: BLE001
        return "unknown"


class _DiagnosticCapture(logging.Handler):
    """Capture Qt-forwarded diagnostics with probe timestamps. 带探针时间戳捕获诊断。"""

    def __init__(self, sink) -> None:
        super().__init__(level=logging.DEBUG)
        self._sink = sink

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._sink(record.getMessage())
        except Exception:  # noqa: BLE001 - diagnostics must never break the probe
            pass


def _loader_ready(loader) -> bool | None:
    """Ask QML whether a Loader is Ready, bypassing the enum converter.

    由 QML 判断 Loader 是否就绪, 绕开枚举转换器。

    ``Loader.status`` cannot be marshalled into Python on this Qt build, so the
    comparison is evaluated inside the QML engine and only the boolean crosses
    the boundary. ``None`` means "not evaluable yet".
    / 本 Qt 构建下 ``Loader.status`` 无法编排进 Python, 因此比较在 QML 引擎内完成,
    只把布尔值带过边界。``None`` 表示"暂时无法求值"。
    """
    if loader is None:
        return None
    try:
        from PySide6.QtQml import QQmlExpression, QQmlEngine
    except ImportError:
        return None
    context = QQmlEngine.contextForObject(loader)
    if context is None:
        return None
    expression = QQmlExpression(context, loader, "status === Loader.Ready")
    try:
        value = expression.evaluate()
        if expression.hasError():
            return None
    except (RuntimeError, TypeError):
        return None
    if isinstance(value, tuple):
        value = value[0]
    return bool(value)


def _is_alive(obj) -> bool:
    """Return whether a wrapped C++ object is still valid. 判断包装的 C++ 对象是否仍有效。"""
    if obj is None:
        return False
    try:
        import shiboken6
    except ImportError:
        return True
    try:
        return bool(shiboken6.isValid(obj))
    except (RuntimeError, TypeError):
        return False


def _qml_int(scope, expression_text: str) -> int | None:
    """Evaluate a QML expression to an int, or None. 将 QML 表达式求值为 int 或 None。"""
    try:
        from PySide6.QtQml import QQmlEngine, QQmlExpression
    except ImportError:
        return None
    context = QQmlEngine.contextForObject(scope)
    if context is None:
        return None
    try:
        expression = QQmlExpression(context, scope, expression_text)
        value = expression.evaluate()
        if expression.hasError():
            return None
    except (RuntimeError, TypeError):
        return None
    if isinstance(value, tuple):
        value = value[0]
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _emit(report: dict, args: argparse.Namespace, state: dict) -> None:
    """Print and persist the single-line JSON measurement. 打印并落盘单行 JSON 测量。"""
    if state.get("printed"):
        return
    state["printed"] = True
    report.setdefault("timed_out", False)
    line = json.dumps(report, ensure_ascii=False, sort_keys=True, default=str)
    print(RESULT_PREFIX + line, flush=True)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = args.result_file or (out_dir / f"probe-style{args.style}-run{args.run}.json")
    try:
        Path(target).write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        print(f"RESULT_FILE={Path(target).resolve()}", flush=True)
    except OSError as error:
        print(f"RESULT_FILE_WRITE_FAILED={error}", flush=True)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(list(sys.argv[1:] if argv is None else argv))
    config_path = _write_config(args.style)
    os.environ["PRISMQML_CONFIG_FILE"] = str(config_path)
    if args.no_verbose:
        # Match the user's default logging level exactly.
        # 精确匹配用户的默认日志级别。
        os.environ.pop("PRISMQML_STARTUP_PROFILE_VERBOSE", None)
        os.environ["PRISM_LOG_LEVEL"] = "INFO"
    else:
        os.environ["PRISMQML_STARTUP_PROFILE_VERBOSE"] = "1"
        os.environ["PRISM_LOG_LEVEL"] = "DEBUG"

    import examples.main as gallery
    from PySide6.QtCore import QObject, Qt, QTimer
    from PySide6.QtQuick import QQuickWindow

    from prismqml.python.core import Logger, getLogger

    if args.sync_pages:
        # examples/main.py publishes this switch from the incubation policy, so
        # patching the policy function is what actually reaches the QML context.
        # examples/main.py 从孵化策略发布该开关, 因此补丁打在策略函数上才真正生效。
        from prismqml.python.core import incubation as _incubation

        _incubation.asynchronous_page_loader_enabled = (
            lambda *positional, **keyword: False
        )

    if args.no_incubation_controller:
        # Keep Loaders asynchronous but install no incubation controller. This
        # splits the two effects that --sync-pages conflates: patching
        # `asynchronous_page_loader_enabled` also makes
        # `install_default_incubation_controller` return early, so `--sync-pages`
        # alone cannot tell "synchronous creation" from "no controller".
        # The patch must land on the DEFINING module: engine.py does
        # `from ..core.incubation import install_default_incubation_controller`
        # inside the function body, so patching the engine module attribute would
        # be a no-op and silently keep the controller installed.
        # 保持 Loader 异步但不装孵化控制器。这拆开了 --sync-pages 混淆的两个效果:
        # 补丁同时让 install_default_incubation_controller 提前返回, 因此单靠
        # --sync-pages 无法区分"同步创建"与"没有控制器"。
        # 补丁必须打在定义模块上: engine.py 在函数体内做 from ... import, 因此
        # 打在 engine 模块属性上是空操作, 会静默地继续安装控制器。
        from prismqml.python.core import incubation as _incubation_module

        _incubation_module.install_default_incubation_controller = (
            lambda *positional, **keyword: None
        )
        _incubation_module.install_incubation_controller = (
            lambda *positional, **keyword: None
        )

    acrylic_calls: dict = {"count": 0, "total_ms": 0.0, "max_ms": 0.0}
    if args.no_acrylic:
        from prismqml.python.window import mica_window as _mica

        _original_grab = _mica.AcrylicHelper.grabAndBlur

        def _timed_grab(self, *positional, **keyword):
            import time as _time

            acrylic_calls["count"] += 1
            started = _time.perf_counter()
            try:
                # A blank result is the documented "nothing to publish" outcome, so
                # callers take their normal no-op path.
                # 返回空串是既有的"无可发布"结果, 调用方走正常空操作路径。
                return ""
            finally:
                elapsed = (_time.perf_counter() - started) * 1000
                acrylic_calls["total_ms"] += elapsed
                acrylic_calls["max_ms"] = max(acrylic_calls["max_ms"], elapsed)

        _mica.AcrylicHelper.grabAndBlur = _timed_grab

    diagnostics: list[list] = []

    def _capture(message: str) -> None:
        if len(diagnostics) >= DIAGNOSTIC_CAP:
            return
        if not any(marker in message for marker in DIAGNOSTIC_MARKERS):
            return
        diagnostics.append([round(_now_ms(), 2), message])

    getLogger().logger.addHandler(_DiagnosticCapture(_capture))

    state: dict = {"printed": False}
    report: dict = {
        "probe": "skeleton_navigation_stall",
        # Which controller the engine actually holds, so an isolation arm can prove
        # it took effect instead of assuming the patch landed.
        # 引擎实际持有的控制器, 使隔离臂能证明补丁已生效, 而非假设。
        "incubation_controller_type": None,
        "incubation_controller_budget_ms": None,
        "style": args.style,
        "style_name": "skeleton" if args.style == 1 else "ring",
        "run": args.run,
        "target_index": args.target_index,
        "sync_pages": bool(args.sync_pages),
        "no_acrylic": bool(args.no_acrylic),
        "config_path": str(config_path),
        "sample_interval_ms": SAMPLE_INTERVAL_MS,
        "timeout_ms": args.timeout_ms,
        "settle_ms": args.settle_ms,
        "qt_version": _qt_version(),
        "pyside_version": _pyside_version(),
        "python": sys.version.split()[0],
        "visible_window_required": True,
    }
    state["report"] = report

    class StallProbeApp(gallery.App):
        """Drive the real Gallery and measure one lazy switch. 驱动真实 Gallery 并测量一次切换。"""

        def __init__(self, *app_args, **app_kwargs) -> None:
            super().__init__(*app_args, **app_kwargs)
            # Honour --no-verbose so the probe can reproduce the user's default
            # logging level instead of always forcing DEBUG.
            # 尊重 --no-verbose, 使探针能复现用户的默认日志级别而非总是强开 DEBUG。
            getLogger().set_level(Logger.INFO if args.no_verbose else Logger.DEBUG)
            state["app"] = self
            state["engine"] = self.engine

        def exec(self) -> int:
            engine = self.engine
            root_objects = engine.rootObjects()
            if not root_objects:
                report["failure"] = "qml root objects missing"
                _emit(report, args, state)
                return -1
            root = root_objects[0]
            window = root.property("windowInstance")
            if window is None or not isinstance(window, QQuickWindow):
                report["failure"] = "windowInstance missing or not a QQuickWindow"
                _emit(report, args, state)
                return -1

            report["root_type"] = type(root).__name__
            report["window_type"] = type(window).__name__
            report["window_visible"] = bool(window.isVisible())
            if args.window_height > 0:
                window.setHeight(int(args.window_height))
                report["window_height_override"] = int(args.window_height)
            renderer = window.rendererInterface()
            report["graphics_api"] = _enum_name(renderer.graphicsApi())
            screen = window.screen()
            report["screen_refresh_rate_hz"] = (
                float(screen.refreshRate()) if screen is not None else 0.0
            )
            if report["graphics_api"] != "Direct3D11":
                report["failure"] = (
                    "probe requires a real Direct3D11 window; actual="
                    + str(report["graphics_api"])
                )
                _emit(report, args, state)
                self._app.quit()
                return -1

            run = _Run(
                app=self._app,
                window=window,
                report=report,
                diagnostics=diagnostics,
                args=args,
                state=state,
                timer_cls=QTimer,
                object_cls=QObject,
                qt=Qt,
            )
            state["run"] = run
            run.arm()
            code = super().exec()
            state["exit_code"] = code
            return code

    gallery.App = StallProbeApp
    code = gallery.main()
    report["acrylic_calls"] = dict(acrylic_calls)
    report["exit_code"] = state.get("exit_code", code)
    report["process_end_ms"] = round(_now_ms(), 2)
    _emit(report, args, state)
    return int(code)


def _pyside_version() -> str:
    try:
        import PySide6

        return str(PySide6.__version__)
    except Exception:  # noqa: BLE001
        return "unknown"


class _Run:
    """One measured lazy switch on the real Gallery window. 真实窗口上一次被测量的懒加载切换。"""

    def __init__(
        self,
        *,
        app,
        window,
        report: dict,
        diagnostics: list,
        args: argparse.Namespace,
        state: dict,
        timer_cls,
        object_cls,
        qt,
    ) -> None:
        self.app = app
        self.window = window
        self.target_index = int(args.target_index)
        self.report = report
        self.diagnostics = diagnostics
        self.args = args
        self.state = state
        self.QTimer = timer_cls
        self.QObject = object_cls
        self.Qt = qt
        self.timeline: list = []
        self.tick_gaps: dict[str, list] = {name: [] for name in TICK_INTERVALS_MS}
        self.tick_last: dict[str, float] = {}
        self.switch_ms: float | None = None
        self.finished = False
        self.overlay = None
        self.stack = None
        self.helper = None
        self.transition = None
        self.collapse_started_ms: float | None = None
        self.collapse_finished_ms: float | None = None
        self.stage_timer = None
        self.guard = None
        self._skeleton_adjusted = False
        # Frame counters: the stall may be "the window stops rendering, so the
        # async (incubated) page creation never completes". Counting swapped frames
        # tests that directly instead of guessing from timings.
        # 帧计数: 卡死可能是"窗口停止出帧, 导致异步(孵化)的页面创建永不完成"。
        # 直接数已交换帧即可验证, 而不必从耗时反推。
        self.frames_swapped = 0
        self.frames_swapped_after_switch = 0
        self.target_loader = None
        self.timers: list = []
        self.signals: dict[str, list] = {
            "animationStarted": [],
            "animationFinished": [],
            "currentChanged": [],
            "pageLoaded": [],
            "pageLoadFailed": [],
            "pythonLazyTransitionFinished": [],
            "pythonLazyExpansionStarted": [],
            "pythonLazyCollapseFinished": [],
            "overlayFinished": [],
            "collapseStarted": [],
            "collapseFinished": [],
            "expandStarted": [],
            "expandFinished": [],
        }
        self.signal_errors: list[str] = []
        self.loader_status: list[list] = []
        self.overlay_intervals: list[list] = []
        self.overlay_visible_since: float | None = None
        self.overlay_seen_visible = False
        self.overlay_durations: list[float] = []
        self.display_converged_ms: float | None = None
        self.skeleton_rows_visible_max = 0
        self.last_snapshot: tuple | None = None
        self.completion_timer = None
        self.helper_state_seen: set[str] = set()
        self.ready_poll_errors: list[str] = []
        # Transition type sampled during the switch. A `Binding` with `when:` can
        # re-assert after a JS assignment, so the override must be observed rather
        # than assumed. / 带 when: 的 Binding 可能在 JS 赋值后重申, 因此覆写结果必须
        # 观测而非假设。
        self.transition_types: list[list] = []

    # ==================== Arming 武装 ====================
    def arm(self) -> None:
        report = self.report
        ready = {"done": False}

        def _poll_ready() -> None:
            if ready["done"] or self.finished:
                return
            try:
                _poll_ready_inner()
            except (RuntimeError, AttributeError, TypeError) as error:
                # Record instead of letting the timer slot die silently: a probe
                # that stops polling without saying so is worse than a failing one.
                # 记录而不是让定时器槽静默死掉: 停止轮询却不说, 比探针失败更糟。
                if len(self.ready_poll_errors) < 200:
                    self.ready_poll_errors.append(f"{type(error).__name__}: {error}")

        def _poll_ready_inner() -> None:
            stack = self.window.property("stackedWidget")
            if stack is None:
                return
            if int(stack.property("count") or 0) <= self.target_index:
                return
            # The Gallery disables the embedded splash (splashEnabled: false), so
            # `_splashDismissed` never turns true there. Requiring it made this
            # probe unable to ever arm. Gate on the shell being presentation-ready
            # instead, and keep the splash flags as reported state only.
            # Gallery 关闭了内嵌启动页(splashEnabled: false), 因此 `_splashDismissed`
            # 在那里永远不会变真; 以它为门禁会让探针永远无法武装。改为以"外壳呈现就绪"
            # 为门禁, 启动页标志仅作为上报状态。
            if not bool(self.window.property("_dwmInitializationDone")):
                return
            if not bool(self.window.property("_showAnimationStarted")):
                return
            overlay = self.window.findChild(self.QObject, "lazyLoadingOverlay")
            if overlay is None:
                return
            if int(stack.property("_displayIndex")) != 0:
                return
            if int(stack.property("currentIndex")) != 0:
                return
            loaders = _as_list(stack.property("_loaders"))
            if len(loaders) <= self.target_index or loaders[0] is None:
                return
            if _loader_ready(loaders[0]) is not True:
                return
            ready["done"] = True
            report["ready_ms"] = round(_now_ms(), 2)
            report["splash_dismissed_at_ready"] = bool(
                self.window.property("_splashDismissed")
            )
            report["loader_status_readable"] = _loader_status(loaders[0]) is not None
            # Prove which incubation controller is actually installed, so an
            # isolation arm cannot silently no-op. self.app is the QApplication,
            # so reach the engine through the published-engine accessor.
            # 证明实际安装的是哪个孵化控制器, 使隔离臂不会静默空转。self.app 是
            # QApplication, 因此通过已发布引擎访问器取得引擎。
            try:
                from prismqml.python.runtime.engine import get_or_create_qml_engine

                controller = get_or_create_qml_engine().incubationController()
                report["incubation_controller_type"] = (
                    type(controller).__name__ if controller is not None else None
                )
                report["incubation_controller_budget_ms"] = (
                    int(controller._budget_ms)
                    if controller is not None and hasattr(controller, "_budget_ms")
                    else None
                )
            except (AttributeError, RuntimeError, TypeError) as exc:
                report["incubation_controller_type"] = f"unreadable: {type(exc).__name__}"
            ready_timer.stop()
            # Disarm the readiness watchdog too. Leaving it armed let a long stall
            # measurement be killed by "gallery never became ready" at the ready
            # timeout, truncating every slow case to that exact duration.
            # 就绪看门狗也必须解除。留着它会让长时间卡死的测量在 ready 超时时被
            # "gallery never became ready" 杀掉, 把每个慢速用例都截断到该时长。
            ready_timeout.stop()
            self._bind_stack(stack, overlay)
            self._connect_frame_counter()
            if self.args.overlay_ring:
                self._overlay_render_ring(overlay)
            if self.args.overlay_touch_style:
                self._overlay_touch_style(overlay)
            if self.args.helper_sync:
                self._reload_helper_synchronously()
            if self.args.skeleton_loading_off or self.args.skeleton_layers_off:
                # Applied later, once the overlay is visible and populated: before
                # the switch the skeleton subtree is not built yet, so a walk here
                # only finds the layout container.
                # 稍后在遮罩可见且已填充时应用: 切换前骨架子树尚未构建, 此时遍历
                # 只能找到布局容器。
                pass
            settle_timer.start()

        def _settle_done() -> None:
            if self.finished:
                return
            report["baseline_ms"] = round(_now_ms(), 2)
            report["baseline"] = self._baseline()
            if self.args.override_target_source is not None:
                self._override_target_page()
            if self.args.force_circle:
                self._force_circle_transition()
            if self.args.force_none:
                self._force_none_transition()
            if self.args.activation_delay_ms >= 0:
                self._apply_activation_delay()
            self.QTimer.singleShot(0, self._do_switch)

        ready_timer = self.QTimer(self.app)
        ready_timer.setInterval(10)
        ready_timer.timeout.connect(_poll_ready)
        ready_timer.start()
        settle_timer = self.QTimer(self.app)
        settle_timer.setSingleShot(True)
        settle_timer.setInterval(self.args.settle_ms)
        settle_timer.timeout.connect(_settle_done)
        ready_timeout = self.QTimer(self.app)
        ready_timeout.setSingleShot(True)
        ready_timeout.setInterval(self.args.ready_timeout_ms)
        ready_timeout.timeout.connect(self._on_ready_timeout)
        ready_timeout.start()
        self.timers.extend([ready_timer, settle_timer, ready_timeout])

    def _on_ready_timeout(self) -> None:
        if self.finished:
            return
        self.report["failure"] = "gallery never became ready for a lazy switch"
        self.report["timed_out"] = True
        self._finish()

    # ==================== Binding 绑定 ====================
    def _bind_stack(self, stack, overlay) -> None:
        self.stack = stack
        self.overlay = overlay
        report = self.report
        report["stack_count"] = int(stack.property("count"))
        report["use_source_mode"] = bool(stack.property("_useSourceMode"))
        report["python_page_mode"] = bool(stack.property("_pythonPageMode"))
        report["lazy_loading"] = bool(stack.property("lazyLoading"))
        report["lazy_loading_style"] = int(stack.property("lazyLoadingStyle"))
        report["lazy_animation_type"] = int(stack.property("lazyAnimationType"))
        report["lazy_skeleton_style"] = bool(stack.property("_lazySkeletonStyle"))
        report["stack_animation_type"] = int(stack.property("animationType"))

        transition = stack.findChild(self.QObject, "lazyPageCircleTransition")
        self.transition = transition
        if transition is not None:
            report["transition_animation_type"] = int(transition.property("animationType"))
            report["transition_custom_animation"] = (
                transition.property("customAnimation") is not None
            )
            report["transition_backend_present"] = (
                transition.property("_backend") is not None
            )
            report["transition_contract_valid"] = bool(
                transition.property("_contractValid")
            )
            report["transition_cover_duration_ms"] = int(
                transition.property("coverDuration")
            )
            report["transition_reveal_duration_ms"] = int(
                transition.property("revealDuration")
            )
            report["transition_active_at_baseline"] = bool(
                transition.property("active")
            )

        raw_loaders = stack.property("_loaders")
        report["loaders_raw_type"] = type(raw_loaders).__name__
        loaders = _as_list(raw_loaders)
        report["loader_count"] = len(loaders)
        if len(loaders) > self.target_index:
            self.target_loader = loaders[self.target_index]
            report["target_loader_present"] = self.target_loader is not None
            report["target_loader_source"] = str(
                self.target_loader.property("source") or ""
            )

        report["overlay_object_name"] = overlay.objectName()
        self.helper = overlay.parent()
        if self.helper is not None:
            report["helper_type"] = type(self.helper).__name__
        self.stage_timer = self.window.findChild(self.QObject, "lazyLoaderActivateTimer")
        self.guard = self.window.findChild(self.QObject, "lazyOverlayLifecycleGuard")
        report["stage_timer_found"] = self.stage_timer is not None
        report["lifecycle_guard_found"] = self.guard is not None
        report["helper_loading_style"] = (
            int(self.helper.property("loadingStyle")) if self.helper is not None else None
        )
        report["helper_loader_activation_delay_ms"] = (
            int(self.helper.property("loaderActivationDelay"))
            if self.helper is not None
            else None
        )

        self._connect_signals()
        self._start_timers()
        self._observe_overlay(initial=True)

    def _connect_signals(self) -> None:
        pairs = (
            ("animationStarted", lambda: self._sig("animationStarted")),
            ("animationFinished", lambda: self._sig("animationFinished")),
            (
                "currentChanged",
                lambda index: self.signals["currentChanged"].append(
                    [round(_now_ms(), 2), int(index)]
                ),
            ),
            (
                "pageLoaded",
                lambda index: self.signals["pageLoaded"].append(
                    [round(_now_ms(), 2), int(index)]
                ),
            ),
            (
                "pageLoadFailed",
                lambda index, error: self.signals["pageLoadFailed"].append(
                    [round(_now_ms(), 2), int(index), str(error)]
                ),
            ),
            (
                "pythonLazyTransitionFinished",
                lambda index: self.signals["pythonLazyTransitionFinished"].append(
                    [round(_now_ms(), 2), int(index)]
                ),
            ),
            (
                "pythonLazyExpansionStarted",
                lambda index: self.signals["pythonLazyExpansionStarted"].append(
                    [round(_now_ms(), 2), int(index)]
                ),
            ),
            (
                "pythonLazyCollapseFinished",
                lambda index: self.signals["pythonLazyCollapseFinished"].append(
                    [round(_now_ms(), 2), int(index)]
                ),
            ),
        )
        for label, slot in pairs:
            signal = getattr(self.stack, label, None)
            if signal is None:
                self.signal_errors.append(f"{label}: signal missing")
                continue
            try:
                signal.connect(slot)
            except (TypeError, RuntimeError) as error:
                self.signal_errors.append(f"{label}: {error}")

        for label, slot in (
            ("visibleChanged", self._on_overlay_visible_changed),
            ("finished", self._on_overlay_finished),
        ):
            signal = getattr(self.overlay, label, None)
            if signal is None:
                self.signal_errors.append(f"overlay.{label}: signal missing")
                continue
            try:
                signal.connect(slot)
            except (TypeError, RuntimeError) as error:
                self.signal_errors.append(f"overlay.{label}: {error}")

        # The skeleton style drives PageTransition.animationType to none, which
        # makes collapseStarted/collapseFinished synchronous. Recording those four
        # signals on the transition itself is what proves whether the helper's
        # onCollapseFinished -> _completeLoadingCollapse -> _startLoadingOverlay
        # chain ran in the same event-loop turn.
        # 骨架样式把 PageTransition.animationType 置为 none, 使 collapseStarted/
        # collapseFinished 同步发出。在过渡对象上记录这四个信号, 即可证明 helper 的
        # onCollapseFinished -> _completeLoadingCollapse -> _startLoadingOverlay
        # 链路是否在同一事件循环回合内跑过。
        if self.transition is not None:
            for label in (
                "collapseStarted",
                "collapseFinished",
                "expandStarted",
                "expandFinished",
            ):
                signal = getattr(self.transition, label, None)
                if signal is None:
                    self.signal_errors.append(f"transition.{label}: signal missing")
                    continue
                try:
                    signal.connect(lambda name=label: self._sig(name))
                except (TypeError, RuntimeError) as error:
                    self.signal_errors.append(f"transition.{label}: {error}")
            started = getattr(self.transition, "collapseStarted", None)
            finished = getattr(self.transition, "collapseFinished", None)
            if started is not None and finished is not None:
                try:
                    started.connect(lambda: setattr(self, "collapse_started_ms", _now_ms()))
                    finished.connect(lambda: setattr(self, "collapse_finished_ms", _now_ms()))
                except (TypeError, RuntimeError) as error:
                    self.signal_errors.append(f"transition collapse timing: {error}")
        self.report["signal_errors"] = list(self.signal_errors)

    def _sig(self, name: str) -> None:
        self.signals[name].append([round(_now_ms(), 2)])

    def _on_overlay_visible_changed(self) -> None:
        self._observe_overlay()
        self._maybe_complete()

    def _on_overlay_finished(self) -> None:
        self.signals["overlayFinished"].append([round(_now_ms(), 2)])

    # ==================== Timers 计时器 ====================
    def _start_timers(self) -> None:
        for name, interval in TICK_INTERVALS_MS.items():
            timer = self.QTimer(self.app)
            timer.setTimerType(self.Qt.TimerType.PreciseTimer)
            timer.setInterval(interval)
            timer.timeout.connect(lambda key=name: self._record_tick(key))
            timer.start()
            self.timers.append(timer)
            self.tick_last[name] = _now_ms()

        poll = self.QTimer(self.app)
        poll.setTimerType(self.Qt.TimerType.PreciseTimer)
        poll.setInterval(SAMPLE_INTERVAL_MS)
        poll.timeout.connect(self._sample)
        poll.start()
        self.timers.append(poll)

        switch_timeout = self.QTimer(self.app)
        switch_timeout.setSingleShot(True)
        switch_timeout.setInterval(self.args.timeout_ms)
        switch_timeout.timeout.connect(self._on_switch_timeout)
        switch_timeout.start()
        self.timers.append(switch_timeout)

        self.completion_timer = self.QTimer(self.app)
        self.completion_timer.setSingleShot(True)
        self.completion_timer.setInterval(COMPLETION_GRACE_MS)
        self.completion_timer.timeout.connect(self._finish)
        self.timers.append(self.completion_timer)

    def _record_tick(self, key: str) -> None:
        now = _now_ms()
        last = self.tick_last.get(key)
        self.tick_last[key] = now
        if last is None:
            return
        self.tick_gaps[key].append((last, now - last))

    # ==================== Switch 切换 ====================
    def _override_target_page(self) -> None:
        """Point the target index at a different QML file at runtime.

        运行时把目标下标改指到另一个 QML 文件。

        Only the stack's own ``pageSources`` is rewritten; no product file is
        edited. This is the bisection knob for locating the stall inside
        NavigationPage.
        / 只改写 stack 自己的 ``pageSources``, 不编辑任何产品文件。这是把卡死定位到
        NavigationPage 内部某处的二分旋钮。
        """
        path = Path(self.args.override_target_source).resolve()
        if not path.is_file():
            self.report["override_error"] = f"not a file: {path}"
            return
        urls = _as_list(self.stack.property("pageSources"))
        if len(urls) <= self.target_index:
            self.report["override_error"] = "target index beyond pageSources"
            return
        urls[self.target_index] = QUrl.fromLocalFile(str(path)).toString()
        self.stack.setProperty("pageSources", urls)
        self.report["override_source"] = str(path)
        self.report["override_url"] = urls[self.target_index]

    def _force_circle_transition(self) -> None:
        """Keep the skeleton overlay but restore the circle page transition.

        保留骨架覆盖层, 但恢复圆圈页面过渡。

        The skeleton style normally binds the transition's ``animationType`` to
        ``Enums.lazyAnimation.none``; overriding it isolates "the none path is the
        cause" from "the skeleton overlay is the cause". Read-only with respect to
        product files.
        / 骨架样式通常把过渡的 ``animationType`` 绑定为 ``Enums.lazyAnimation.none``;
        覆写它即可把"none 路径是原因"与"骨架覆盖层是原因"分开。不修改任何产品文件。
        """
        transition = self.stack.findChild(self.QObject, "lazyPageCircleTransition")
        if transition is None:
            self.report["force_circle_error"] = "lazyPageCircleTransition not found"
            return
        self.report["force_circle_before"] = int(
            transition.property("animationType")
        )
        # Ask QML for the enum value instead of guessing a literal.
        # 向 QML 求取枚举值, 而不是猜字面量。
        circle_value = _qml_int(self.stack, "Enums.lazyAnimation.lazy_circle")
        if circle_value is None:
            self.report["force_circle_error"] = "could not resolve lazy_circle"
            return
        transition.setProperty("animationType", circle_value)
        self.report["force_circle_after"] = int(transition.property("animationType"))

    def _force_none_transition(self) -> None:
        """Keep the configured overlay style but force `animationType = none`.

        保留配置的覆盖层样式, 但强制 `animationType = none`。

        Reverse arm of --force-circle: proves the stall follows the `none` path
        rather than the skeleton overlay.
        / --force-circle 的反向臂: 证明卡死跟随 none 路径, 而非骨架覆盖层。
        """
        transition = self.stack.findChild(self.QObject, "lazyPageCircleTransition")
        if transition is None:
            self.report["force_none_error"] = "lazyPageCircleTransition not found"
            return
        self.report["force_none_before"] = int(transition.property("animationType"))
        none_value = _qml_int(self.stack, "Enums.lazyAnimation.none")
        if none_value is None:
            self.report["force_none_error"] = "could not resolve none"
            return
        transition.setProperty("animationType", none_value)
        self.report["force_none_after"] = int(transition.property("animationType"))

    def _apply_activation_delay(self) -> None:
        """Delay the target Loader activation to test the timing-race hypothesis.

        推迟目标 Loader 激活, 以验证时序竞争假设。

        With ``animationType = none`` the collapse finishes synchronously, so the
        Loader is activated roughly ``coverDuration`` earlier than with the circle
        transition. This knob pushes activation later without touching any product
        file, isolating "the race" from "the path".
        / ``animationType = none`` 时收紧同步完成, 目标 Loader 比圆圈过渡提前约
        ``coverDuration`` 被激活。本旋钮在不改产品文件的前提下把激活推后, 从而把
        "时序竞争"与"代码路径"分开。
        """
        self.stack.setProperty("lazyActivationDelay", int(self.args.activation_delay_ms))
        self.report["activation_delay_ms"] = int(self.args.activation_delay_ms)

    def _overlay_render_ring(self, overlay) -> None:
        """Make the wait overlay render the ring while style stays skeleton.

        在样式仍为骨架时, 让等待覆盖层渲染环形。

        Diagnostic only: the product keeps `style: helper.loadingStyle`. Overriding
        the overlay's own `style` separates "the skeleton overlay's rendering" from
        "the skeleton `none` transition path" as the cause of the stall.
        / 仅用于诊断: 产品仍为 `style: helper.loadingStyle`。覆写覆盖层自身的 `style`
        可把"骨架覆盖层的渲染"与"骨架的 none 过渡路径"分开。
        """
        ring_value = _qml_int(self.stack, "Enums.lazyLoadingStyle.style_ring")
        if ring_value is None:
            self.report["overlay_ring_error"] = "could not resolve style_ring"
            return
        self.report["overlay_ring_before"] = int(overlay.property("style"))
        overlay.setProperty("style", ring_value)
        self.report["overlay_ring_after"] = int(overlay.property("style"))

    def _maybe_adjust_skeleton_once(self) -> None:
        """Apply the skeleton bisect arm once, after the overlay is populated.

        在遮罩填充完成后只应用一次骨架二分臂。
        """
        if not (self.args.skeleton_loading_off or self.args.skeleton_layers_off):
            return
        if self._skeleton_adjusted:
            return
        overlay = self.overlay
        if overlay is None or not bool(overlay.property("visible")):
            return
        self._skeleton_adjusted = True
        try:
            self._adjust_skeleton_blocks(overlay)
        except (RuntimeError, AttributeError, TypeError, NameError) as exc:
            # A broken bisect arm must be visible: silently continuing would let an
            # arm that never took effect look like a real negative result.
            # 损坏的二分臂必须可见: 静默继续会让"其实没生效"的臂看起来像真实负结果。
            self.report["skeleton_adjust_error"] = f"{type(exc).__name__}: {exc}"

    def _adjust_skeleton_blocks(self, overlay) -> None:
        """Turn off parts of the skeleton overlay to bisect its cost.

        关掉骨架覆盖层的部分开销, 以二分其成本。

        The overlay's blocks each own a layer + MultiEffect mask plus an infinite
        shimmer. Disabling them one family at a time tells whether the page's
        stalled asynchronous creation is starved by the overlay's rendering or by
        its animations. Product files are untouched.
        / 覆盖层的每个块都带一层 layer + MultiEffect 遮罩以及无限闪光。逐类关闭即可
        判断目标页异步创建被饿死是覆盖层渲染还是动画所致。不修改产品文件。
        """
        if self.QObject is None:
            return
        from PySide6.QtQuick import QQuickItem

        def walk(item, depth=0):
            if item is None or depth > 30:
                return []
            try:
                children = item.childItems()
            except (RuntimeError, AttributeError):
                return []
            found = []
            for child in children:
                found.append(child)
                found.extend(walk(child, depth + 1))
            return found

        blocks = []
        subtree = []
        for item in walk(overlay):
            subtree.append(item)
            try:
                name = item.objectName()
            except RuntimeError:
                continue
            if name.startswith("qmlPageSkeleton"):
                blocks.append(item)

        report = self.report
        report["skeleton_blocks_found"] = len(blocks)
        report["skeleton_subtree_size"] = len(subtree)
        changed = 0
        layer_seen = 0
        layer_type = None
        layer_has_set = None
        for item in blocks:
            try:
                if self.args.skeleton_loading_off and item.property("loading") is not None:
                    if item.setProperty("loading", False):
                        changed += 1
            except (RuntimeError, AttributeError, TypeError):
                continue
        if self.args.skeleton_layers_off:
            # The layer lives on unnamed inner items (content container and mask
            # shape), not on the named Skeleton block itself, so every descendant
            # must be visited or nothing gets disabled.
            # layer 挂在未命名的内部项(内容容器与遮罩形状)上, 不在命名的 Skeleton
            # 块本身, 因此必须遍历全部后代, 否则一个都关不掉。
            #
            # PySide6 cannot read the grouped `layer` property: property("layer")
            # returned None for all 193 descendants. QML/JS can, so the walk is done
            # through a QQmlExpression instead of the Python property API.
            # PySide6 读不到分组属性 layer: 193 个后代全部返回 None。QML/JS 可以,
            # 因此改由 QQmlExpression 完成遍历, 而不是走 Python 属性 API。
            changed += self._disable_layers_via_qml(overlay)
        report["skeleton_layers_seen"] = layer_seen
        report["skeleton_layer_type"] = layer_type
        report["skeleton_layer_has_set"] = layer_has_set
        report["skeleton_blocks_changed"] = changed

    def _reload_helper_synchronously(self) -> None:
        """Reload the lazy helper Loader without sliced incubation.

        不经分片孵化地重载懒加载辅助器 Loader。

        Finds the Loader that sources ``LazyLoadingHelper.qml``, switches it to
        synchronous creation, and forces a fresh load. The page Loaders keep their
        asynchronous setting, so this isolates "the helper competes for the page
        incubation queue" from "page creation is asynchronous".
        / 找到加载 ``LazyLoadingHelper.qml`` 的 Loader, 改为同步创建并强制重新加载。
        页面 Loader 保持异步, 因此这能把"辅助器争用页面孵化队列"与"页面创建是异步的"
        分开。
        """
        stack = self.stack
        if stack is None:
            return
        helper_loader = None
        for child in stack.findChildren(self.QObject):
            try:
                source = child.property("source")
            except (RuntimeError, AttributeError, TypeError):
                continue
            if source is None:
                continue
            text = source.toString() if hasattr(source, "toString") else str(source)
            if "LazyLoadingHelper.qml" in text:
                helper_loader = child
                break

        report = self.report
        if helper_loader is None:
            report["helper_sync_error"] = "helper Loader not found"
            return

        report["helper_sync_source"] = "LazyLoadingHelper.qml"
        report["helper_sync_async_before"] = bool(
            helper_loader.property("asynchronous")
        )
        # Drop the current (asynchronously built) instance, then rebuild it with
        # sliced incubation disabled so the helper never enters the page queue.
        # 先丢弃当前(异步构建的)实例, 再在关闭分片孵化的情况下重建, 使辅助器不再
        # 进入页面队列。
        helper_loader.setProperty("active", False)
        helper_loader.setProperty("asynchronous", False)
        helper_loader.setProperty("active", True)
        report["helper_sync_async_after"] = bool(
            helper_loader.property("asynchronous")
        )
        report["helper_sync_active"] = bool(helper_loader.property("active"))
        # Let the synchronous load land before the switch is requested.
        # 让同步加载先落地, 再发起切换。
        for _ in range(40):
            if helper_loader.property("item") is not None:
                break
            self.app.processEvents()
        # The reload destroys the previous helper subtree, so every reference the
        # probe captured at startup is now dangling. Re-bind them or the first
        # sample touches a deleted QQuickItem.
        # 重载会销毁旧的辅助器子树, 因此探针启动时捕获的引用全部悬空。必须重新绑定,
        # 否则第一次采样就会访问已删除的 QQuickItem。
        self._rebind_helper_objects()

    def _rebind_helper_objects(self) -> None:
        """Re-capture the helper and overlay after the helper was reloaded.

        辅助器重载后重新捕获辅助器与遮罩。
        """
        window = self.window
        overlay = window.findChild(self.QObject, "lazyLoadingOverlay")
        helper = window.findChild(self.QObject, "lazyHelper")
        self.overlay = overlay
        self.helper = helper
        # The guard, stage timer and target loader also live inside the destroyed
        # helper subtree, so re-run the stack binding to refresh all of them.
        # 守卫、阶段计时器与目标 Loader 同样位于被销毁的辅助器子树内, 因此重跑一次
        # 栈绑定以刷新它们。
        if self.stack is not None and overlay is not None:
            self._bind_stack(self.stack, overlay)
        self.report["rebound_overlay"] = overlay is not None
        self.report["rebound_helper"] = helper is not None

    def _disable_layers_via_qml(self, overlay) -> int:
        """Disable every descendant layer through a QML expression.

        通过 QML 表达式关闭全部后代项的 layer。

        PySide6 cannot read the grouped ``layer`` property, but QML/JS can, so the
        subtree is walked from QML. Returns how many layers were switched off.
        / PySide6 读不到分组属性 ``layer``, 但 QML/JS 可以, 因此改从 QML 侧遍历子树。
        返回被关闭的图层数量。
        """
        try:
            from PySide6.QtQml import QQmlEngine, QQmlExpression
        except ImportError:
            self.report["skeleton_layers_error"] = "QtQml unavailable"
            return 0

        # contextForObject() returns a QQmlContext, not a QQmlEngine: reach the
        # engine through the context and take its root context.
        # contextForObject() 返回的是 QQmlContext 而非 QQmlEngine: 需经该上下文取引擎,
        # 再取引擎的根上下文。
        context = QQmlEngine.contextForObject(overlay)
        if context is None:
            self.report["skeleton_layers_error"] = "no qml context"
            return 0
        engine = context.engine() if hasattr(context, "engine") else None
        root = engine.rootContext() if engine is not None else context
        if root is None:
            self.report["skeleton_layers_error"] = "no root context"
            return 0
        # Publish the overlay under a probe-only name so the expression can reach
        # it without relying on scope-object `this` semantics.
        # 用一个探针专用名字发布遮罩, 使表达式无需依赖作用域对象的 this 语义即可访问。
        root.setContextProperty("__prismProbeOverlay", overlay)
        script = (
            "(function walk(item, depth) {"
            "  if (!item || depth > 30) return 0;"
            "  var count = 0;"
            "  if (item.layer !== undefined && item.layer !== null) {"
            "    item.layer.enabled = false;"
            "    count += 1;"
            "  }"
            "  var kids = item.children || [];"
            "  for (var i = 0; i < kids.length; i++) {"
            "    count += walk(kids[i], depth + 1);"
            "  }"
            "  return count;"
            "})(__prismProbeOverlay, 0)"
        )
        try:
            expression = QQmlExpression(root, None, script)
            value = expression.evaluate()
            if expression.hasError():
                self.report["skeleton_layers_error"] = "expression error"
                return 0
        except (RuntimeError, TypeError) as exc:
            self.report["skeleton_layers_error"] = f"{type(exc).__name__}: {exc}"
            return 0
        if isinstance(value, tuple):
            value = value[0]
        try:
            count = int(value)
        except (TypeError, ValueError):
            self.report["skeleton_layers_error"] = "non-numeric result"
            return 0
        self.report["skeleton_layers_disabled_by_qml"] = count
        return count

    def _overlay_touch_style(self, overlay) -> None:
        """Write the overlay's current style value back, unchanged.

        把覆盖层当前的 style 值原样写回。

        Used to tell whether ``--overlay-ring`` succeeds because of the ring content
        or merely because a runtime write happens at that moment.
        / 用于判断 --overlay-ring 的成功来自环形内容, 还是仅仅因为那一刻发生了一次
        运行期写入。
        """
        current = int(overlay.property("style"))
        self.report["overlay_touch_before"] = current
        overlay.setProperty("style", current)
        self.report["overlay_touch_after"] = int(overlay.property("style"))

    def _connect_frame_counter(self) -> None:
        """Count swapped frames so the stall can be tied to rendering activity.

        统计已交换帧, 以便把卡死与渲染活动关联起来。
        """
        window = self.window
        if window is None:
            return
        try:
            window.frameSwapped.connect(self._on_frame_swapped)
        except (RuntimeError, AttributeError, TypeError) as exc:
            self.report["frame_counter_error"] = f"{type(exc).__name__}: {exc}"

    def _on_frame_swapped(self) -> None:
        self.frames_swapped += 1
        if self.switch_ms is not None:
            self.frames_swapped_after_switch += 1

    def _do_switch(self) -> None:
        if self.finished:
            return
        self.switch_ms = _now_ms()
        self.report["switch_requested_ms"] = round(self.switch_ms, 2)
        self.report["switch_method"] = "window.currentIndex = 6 (navigation click path)"
        self.window.setProperty("currentIndex", self.target_index)
        self.report["host_current_index_after_request"] = int(
            self.window.property("currentIndex")
        )
        self.report["stack_current_index_after_request"] = int(
            self.stack.property("currentIndex")
        )
        self.report["stack_pending_switch_after_request"] = int(
            self.stack.property("_pendingLazySwitchIndex")
        )
        self._sample()

    # ==================== Sampling 采样 ====================
    def _sample(self) -> None:
        if self.finished or self.stack is None or self.overlay is None:
            return
        # A reloaded helper destroys its old subtree, so a captured reference can
        # go stale mid-run. Re-bind instead of touching a deleted QQuickItem,
        # which would abort the probe and leave its window process behind.
        # 重载辅助器会销毁其旧子树, 因此已捕获的引用可能在运行中失效。此时重新绑定,
        # 而不是访问已删除的 QQuickItem —— 那会中断探针并把窗口进程留在后台。
        if not _is_alive(self.stack) or not _is_alive(self.overlay):
            self.report["stale_reference_rebind"] = (
                self.report.get("stale_reference_rebind", 0) + 1
            )
            stack = self.window.property("stackedWidget")
            overlay = self.window.findChild(self.QObject, "lazyLoadingOverlay")
            if stack is None or overlay is None:
                return
            self.stack = stack
            self._bind_stack(stack, overlay)
            if not _is_alive(self.overlay):
                return
        snapshot = self._snapshot()
        if snapshot != self.last_snapshot:
            self.last_snapshot = snapshot
            if len(self.timeline) < TIMELINE_CAP:
                self.timeline.append([round(_now_ms(), 2), self._snapshot_dict(snapshot)])
            self._track_helper_state(snapshot)
        visible_rows = snapshot[SKELETON_ROWS_INDEX]
        if isinstance(visible_rows, (int, float)) and visible_rows > self.skeleton_rows_visible_max:
            self.skeleton_rows_visible_max = int(visible_rows)
        if (
            self.display_converged_ms is None
            and snapshot[0] == self.target_index
            and self.switch_ms is not None
        ):
            self.display_converged_ms = _now_ms()
            self.report["display_converged_ms"] = round(self.display_converged_ms, 2)
        self._observe_loader(snapshot)
        self._observe_transition_type()
        self._maybe_adjust_skeleton_once()
        self._maybe_complete()

    def _snapshot(self) -> tuple:
        stack = self.stack
        overlay = self.overlay
        helper = self.helper
        stage = self.stage_timer
        guard = self.guard
        return (
            int(stack.property("_displayIndex")),
            int(stack.property("currentIndex")),
            int(stack.property("previousIndex")),
            int(stack.property("_pendingLazySwitchIndex")),
            int(stack.property("_pythonLazyTransitionTargetIndex")),
            bool(stack.property("busy")),
            bool(overlay.property("visible")),
            bool(overlay.property("finishing")),
            bool(overlay.property("running")),
            int(helper.property("pendingTargetIndex")) if helper is not None else None,
            bool(helper.property("isLoadingSwitching")) if helper is not None else None,
            int(helper.property("_deferredRevealTarget")) if helper is not None else None,
            bool(helper.property("_waitIndicatorFinished")) if helper is not None else None,
            bool(helper.property("_targetExpansionFinished"))
            if helper is not None
            else None,
            bool(helper.property("_initialLoading")) if helper is not None else None,
            int(helper.property("internalLastIndex")) if helper is not None else None,
            bool(stage.property("running")) if stage is not None else None,
            int(stage.property("interval")) if stage is not None else None,
            bool(stage.property("_activationPhase")) if stage is not None else None,
            bool(stage.property("_renderPhase")) if stage is not None else None,
            int(stage.property("targetIndex")) if stage is not None else None,
            bool(guard.property("running")) if guard is not None else None,
            _loader_ready(self.target_loader),
            bool(self.target_loader.property("active"))
            if self.target_loader is not None
            else None,
            self._visible_skeleton_rows(),
            float(guard.property("_visibleElapsed")) if guard is not None else None,
            int(guard.property("_ownedBudget")) if guard is not None else None,
            float(guard.property("_visibleSince")) if guard is not None else None,
        )

    @staticmethod
    def _snapshot_keys() -> tuple[str, ...]:
        return (
            "displayIndex",
            "currentIndex",
            "previousIndex",
            "pendingLazySwitchIndex",
            "pythonTargetIndex",
            "busy",
            "overlayVisible",
            "overlayFinishing",
            "overlayRunning",
            "helperPendingTargetIndex",
            "helperIsLoadingSwitching",
            "helperDeferredRevealTarget",
            "helperWaitIndicatorFinished",
            "helperTargetExpansionFinished",
            "helperInitialLoading",
            "helperInternalLastIndex",
            "stageTimerRunning",
            "stageTimerIntervalMs",
            "stageTimerActivationPhase",
            "stageTimerRenderPhase",
            "stageTimerTargetIndex",
            "lifecycleGuardRunning",
            "targetLoaderReady",
            "targetLoaderActive",
            "skeletonRowsVisible",
            "guardVisibleElapsedMs",
            "guardOwnedBudgetMs",
            "guardVisibleSince",
        )

    def _snapshot_dict(self, snapshot: tuple) -> dict:
        return dict(zip(self._snapshot_keys(), snapshot))

    def _visual_descendants(self, item) -> list:
        """Every visual descendant, in tree order. 全部可视后代, 按树序。

        Repeater delegates are visual children of the Repeater's parent but are not
        parented to it as QObjects, so ``findChildren`` cannot see them; the visual
        tree is the only view that contains every skeleton block.
        Repeater 委托是 Repeater 父项的可视子项, 但其 QObject 父级不是它, 因此
        ``findChildren`` 看不到它们; 只有可视树包含全部骨架块。
        """
        found: list = []
        try:
            children = item.childItems()
        except (AttributeError, RuntimeError):
            return found
        for child in children:
            found.append(child)
            found.extend(self._visual_descendants(child))
        return found

    def _skeleton_rows(self, visible_only: bool) -> int:
        if self.overlay is None:
            return 0
        count = 0
        for item in self._visual_descendants(self.overlay):
            try:
                if item.objectName() != "qmlPageSkeletonRow":
                    continue
                if visible_only and not bool(item.property("visible")):
                    continue
            except (RuntimeError, AttributeError):
                continue
            count += 1
        return count

    def _visible_skeleton_rows(self) -> int:
        return self._skeleton_rows(visible_only=True)

    def _skeleton_rows_total(self) -> int:
        return self._skeleton_rows(visible_only=False)

    def _observe_transition_type(self) -> None:
        """Record the transition's animationType whenever it changes.

        过渡 animationType 变化时记录之。

        Used to detect a ``Binding`` re-asserting after the JS override, which
        would silently invalidate an isolation arm.
        / 用于检测 JS 覆写后 Binding 是否重申, 否则隔离臂会被静默作废。
        """
        transition = self.stack.findChild(self.QObject, "lazyPageCircleTransition")
        if transition is None:
            return
        try:
            value = int(transition.property("animationType"))
        except (RuntimeError, AttributeError, TypeError):
            return
        if not self.transition_types or self.transition_types[-1][1] != value:
            self.transition_types.append([round(_now_ms(), 2), value])

    def _observe_loader(self, snapshot: tuple) -> None:
        ready = snapshot[STATUS_INDEX]
        active = snapshot[STATUS_INDEX + 1]
        if not self.loader_status or self.loader_status[-1][1] != ready:
            self.loader_status.append([round(_now_ms(), 2), ready, active])

    def _track_helper_state(self, snapshot: tuple) -> None:
        state = self._snapshot_dict(snapshot)
        for key in (
            "helperPendingTargetIndex",
            "helperIsLoadingSwitching",
            "helperDeferredRevealTarget",
            "helperWaitIndicatorFinished",
            "helperTargetExpansionFinished",
            "stageTimerRunning",
            "stageTimerRenderPhase",
            "stageTimerActivationPhase",
            "overlayVisible",
            "overlayFinishing",
        ):
            self.helper_state_seen.add(f"{key}={state[key]}")

    def _observe_overlay(self, initial: bool = False) -> None:
        if self.overlay is None:
            return
        visible = bool(self.overlay.property("visible"))
        now = _now_ms()
        if initial:
            self.overlay_intervals.append([round(now, 2), "initial", visible])
            self.overlay_visible_since = now if visible else None
            self.overlay_seen_visible = visible
            self.report["overlay_visible_at_baseline"] = visible
            return
        self.overlay_intervals.append([round(now, 2), "visible", visible])
        if visible:
            self.overlay_seen_visible = True
            if self.overlay_visible_since is None:
                self.overlay_visible_since = now
                if self.switch_ms is not None:
                    self.report["overlay_visible_true_ms"] = round(now, 2)
        elif self.overlay_visible_since is not None:
            duration = now - self.overlay_visible_since
            self.overlay_durations.append(round(duration, 2))
            self.report["overlay_visible_false_ms"] = round(now, 2)
            self.report["overlay_visible_duration_ms"] = round(duration, 2)
            self.overlay_visible_since = None

    def _baseline(self) -> dict:
        return {
            "displayIndex": int(self.stack.property("_displayIndex")),
            "currentIndex": int(self.stack.property("currentIndex")),
            "overlayVisible": bool(self.overlay.property("visible")),
            "helperPendingTargetIndex": int(self.helper.property("pendingTargetIndex"))
            if self.helper is not None
            else None,
            "targetLoaderReady": _loader_ready(self.target_loader),
            "skeletonRowsTotal": self._skeleton_rows_total(),
            "skeletonRowsVisible": self._visible_skeleton_rows(),
            "skeletonLoaderActive": self._skeleton_loader_active(),
        }

    def _skeleton_loader_active(self) -> bool | None:
        if self.overlay is None:
            return None
        loader = self.overlay.findChild(self.QObject, "qmlPageSkeletonLoader")
        return bool(loader.property("active")) if loader is not None else None

    # ==================== Completion 收尾 ====================
    def _maybe_complete(self) -> None:
        if self.finished or self.switch_ms is None or self.completion_timer is None:
            return
        if self.completion_timer.isActive():
            return
        visible = bool(self.overlay.property("visible"))
        elapsed = _now_ms() - self.switch_ms
        settled = False
        if self.overlay_seen_visible and not visible:
            settled = True
        elif not self.overlay_seen_visible and elapsed >= OVERLAY_ABSENT_GRACE_MS:
            settled = int(self.stack.property("_displayIndex")) == self.target_index
        if settled:
            self.completion_timer.start()

    def _on_switch_timeout(self) -> None:
        if self.finished:
            return
        self.report["timed_out"] = True
        self.report["timeout_snapshot"] = self._timeout_snapshot()
        self._finish()

    def _timeout_snapshot(self) -> dict:
        timers = []
        for timer in self.timers:
            try:
                timers.append(
                    {
                        "object_name": timer.objectName(),
                        "interval": int(timer.interval()),
                        "running": bool(timer.isActive()),
                        "single_shot": bool(timer.isSingleShot()),
                    }
                )
            except RuntimeError:
                continue
        return {
            "timeline_tail": self.timeline[-15:],
            "loader_status_tail": self.loader_status[-8:],
            "timer_state": timers,
            "overlay_still_visible": bool(self.overlay.property("visible")),
            "helper_pending_target": int(self.helper.property("pendingTargetIndex"))
            if self.helper is not None
            else None,
            "display_index": int(self.stack.property("_displayIndex")),
        }

    def _finish(self) -> None:
        if self.finished:
            return
        self.finished = True
        for timer in self.timers:
            try:
                timer.stop()
            except RuntimeError:
                continue
        self._observe_overlay()
        self._finalize()
        self.QTimer.singleShot(50, self.app.quit)

    def _finalize(self) -> None:
        report = self.report
        switch_ms = self.switch_ms
        end_ms = _now_ms()
        report["overlay_visible_at_end"] = (
            bool(self.overlay.property("visible")) if self.overlay is not None else None
        )
        if self.overlay_visible_since is not None:
            report["overlay_still_visible_at_end_ms"] = round(end_ms, 2)
            report["overlay_visible_duration_ms"] = round(
                end_ms - self.overlay_visible_since, 2
            )
            report["overlay_visible_duration_capped_ms"] = self.args.timeout_ms
            report["overlay_exit_observed"] = False
        else:
            report.setdefault("overlay_exit_observed", True)
        report["overlay_visible_intervals"] = self.overlay_intervals
        report["overlay_visible_durations_ms"] = self.overlay_durations
        report["skeleton_rows_total"] = (
            self._skeleton_rows_total() if self.overlay is not None else 0
        )
        report["skeleton_rows_visible_max"] = self.skeleton_rows_visible_max
        report["skeleton_loader_active_at_end"] = self._skeleton_loader_active()
        report["display_index_converged"] = self.display_converged_ms is not None
        # Never let a missing stack abort the report: this script's whole job is to
        # persist whatever was observed, including a failure to reach the switch.
        # 绝不让 stack 缺失中断报告: 本脚本的职责就是落盘一切已观测内容,
        # 包括"未能到达切换"这一结果本身。
        if self.stack is None:
            report["display_index_at_end"] = None
            report["current_index_at_end"] = None
            self._finalize_without_stack()
            return
        report["display_index_at_end"] = int(self.stack.property("_displayIndex"))
        report["current_index_at_end"] = int(self.stack.property("currentIndex"))
        if self.display_converged_ms is not None and switch_ms is not None:
            report["display_converged_after_switch_ms"] = round(
                self.display_converged_ms - switch_ms, 2
            )
        if "overlay_visible_true_ms" in report and switch_ms is not None:
            report["overlay_visible_true_after_switch_ms"] = round(
                report["overlay_visible_true_ms"] - switch_ms, 2
            )
        if "overlay_visible_false_ms" in report and switch_ms is not None:
            report["overlay_visible_false_after_switch_ms"] = round(
                report["overlay_visible_false_ms"] - switch_ms, 2
            )
        report["transition_type_timeline"] = self.transition_types
        report["frames_swapped_total"] = self.frames_swapped
        report["frames_swapped_after_switch"] = self.frames_swapped_after_switch
        report["signals"] = self.signals
        # Each entry is [t_ms, loaderReady, loaderActive]; readiness comes from
        # QML because the enum cannot be marshalled on this Qt build.
        # 每项为 [t_ms, loaderReady, loaderActive]; 就绪由 QML 判定, 因本 Qt 构建
        # 无法编排该枚举。
        report["loader_status_sequence"] = self.loader_status
        ready_entries = [entry for entry in self.loader_status if entry[1] is True]
        report["target_loader_ready_observed"] = bool(ready_entries)
        report["target_loader_first_ready_ms"] = (
            ready_entries[0][0] if ready_entries else None
        )
        if ready_entries and switch_ms is not None:
            report["target_loader_first_ready_after_switch_ms"] = round(
                ready_entries[0][0] - switch_ms, 2
            )
        report["state_timeline"] = self.timeline
        report["state_timeline_entries"] = len(self.timeline)
        report["helper_states_observed"] = sorted(self.helper_state_seen)
        self._finalize_guard_analysis()
        self._finalize_collapse_timing()
        self._finalize_polling_timing()
        report["tick_stats"] = {key: self._tick_stats(key) for key in TICK_INTERVALS_MS}
        report["diagnostics"] = self._diagnostic_entries()
        report["diagnostics_count"] = len(self.diagnostics)

    def _finalize_without_stack(self) -> None:
        """Persist the report when the stack never appeared. 未出现 stack 时也落盘报告。"""
        report = self.report
        report["stack_never_became_ready"] = True
        report["signals"] = self.signals
        report["loader_status_sequence"] = self.loader_status
        report["state_timeline"] = self.timeline
        report["state_timeline_entries"] = len(self.timeline)
        report["helper_states_observed"] = sorted(self.helper_state_seen)
        report["tick_stats"] = {key: self._tick_stats(key) for key in TICK_INTERVALS_MS}
        report["diagnostics"] = self._diagnostic_entries()
        report["diagnostics_count"] = len(self.diagnostics)
        report["ready_poll_errors"] = self.ready_poll_errors[:50]
        report["ready_poll_error_count"] = len(self.ready_poll_errors)
        report["overlay_object_name"] = None

    def _finalize_guard_analysis(self) -> None:
        """Report whether the lifecycle guard budget ever elapsed. 报告守卫预算是否曾经走完。"""
        report = self.report
        elapsed_values = [
            entry[1]["guardVisibleElapsedMs"]
            for entry in self.timeline
            if entry[1].get("guardVisibleElapsedMs") is not None
        ]
        budgets = [
            entry[1]["guardOwnedBudgetMs"]
            for entry in self.timeline
            if entry[1].get("guardOwnedBudgetMs") is not None
        ]
        pending_values = [
            entry[1]["helperPendingTargetIndex"]
            for entry in self.timeline
            if entry[1].get("helperPendingTargetIndex") is not None
        ]
        report["guard_visible_elapsed_max_ms"] = (
            round(max(elapsed_values), 3) if elapsed_values else None
        )
        report["guard_visible_elapsed_distinct_values"] = sorted(
            {round(value, 3) for value in elapsed_values}
        )
        report["guard_owned_budget_ms"] = budgets[0] if budgets else None
        report["guard_budget_ever_elapsed"] = (
            bool(elapsed_values)
            and budgets
            and max(elapsed_values) >= budgets[0]
        )
        report["guard_visible_elapsed_ever_grew"] = (
            len({round(value, 3) for value in elapsed_values}) > 1
        )
        report["helper_pending_target_max"] = (
            max(pending_values) if pending_values else None
        )
        # A guard whose elapsed time never grows while a target is still pending
        # cannot bound the overlay: the 3000ms budget is unreachable on that path.
        # 当目标仍待处理而守卫计时永不增长时, 3000ms 预算在该路径上不可达, 遮罩无界。
        report["guard_budget_unreachable_while_owned"] = (
            report["guard_budget_ever_elapsed"] is False
            and (report["helper_pending_target_max"] or -1) >= 0
        )

    def _finalize_collapse_timing(self) -> None:
        """Report the PageTransition collapse timing for the measured switch."""
        report = self.report
        started = self.collapse_started_ms
        finished = self.collapse_finished_ms
        switch_ms = self.switch_ms
        report["collapse_started_ms"] = round(started, 2) if started else None
        report["collapse_finished_ms"] = round(finished, 2) if finished else None
        report["collapse_signal_received"] = finished is not None
        report["collapse_synchronous"] = (
            started is not None
            and finished is not None
            and abs(finished - started) < 0.05
        )
        if switch_ms is not None:
            if started is not None:
                report["collapse_started_after_switch_ms"] = round(
                    started - switch_ms, 2
                )
            if finished is not None:
                report["collapse_finished_after_switch_ms"] = round(
                    finished - switch_ms, 2
                )
        if started is not None and finished is not None:
            report["collapse_duration_ms"] = round(finished - started, 3)
        collapse_signals = self.signals.get("collapseFinished") or []
        report["collapse_finished_signal_count"] = len(collapse_signals)
        # The skeleton style must still deliver collapseFinished; without it the
        # helper never runs _completeLoadingCollapse and never shows the overlay.
        # 骨架样式仍必须送达 collapseFinished; 否则 helper 不会执行
        # _completeLoadingCollapse, 遮罩也不会显示。
        report["skeleton_collapse_chain_ok"] = (
            self.report.get("lazy_skeleton_style") is not True
            or len(collapse_signals) >= 1
        )

    def _finalize_polling_timing(self) -> None:
        """Time the 1ms render-poll phase against the target Loader status.

        把 1ms 渲染轮询阶段与目标 Loader 状态对齐计时。"""
        report = self.report
        poll_entries = [
            entry
            for entry in self.timeline
            if entry[1].get("stageTimerRunning")
            and entry[1].get("stageTimerIntervalMs") == 1
        ]
        report["poll_phase_entry_count"] = len(poll_entries)
        report["poll_phase_first_ms"] = poll_entries[0][0] if poll_entries else None
        report["poll_phase_last_ms"] = poll_entries[-1][0] if poll_entries else None
        if poll_entries and self.switch_ms is not None:
            report["poll_phase_first_after_switch_ms"] = round(
                poll_entries[0][0] - self.switch_ms, 2
            )
        ready_entries = [entry for entry in self.loader_status if entry[1] is True]
        if poll_entries and ready_entries:
            report["poll_to_loader_ready_ms"] = round(
                ready_entries[0][0] - poll_entries[0][0], 2
            )
        # A Loader that reaches Ready long after the poll started points at page
        # creation/incubation being starved by the 1ms repeat timer; a Loader that
        # is Ready early while the overlay stays up points at the exit condition.
        # Loader 在轮询开始很久后才 Ready 说明页面创建/孵化被 1ms 重复定时器饿死;
        # Loader 早已 Ready 而遮罩仍不退则说明问题在退场条件。
        report["poll_to_ready_exceeds_1000ms"] = (
            report.get("poll_to_loader_ready_ms") is not None
            and report["poll_to_loader_ready_ms"] > 1000
        )

    def _tick_stats(self, key: str) -> dict:
        expected = TICK_INTERVALS_MS[key]
        gaps = self.tick_gaps[key]
        switch_ms = self.switch_ms
        after = [item for item in gaps if switch_ms is None or item[0] >= switch_ms]
        before = [item for item in gaps if switch_ms is not None and item[0] < switch_ms]

        def _stats(entries: list) -> dict:
            if not entries:
                return {
                    "count": 0,
                    "max_gap_ms": None,
                    "mean_gap_ms": None,
                    "stall_total_ms": 0.0,
                    "stall_event_count": 0,
                    "stall_events": [],
                }
            values = [item[1] for item in entries]
            stall = [(item[0], item[1] - expected) for item in entries]
            stall_events = [
                [round(stamp, 2), round(over, 2)]
                for stamp, over in stall
                if over > expected * STALL_THRESHOLD_FACTOR
            ]
            return {
                "count": len(values),
                "max_gap_ms": round(max(values), 2),
                "mean_gap_ms": round(sum(values) / len(values), 3),
                "stall_total_ms": round(sum(max(0.0, over) for _, over in stall), 2),
                "stall_event_count": len(stall_events),
                "stall_events": stall_events[:TICK_EVENT_CAP],
            }

        return {
            "expected_interval_ms": expected,
            "stall_threshold_ms": expected * STALL_THRESHOLD_FACTOR,
            "all": _stats(gaps),
            "before_switch": _stats(before),
            "after_switch": _stats(after),
        }

    def _diagnostic_entries(self) -> list:
        switch_ms = self.switch_ms
        entries = []
        for stamp, message in self.diagnostics:
            entry = {"t_ms": stamp, "message": message}
            if switch_ms is not None:
                entry["t_rel_switch_ms"] = round(stamp - switch_ms, 2)
            entries.append(entry)
        return entries


if __name__ == "__main__":
    raise SystemExit(main())
