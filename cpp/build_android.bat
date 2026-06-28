@echo off
REM Android 构建: qt-cmake(Qt android) + SDK/NDK/JDK
set "JAVA_HOME=D:\Qt\_tools\jdk17_extract\jdk-17.0.19+10"
set "ANDROID_SDK_ROOT=D:\Qt\_tools\android-sdk"
set "ANDROID_NDK_ROOT=D:\Qt\_tools\android-sdk\ndk\27.2.12479018"
set "PATH=%JAVA_HOME%\bin;%PATH%"
set "NINJA=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"
set "CMAKEBIN=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
set "PATH=%CMAKEBIN%;%PATH%"
set "QTCMAKE=D:\Qt\6.10.3\android_arm64_v8a\bin\qt-cmake.bat"

cd /d D:\PrismQML\PrismQML\cpp

call "%QTCMAKE%" -S . -B build-android -G Ninja ^
  -DCMAKE_MAKE_PROGRAM="%NINJA%" ^
  -DCMAKE_BUILD_TYPE=Release ^
  -DQT_HOST_PATH=D:\Qt\6.10.3\msvc2022_64 ^
  -DANDROID_SDK_ROOT=%ANDROID_SDK_ROOT% ^
  -DANDROID_NDK_ROOT=%ANDROID_NDK_ROOT% ^
  -DQT_ANDROID_ABIS=arm64-v8a ^
  -DPRISM_BUILD_TESTS=OFF ^
  -DPRISM_VERIFY_MOBILE=OFF
if errorlevel 1 (echo ANDROID_CONFIG_FAIL & exit /b 11)

call "%NINJA%" -C build-android prism
if errorlevel 1 (echo ANDROID_BUILD_FAIL & exit /b 12)
echo ANDROID_PRISM_BUILD_OK
