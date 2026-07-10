@echo off
setlocal EnableExtensions EnableDelayedExpansion

if /i "%~1"=="require-dir" goto require_dir
if /i "%~1"=="require-file" goto require_file
echo BUILD_ENV_UNKNOWN_CHECK=%~1
exit /b 2

:require_dir
if "%~2"=="" exit /b 2
for %%V in (%~2) do set "REQUIRED_VALUE=!%%V!"
if not defined REQUIRED_VALUE (
  echo MISSING_ENV_%~2
  exit /b 1
)
if not exist "!REQUIRED_VALUE!\." (
  echo INVALID_DIR_%~2=!REQUIRED_VALUE!
  exit /b 1
)
exit /b 0

:require_file
if "%~2"=="" exit /b 2
for %%V in (%~2) do set "REQUIRED_VALUE=!%%V!"
if not defined REQUIRED_VALUE (
  echo MISSING_ENV_%~2
  exit /b 1
)
if not exist "!REQUIRED_VALUE!" (
  echo INVALID_FILE_%~2=!REQUIRED_VALUE!
  exit /b 1
)
exit /b 0
