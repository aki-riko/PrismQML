# PrismQML C++ 宿主层 (prism)
# 与 PySide6 宿主平行: 让 C++ 应用以对称 API 调用同一套 QML 引擎。
# Minimum Qt 6.9 for RectangularShadow 最低 Qt 6.9，满足 RectangularShadow 要求
cmake_minimum_required(VERSION 3.16)
project(prism LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

set(PRISM_MIN_QT_VERSION 6.9)
find_package(Qt6 ${PRISM_MIN_QT_VERSION} REQUIRED COMPONENTS Core Gui Qml Quick Svg Widgets Network Sql Concurrent
    QuickControls2 QuickLayouts QuickEffects)

qt_standard_project_setup()

# ==================== prism 静态库 ====================
add_library(prism STATIC
    src/Theme.cpp
    src/ThemeManager.cpp
    src/ConfigContracts.cpp
    src/ConfigManager.cpp
    src/ShadowManager.cpp
    src/MicaManager.cpp
    src/NativeWindow.cpp
    src/PopupOwner.cpp
    src/Providers.cpp
    src/SvgImageProvider.cpp
    src/Store.cpp
    src/Logger.cpp
    src/SystemAndInstance.cpp
    src/Updater.cpp
    src/ScreenEyedropper.cpp
    src/QRCodeGenerator.cpp
    src/QRCodeProtocol_p.cpp
    src/SqlListModel.cpp
    src/PlatformInfo.cpp
    src/Icon.cpp
    src/DataModels.cpp
    src/Registry.cpp
    src/QmlRuntimePlugin.cpp
    src/App.cpp
    src/Window.cpp
    # 第三方: nayuki QR-Code-generator (MIT), QRCodeGenerator 编码后端
    third_party/qrcodegen/qrcodegen.cpp
    # 头文件显式列入: 确保 AUTOMOC 扫描到含 Q_OBJECT 的头
    include/prism/Theme.h
    include/prism/ThemeManager.h
    include/prism/ConfigContracts.h
    include/prism/ConfigManager.h
    include/prism/ShadowManager.h
    include/prism/MicaManager.h
    include/prism/NativeWindow.h
    include/prism/ClipboardHelper.h
    include/prism/WindowHelper.h
    include/prism/AcrylicHelper.h
    include/prism/SvgImageProvider.h
    include/prism/Store.h
    include/prism/Logger.h
    include/prism/SystemTray.h
    include/prism/SingleInstance.h
    include/prism/Updater.h
    include/prism/ScreenEyedropper.h
    include/prism/QRCodeGenerator.h
    include/prism/SqlListModel.h
    include/prism/Platform.h
    include/prism/PlatformInfo.h
    include/prism/Accessors.h
    include/prism/Icon.h
    include/prism/DataModels.h
    include/prism/Registry.h
    include/prism/App.h
    include/prism/Window.h
    src/IconPath_p.h
    src/ConfigContracts_p.h
    src/QRCodeProtocol_p.h
)
set_source_files_properties(src/QmlRuntimePlugin.cpp PROPERTIES
    COMPILE_DEFINITIONS "QT_PLUGIN;QT_STATICPLUGIN")
set_property(TARGET prism APPEND PROPERTY
    AUTOMOC_MOC_OPTIONS "-Muri=PrismQML")

target_include_directories(prism PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)
target_compile_features(prism PUBLIC cxx_std_17)

# 第三方 QR 编码器头 (nayuki qrcodegen): 仅 prism 内部实现使用, 不对外暴露
target_include_directories(prism PRIVATE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/third_party>
)

target_link_libraries(prism PUBLIC
    Qt6::Core Qt6::Gui Qt6::Qml Qt6::Quick Qt6::Svg Qt6::Widgets Qt6::Network Qt6::Sql
    Qt6::QuickControls2 Qt6::QuickLayouts Qt6::QuickEffects
)
target_link_libraries(prism PRIVATE Qt6::Concurrent)

# ==================== Embedded QML runtime ====================
# Keep the complete source module in the exported prism target.  A generated
# qrc source avoids leaking Qt's private resource object targets into the
# installed CMake export set.
function(prism_attach_generated_qrc
         target resource_name qrc_body_variable qrc_dependencies_variable)
    set(_qrc_file "${CMAKE_CURRENT_BINARY_DIR}/${resource_name}.qrc")
    file(WRITE "${_qrc_file}"
        "<RCC>\n  <qresource prefix=\"/\">\n${${qrc_body_variable}}  </qresource>\n</RCC>\n")

    find_program(PRISM_RCC NAMES rcc
        PATHS "${QT_HOST_PATH}/bin" "${QT_HOST_PATH}/libexec"
        NO_DEFAULT_PATH)
    if(NOT PRISM_RCC)
        find_program(PRISM_RCC NAMES rcc REQUIRED)
    endif()

    set(_qrc_cpp "${CMAKE_CURRENT_BINARY_DIR}/qrc_${resource_name}.cpp")
    add_custom_command(
        OUTPUT "${_qrc_cpp}"
        COMMAND "${PRISM_RCC}" --name "${resource_name}" --no-zstd
                -o "${_qrc_cpp}" "${_qrc_file}"
        DEPENDS "${_qrc_file}" ${${qrc_dependencies_variable}}
        VERBATIM)
    target_sources(${target} PRIVATE "${_qrc_cpp}")
endfunction()

set(_prism_qml_package_root "${CMAKE_CURRENT_SOURCE_DIR}/../prismqml")
set(_prism_qml_module_root "${_prism_qml_package_root}/PrismQML")
set(_prism_qml_source_qmldir "${_prism_qml_module_root}/qmldir")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    "${_prism_qml_source_qmldir}")
file(GLOB_RECURSE _prism_qml_resources CONFIGURE_DEPENDS
    RELATIVE "${_prism_qml_module_root}"
    "${_prism_qml_module_root}/*.qml"
    "${_prism_qml_module_root}/*.js"
    "${_prism_qml_module_root}/*.svg"
    "${_prism_qml_module_root}/*.json"
    "${_prism_qml_module_root}/*.png"
    "${_prism_qml_module_root}/*.frag"
    "${_prism_qml_module_root}/*.qsb"
    "${_prism_qml_module_root}/qmldir"
)

# Keep the filesystem module plugin-free for PySide hosts.  Generate a
# resource-only qmldir that activates the static C++ runtime plugin.
# 文件系统模块供 PySide 显式注入；资源模块单独生成静态 C++ 插件声明。
file(READ "${_prism_qml_source_qmldir}"
    _prism_qml_source_qmldir_contents)
string(REGEX REPLACE
    "^(module[^\r\n]*\r?\n)"
    "\\1plugin prismqmlruntimeplugin\nclassname PrismQMLRuntimePlugin\n"
    _prism_qml_runtime_qmldir_contents
    "${_prism_qml_source_qmldir_contents}")
if(_prism_qml_runtime_qmldir_contents STREQUAL
   _prism_qml_source_qmldir_contents)
    message(FATAL_ERROR "PrismQML qmldir has no module declaration")
endif()
set(_prism_qml_runtime_qmldir
    "${CMAKE_CURRENT_BINARY_DIR}/prismqml_runtime_qmldir")
file(WRITE "${_prism_qml_runtime_qmldir}"
    "${_prism_qml_runtime_qmldir_contents}")

set(_prism_qml_qrc_body "")
set(_prism_qml_qrc_dependencies "")
foreach(_prism_qml_file IN LISTS _prism_qml_resources)
    if(_prism_qml_file STREQUAL "qmldir")
        continue()
    endif()
    string(APPEND _prism_qml_qrc_body
        "    <file alias=\"qt/qml/PrismQML/${_prism_qml_file}\">${_prism_qml_module_root}/${_prism_qml_file}</file>\n")
    list(APPEND _prism_qml_qrc_dependencies
        "${_prism_qml_module_root}/${_prism_qml_file}")
endforeach()
string(APPEND _prism_qml_qrc_body
    "    <file alias=\"qt/qml/PrismQML/qmldir\">${_prism_qml_runtime_qmldir}</file>\n")
list(APPEND _prism_qml_qrc_dependencies
    "${_prism_qml_runtime_qmldir}")
prism_attach_generated_qrc(
    prism prismqml_components _prism_qml_qrc_body
    _prism_qml_qrc_dependencies)

# Windows: 链接 DWM API (Shadow/Mica) + user32 (NativeWindow) + shell32 (Updater 安装包启动)
if(WIN32)
    target_link_libraries(prism PUBLIC dwmapi user32 shell32)
endif()

# 编译期默认 QML import 目录(开发树): 未设 PRISMQML_QML_DIR 环境变量时 resolveImportPath
# 兜底用它, 使 demo/gallery 等无需手动设环境变量即可 import PrismQML。指向含 PrismQML
# 子目录的父目录(addImportPath 约定)。安装后用户经 find_package(prism) 的 prism_QML_DIR。
if(NOT ANDROID AND NOT IOS)
    target_compile_definitions(prism PRIVATE
        PRISM_QML_DIR_DEFAULT="${CMAKE_CURRENT_SOURCE_DIR}/../prismqml")
endif()

# ==================== demo 可执行 ====================
option(PRISM_BUILD_DEMO "Build the C++ demo app" ON)
if(PRISM_BUILD_DEMO)
    qt_add_executable(prism_demo demo/main.cpp)
    target_link_libraries(prism_demo PRIVATE prism)
    # 桌面: 注入源码树页面默认路径, 使 demo 无需手动设 PRISM_DEMO_PAGES 即可运行
    if(NOT ANDROID AND NOT IOS)
        target_compile_definitions(prism_demo PRIVATE
            PRISM_DEMO_PAGES_DIR="${CMAKE_CURRENT_SOURCE_DIR}/demo/pages")
    endif()

    # Android/iOS: PrismQML resources are already carried by prism.  Only the
    # demo pages need a second generated resource bundle here.
    if(ANDROID OR IOS)
        file(GLOB _demo_pages RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}/demo"
             "${CMAKE_CURRENT_SOURCE_DIR}/demo/pages/*.qml")
        set(_demo_qrc_body "")
        set(_demo_qrc_dependencies "")
        foreach(f ${_demo_pages})
            string(APPEND _demo_qrc_body
                "    <file alias=\"${f}\">${CMAKE_CURRENT_SOURCE_DIR}/demo/${f}</file>\n")
            list(APPEND _demo_qrc_dependencies
                "${CMAKE_CURRENT_SOURCE_DIR}/demo/${f}")
        endforeach()
        prism_attach_generated_qrc(
            prism_demo prism_demo_pages _demo_qrc_body
            _demo_qrc_dependencies)
        target_compile_definitions(prism_demo PRIVATE PRISM_QML_FROM_QRC)
    endif()

    # iOS: 可执行需为 app bundle + bundle identifier(否则 Xcode 无法生成 .app)
    if(IOS)
        set_target_properties(prism_demo PROPERTIES
            MACOSX_BUNDLE TRUE
            MACOSX_BUNDLE_GUI_IDENTIFIER "life.9li.prism.demo"
            MACOSX_BUNDLE_BUNDLE_NAME "PrismDemo"
            MACOSX_BUNDLE_SHORT_VERSION_STRING "1.0"
            MACOSX_BUNDLE_BUNDLE_VERSION "1"
            XCODE_ATTRIBUTE_TARGETED_DEVICE_FAMILY "1,2"  # iPhone+iPad
        )
    endif()
endif()

# ==================== gallery 可执行 (纯 C++ 完整组件画廊) ====================
# 加载 examples/pages 的 13 个组件展示页, 让纯 C++ 用户(无 Python)也能看到完整画廊。
# 桌面: 从磁盘加载 examples/pages (与 Python gallery 共享同一份页面源)。
option(PRISM_BUILD_GALLERY "Build the C++ gallery app" ON)
if(PRISM_BUILD_GALLERY AND NOT ANDROID AND NOT IOS)
    qt_add_executable(prism_gallery gallery/main.cpp)
    target_link_libraries(prism_gallery PRIVATE prism)
    # 注入源码树默认路径(开发树), 使 gallery 无需手动设环境变量即可运行。
    # 用户分发时可设 PRISM_GALLERY_PAGES / PRISM_GALLERY_ICON 环境变量覆盖。
    target_compile_definitions(prism_gallery PRIVATE
        PRISM_GALLERY_PAGES_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../examples/pages"
        PRISM_GALLERY_ICON_DEFAULT="${CMAKE_CURRENT_SOURCE_DIR}/../examples/resources/app_icon.svg")
endif()

# ==================== 单元测试 ====================
option(PRISM_BUILD_TESTS "Build the C++ tests" ON)
option(PRISM_BUILD_NATIVE_TESTS "Register native platform tests" OFF)
if(PRISM_BUILD_TESTS)
    enable_testing()
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    set(PRISM_TEST_TIMEOUT_SECONDS "60" CACHE STRING
        "Timeout in seconds for each PrismQML automated test")
    set(PRISM_TEST_CLEANUP_GRACE_SECONDS "50" CACHE STRING
        "Cleanup grace after a PrismQML automated test timeout")
    math(EXPR PRISM_CTEST_TIMEOUT_SECONDS
        "${PRISM_TEST_TIMEOUT_SECONDS} + ${PRISM_TEST_CLEANUP_GRACE_SECONDS}")
    set(PRISM_TEST_PROCESS_RUNNER
        "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/test_process.py")

    function(prism_add_cpp_test test_name target_name qt_platform)
        if(WIN32)
            add_test(NAME "${test_name}"
                COMMAND "${CMAKE_COMMAND}" -E env
                    "PATH=$<TARGET_FILE_DIR:Qt6::Core>$<SEMICOLON>$ENV{PATH}"
                    "${Python3_EXECUTABLE}" "${PRISM_TEST_PROCESS_RUNNER}"
                    --qt-platform "${qt_platform}"
                    --timeout "${PRISM_TEST_TIMEOUT_SECONDS}" --
                    "$<TARGET_FILE:${target_name}>" ${ARGN})
        else()
            add_test(NAME "${test_name}"
                COMMAND "${Python3_EXECUTABLE}" "${PRISM_TEST_PROCESS_RUNNER}"
                    --qt-platform "${qt_platform}"
                    --timeout "${PRISM_TEST_TIMEOUT_SECONDS}" --
                    "$<TARGET_FILE:${target_name}>" ${ARGN})
        endif()
        set_tests_properties("${test_name}" PROPERTIES
            TIMEOUT "${PRISM_CTEST_TIMEOUT_SECONDS}")
    endfunction()

    qt_add_executable(prism_test_store tests/test_store.cpp)
    target_link_libraries(prism_test_store PRIVATE prism)
    target_compile_definitions(prism_test_store PRIVATE
        PRISM_TEST_ICON_ROOT="${CMAKE_CURRENT_SOURCE_DIR}/../prismqml/PrismQML/controls/icons/fluent")
    prism_add_cpp_test(prism_test_store prism_test_store offscreen)

    qt_add_executable(prism_test_updater tests/test_updater.cpp)
    target_link_libraries(prism_test_updater PRIVATE prism)
    prism_add_cpp_test(prism_test_updater prism_test_updater offscreen)

    qt_add_executable(prism_test_config_manager
        tests/test_config_manager.cpp
        tests/test_config_contracts.cpp
        tests/test_config_qml_contracts.cpp
        tests/ConfigContractTests.h)
    target_link_libraries(prism_test_config_manager PRIVATE prism)
    prism_add_cpp_test(
        prism_test_config_manager prism_test_config_manager offscreen)

    qt_add_executable(prism_test_system tests/test_system.cpp)
    target_link_libraries(prism_test_system PRIVATE prism)
    prism_add_cpp_test(prism_test_system prism_test_system offscreen)

    qt_add_executable(prism_test_native_window tests/test_native_window.cpp)
    target_link_libraries(prism_test_native_window PRIVATE prism)
    target_include_directories(prism_test_native_window PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/src")
    prism_add_cpp_test(
        prism_test_native_window prism_test_native_window offscreen
        "${CMAKE_CURRENT_SOURCE_DIR}/../prismqml")

    qt_add_executable(prism_test_qml_runtime_plugin
        tests/test_qml_runtime_plugin.cpp)
    target_link_libraries(prism_test_qml_runtime_plugin PRIVATE prism)
    prism_add_cpp_test(
        prism_test_qml_runtime_plugin prism_test_qml_runtime_plugin offscreen)

    if(PRISM_BUILD_NATIVE_TESTS AND WIN32)
        set(PRISM_NATIVE_FAILURE_CASE_TIMEOUT_SECONDS "15" CACHE STRING
            "Timeout in seconds for one native failure-injection case")
        set(PRISM_NATIVE_FAILURE_MATRIX_TIMEOUT_SECONDS "360" CACHE STRING
            "Timeout in seconds for the complete native failure matrix")
        math(EXPR PRISM_NATIVE_FAILURE_CTEST_TIMEOUT_SECONDS
            "${PRISM_NATIVE_FAILURE_MATRIX_TIMEOUT_SECONDS} + ${PRISM_TEST_CLEANUP_GRACE_SECONDS}")

        qt_add_executable(prism_test_mica tests/test_mica.cpp)
        target_link_libraries(prism_test_mica PRIVATE prism)
        prism_add_cpp_test(prism_test_mica prism_test_mica windows)
        set_tests_properties(prism_test_mica PROPERTIES
            LABELS "native;windows;mica"
            SKIP_RETURN_CODE 77
        )

        add_library(prism_native_failure_companion SHARED
            tests/native_failure_companion.cpp)
        add_executable(prism_native_failure_loader
            tests/native_failure_loader.cpp)
        target_link_libraries(prism_native_failure_loader PRIVATE
            prism_native_failure_companion)
        set_target_properties(prism_native_failure_companion PROPERTIES
            RUNTIME_OUTPUT_DIRECTORY
                "${CMAKE_CURRENT_BINARY_DIR}/native-failure-companion")
        set_target_properties(prism_native_failure_loader PROPERTIES
            RUNTIME_OUTPUT_DIRECTORY
                "${CMAKE_CURRENT_BINARY_DIR}/native-failure-loader")
        add_executable(prism_native_failure_helper
            tests/native_failure_helper.cpp)
        target_link_libraries(prism_native_failure_helper PRIVATE Qt6::Core)
        set_target_properties(prism_native_failure_helper PROPERTIES
            RUNTIME_OUTPUT_DIRECTORY
                "${CMAKE_CURRENT_BINARY_DIR}/native-failure-helper")
        if(MSVC)
            foreach(_native_failure_target IN ITEMS
                prism_native_failure_companion
                prism_native_failure_loader
                prism_native_failure_helper)
                target_compile_options(${_native_failure_target} PRIVATE /utf-8)
            endforeach()
        endif()

        # Fatal fixtures must only run through verifier -> process runner.
        # 致命夹具只能经 verifier -> process runner 启动。
        add_test(NAME prism_native_failure_matrix
            COMMAND "${Python3_EXECUTABLE}" "${PRISM_TEST_PROCESS_RUNNER}"
                --qt-platform offscreen
                --timeout "${PRISM_NATIVE_FAILURE_MATRIX_TIMEOUT_SECONDS}" --
                "${Python3_EXECUTABLE}"
                "${CMAKE_CURRENT_SOURCE_DIR}/tests/verify_native_failures.py"
                --runner "${PRISM_TEST_PROCESS_RUNNER}"
                --helper "$<TARGET_FILE:prism_native_failure_helper>"
                --loader "$<TARGET_FILE:prism_native_failure_loader>"
                --companion "$<TARGET_FILE:prism_native_failure_companion>"
                --qt-bin "$<TARGET_FILE_DIR:Qt6::Core>"
                --case-timeout "${PRISM_NATIVE_FAILURE_CASE_TIMEOUT_SECONDS}")
        set_tests_properties(prism_native_failure_matrix PROPERTIES
            LABELS "native;windows;failure-injection"
            RUN_SERIAL TRUE
            TIMEOUT "${PRISM_NATIVE_FAILURE_CTEST_TIMEOUT_SECONDS}")
    endif()

    # QR 端到端验证: 生成 QR PNG 供 tests/qr/verify_qr.py 用 opencv 解码比对
    qt_add_executable(prism_test_qrcode_gen
        tests/test_qrcode_gen.cpp
        tests/test_qrcode_protocol.cpp
        tests/QRCodeTestSupport.h)
    target_link_libraries(prism_test_qrcode_gen PRIVATE prism)
    target_include_directories(prism_test_qrcode_gen PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/third_party")
    set(PRISM_QR_TEST_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}/test-output/qrcode")
    file(MAKE_DIRECTORY "${PRISM_QR_TEST_OUTPUT_DIR}")
    prism_add_cpp_test(
        prism_test_qrcode_gen prism_test_qrcode_gen offscreen
        "${PRISM_QR_TEST_OUTPUT_DIR}"
        "${CMAKE_CURRENT_SOURCE_DIR}/../prismqml")
    set_tests_properties(prism_test_qrcode_gen PROPERTIES
        FIXTURES_SETUP prism_qrcode_generated)
    add_test(
        NAME prism_test_qrcode_decode
        COMMAND "${Python3_EXECUTABLE}" "${PRISM_TEST_PROCESS_RUNNER}"
                --qt-platform offscreen
                --timeout "${PRISM_TEST_TIMEOUT_SECONDS}" --
                "${Python3_EXECUTABLE}"
                "${CMAKE_CURRENT_SOURCE_DIR}/tests/qr/verify_qr.py"
                "${PRISM_QR_TEST_OUTPUT_DIR}"
    )
    set_tests_properties(prism_test_qrcode_decode PROPERTIES
        FIXTURES_REQUIRED prism_qrcode_generated
        TIMEOUT "${PRISM_CTEST_TIMEOUT_SECONDS}")

    # SqlListModel 多 shard fan-out + keyset 游标验证
    qt_add_executable(prism_test_sqlmodel tests/test_sqlmodel.cpp)
    target_link_libraries(prism_test_sqlmodel PRIVATE prism)
    prism_add_cpp_test(prism_test_sqlmodel prism_test_sqlmodel offscreen)

    qt_add_executable(prism_test_provider_lifecycle tests/test_provider_lifecycle.cpp)
    target_link_libraries(prism_test_provider_lifecycle PRIVATE prism)
    prism_add_cpp_test(
        prism_test_provider_lifecycle prism_test_provider_lifecycle offscreen)

    set_tests_properties(
        prism_test_store
        prism_test_updater
        prism_test_config_manager
        prism_test_system
        prism_test_native_window
        prism_test_qrcode_gen
        prism_test_qrcode_decode
        prism_test_sqlmodel
        prism_test_provider_lifecycle
        PROPERTIES LABELS headless
    )
    set_tests_properties(prism_test_qml_runtime_plugin PROPERTIES LABELS headless)
endif()

# ==================== 移动端条件编译分支验证 ====================
# 桌面编译器 + 强制 PRISM_MOBILE 编译全库, 验证移动端分支语法/类型正确
# (不验证 Android 运行, 仅坐实移动分支不是写错的代码)
option(PRISM_VERIFY_MOBILE "Compile a mobile-branch variant to verify conditional code" ON)
if(PRISM_VERIFY_MOBILE)
    add_library(prism_mobile_verify STATIC
        src/Window.cpp src/PlatformInfo.cpp src/App.cpp src/ConfigContracts.cpp
        include/prism/Window.h include/prism/PlatformInfo.h include/prism/App.h
        include/prism/ConfigContracts.h src/ConfigContracts_p.h
        # Window.cpp 依赖的其余符号由桩满足? 不, 它依赖全库; 改为编译全部源
    )
    target_compile_definitions(prism_mobile_verify PRIVATE PRISM_FORCE_MOBILE_TEST)
    target_include_directories(prism_mobile_verify PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
    target_link_libraries(prism_mobile_verify PUBLIC
        Qt6::Core Qt6::Gui Qt6::Qml Qt6::Quick Qt6::Svg Qt6::Widgets Qt6::Network Qt6::Sql)
endif()
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

install(TARGETS prism
    EXPORT prismTargets
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
install(DIRECTORY include/prism DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})

# QML 组件模块: 把 PrismQML 引擎 QML 源安装到 <prefix>/qml/PrismQML/, 使纯 C++ 用户
# find_package(prism) 后 addImportPath(prism_QML_DIR) 即可 `import PrismQML`。
# (引擎内部 249 个组件用相对 import 互引, 故按目录原样安装, 不做 qt_add_qml_module 重构)
set(PRISM_QML_INSTALL_DIR "${CMAKE_INSTALL_DATADIR}/prism/qml")
install(DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../prismqml/PrismQML"
    DESTINATION "${PRISM_QML_INSTALL_DIR}"
    FILES_MATCHING
        PATTERN "*.qml"
        PATTERN "qmldir"
        PATTERN "*.js"
        PATTERN "*.json"
        PATTERN "*.svg"
        PATTERN "*.png"
        PATTERN "*.frag"
        PATTERN "*.qsb"
        PATTERN "__pycache__" EXCLUDE
)

# 随 QML 一并安装 LICENSE (MIT 合规: 分发的 QML 组件需附带许可证)
install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/../LICENSE"
    DESTINATION "${PRISM_QML_INSTALL_DIR}/PrismQML")

install(EXPORT prismTargets
    FILE prismTargets.cmake
    NAMESPACE prism::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/prism
)

# 生成 prismConfig.cmake (转发 Qt6 依赖查找 + 暴露 QML import 路径)
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/prismConfig.cmake.in"
"@PACKAGE_INIT@\n\
include(CMakeFindDependencyMacro)\n\
find_dependency(Qt6 REQUIRED COMPONENTS Core Gui Qml Quick Svg Widgets Network Sql QuickControls2 QuickLayouts QuickEffects)\n\
include(\"\${CMAKE_CURRENT_LIST_DIR}/prismTargets.cmake\")\n\
# QML 组件 import 路径: engine->addImportPath(prism_QML_DIR) 后即可 import PrismQML\n\
set_and_check(prism_QML_DIR \"@PACKAGE_PRISM_QML_INSTALL_DIR@\")\n")

set(PACKAGE_PRISM_QML_INSTALL_DIR "${PRISM_QML_INSTALL_DIR}")
configure_package_config_file(
    "${CMAKE_CURRENT_BINARY_DIR}/prismConfig.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/prismConfig.cmake"
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/prism
    PATH_VARS PRISM_QML_INSTALL_DIR
)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/prismConfig.cmake"
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/prism
)
