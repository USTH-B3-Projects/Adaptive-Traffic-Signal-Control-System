@echo off
setlocal
pushd "%~dp0" || exit /b 1
python -B generate_demand.py %*
set "result=%errorlevel%"
popd
exit /b %result%
