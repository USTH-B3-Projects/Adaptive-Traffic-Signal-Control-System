@echo off
setlocal
pushd "%~dp0" || exit /b 1
if not exist "..\..\output\Imbalance\seed42" mkdir "..\..\output\Imbalance\seed42"
sumo-gui -c simulation.sumocfg --start
set "result=%errorlevel%"
if not "%result%"=="0" pause
popd
exit /b %result%
