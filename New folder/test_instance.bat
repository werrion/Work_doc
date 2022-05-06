setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

set SCENARIO_FILE=%1
set RESULT_FILE=%2

if "%SCENARIO_FILE%"=="" ( 
	echo "This is internal use file"
	exit -1
)

echo =====Start Instance=====>"%RESULT_FILE%"
echo Scenario:%SCENARIO_FILE%>>"%RESULT_FILE%"

powershell ".\ABUtility.exe file %SCENARIO_FILE% | tee -Append -FilePath result.log"
powershell -c "Get-Content result.log | Add-Content -Encoding utf8 '%RESULT_FILE%'"

echo =====Finished instance=====>>"%RESULT_FILE%"