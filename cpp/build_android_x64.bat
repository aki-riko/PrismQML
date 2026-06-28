@echo off
REM Android x86_64 构建(用于x86主机emulator真机运行验证)
set "JAVA_HOME=D:\Qt\_tools\jdk17_extract\jdk-17.0.19+10"
set "ANDROID_SDK_ROOT=D:\Qt\_tools\android-sdk"
set "ANDROID_NDK_ROOT=D:\Qt\_tools\android-sdk\ndk\27.2.12479018"
set "CMAKEBIN=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
set "PATH=%JAVA_HOME%\bin;%CMAKEBIN%;%PATH%"
set "NINJA=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"
set "QTCMAKE=D:\Qt\6.10.3\android_x86_64\bin\qt-cmake.bat"

cd /d D:\PrismQML\PrismQML\cpp

call "%QTCMAKE%" -S . -B build-android-x64 -G Ninja ^
  -DCMAKE_MAKE_PROGRAM="%NINJA%" ^
  -DCMAKE_BUILD_TYPE=Release ^
  -DQT_HOST_PATH=D:\Qt\6.10.3\msvc2022_64 ^
  -DANDROID_SDK_ROOT=%ANDROID_SDK_ROOT% ^
  -DANDROID_NDK_ROOT=%ANDROID_NDK_ROOT% ^
  -DQT_ANDROID_ABIS=x86_64 ^
  -DPRISM_BUILD_TESTS=OFF ^
  -DPRISM_VERIFY_MOBILE=OFF
if errorlevel 1 (echo X64_CONFIG_FAIL & exit /b 11)

"%NINJA%" -C build-android-x64 prism_demo_make_apk
echo X64_APK_EXIT=%errorlevel%
