@echo off
setlocal
REM Android x86_64 APK build for emulator Android x86_64 模拟器 APK 构建

call "%~dp0build_env.bat" require-dir JAVA_HOME
if errorlevel 1 exit /b 10
call "%~dp0build_env.bat" require-dir ANDROID_SDK_ROOT
if errorlevel 1 exit /b 10
call "%~dp0build_env.bat" require-dir ANDROID_NDK_ROOT
if errorlevel 1 exit /b 10
call "%~dp0build_env.bat" require-dir QT_HOST_PATH
if errorlevel 1 exit /b 10
call "%~dp0build_env.bat" require-file QT_ANDROID_CMAKE
if errorlevel 1 exit /b 10
call "%~dp0build_env.bat" require-file NINJA
if errorlevel 1 exit /b 10

if not defined PRISM_ARTIFACT_ROOT set "PRISM_ARTIFACT_ROOT=%~dp0..\.artifacts"
if not defined PRISM_ANDROID_BUILD_DIR set "PRISM_ANDROID_BUILD_DIR=%PRISM_ARTIFACT_ROOT%\cpp\android-x64"
for %%I in ("%NINJA%") do set "PATH=%%~dpI;%JAVA_HOME%\bin;%PATH%"
pushd "%~dp0"
if errorlevel 1 (echo CPP_DIR_FAIL & exit /b 10)

call "%QT_ANDROID_CMAKE%" -S . -B "%PRISM_ANDROID_BUILD_DIR%" -G Ninja ^
  -DCMAKE_BUILD_TYPE=Release ^
  "-DQT_HOST_PATH=%QT_HOST_PATH%" ^
  "-DANDROID_SDK_ROOT=%ANDROID_SDK_ROOT%" ^
  "-DANDROID_NDK_ROOT=%ANDROID_NDK_ROOT%" ^
  -DQT_ANDROID_ABIS=x86_64 ^
  -DPRISM_BUILD_TESTS=OFF ^
  -DPRISM_VERIFY_MOBILE=OFF
if errorlevel 1 (popd & echo X64_CONFIG_FAIL & exit /b 11)

call "%NINJA%" -C "%PRISM_ANDROID_BUILD_DIR%" prism_demo_make_apk
if errorlevel 1 (popd & echo X64_APK_BUILD_FAIL & exit /b 12)

popd
echo X64_APK_BUILD_OK
exit /b 0
