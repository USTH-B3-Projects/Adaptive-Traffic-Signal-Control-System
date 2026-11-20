@echo off
setlocal
pushd "%~dp0" || exit /b 1
set "scenario=%~1"
if "%scenario%"=="" set "scenario=Low"
if not exist "scenarios\%scenario%\simulation.sumocfg" (
 echo Unknown scenario. Use Low, Medium, High or Imbalance.
 popd
 exit /b 1
)
call "scenarios\%scenario%\%scenario%.bat"
set "result=%errorlevel%"
popd
exit /b %result%
