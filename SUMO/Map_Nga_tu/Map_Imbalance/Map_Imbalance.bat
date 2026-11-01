@echo off
setlocal
pushd "%~dp0" || exit /b 1
sumo-gui -c simulation.sumocfg --start
set "result=%errorlevel%"
if not "%result%"=="0" pause
popd
exit /b %result%
