@echo off
setlocal
pushd "%~dp0" || exit /b 1
set "scenario=%~1"
if not defined scenario set "scenario=High"
set "seed=%~2"
if not defined seed set "seed=42"
if /I "%scenario%"=="all" exit /b 1
python -B generate_demand.py --scenario "%scenario%" --seed "%seed%"
if errorlevel 1 exit /b 1
sumo-gui -c "scenarios/%scenario%/simulation.sumocfg" --start
set "result=%errorlevel%"
popd
exit /b %result%
