@echo off
setlocal

call "%~dp0build_env.bat" require-file PRISM_VCVARS64
if errorlevel 1 exit /b 10
call "%~dp0build_env.bat" require-dir QT_HOST_PATH
if errorlevel 1 exit /b 10

if not defined PRISM_CMAKE_COMMAND set "PRISM_CMAKE_COMMAND=cmake"
if not defined PRISM_DESKTOP_BUILD_DIR set "PRISM_DESKTOP_BUILD_DIR=%~dp0build"

call "%PRISM_VCVARS64%"
if errorlevel 1 (echo VCVARS_FAIL & exit /b 10)

set "PATH=%QT_HOST_PATH%\bin;%PATH%"
pushd "%~dp0"
if errorlevel 1 (echo CPP_DIR_FAIL & exit /b 10)

call "%PRISM_CMAKE_COMMAND%" -S . -B "%PRISM_DESKTOP_BUILD_DIR%" -G "NMake Makefiles" ^
  -DCMAKE_BUILD_TYPE=Release ^
  "-DCMAKE_PREFIX_PATH=%QT_HOST_PATH%" ^
  "-DQt6_DIR=%QT_HOST_PATH%\lib\cmake\Qt6"
if errorlevel 1 (popd & echo CMAKE_CONFIG_FAIL & exit /b 11)

call "%PRISM_CMAKE_COMMAND%" --build "%PRISM_DESKTOP_BUILD_DIR%"
if errorlevel 1 (popd & echo BUILD_FAIL & exit /b 12)

popd
echo PRISM_BUILD_DONE
exit /b 0
