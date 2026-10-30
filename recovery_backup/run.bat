@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "BACKEND_URL=http://127.0.0.1:8000"
set "FRONTEND_URL=http://127.0.0.1:3000"

echo ============================================================
echo SatQuery Medium - Verify and Start
echo ============================================================

if not exist ".venv\Scripts\python.exe" (
  echo [FAIL] Missing .venv\Scripts\python.exe
  echo Create it with: py -3.11 -m venv .venv
  pause
  exit /b 1
)
if not exist "frontend\node_modules\next" (
  echo [FAIL] Frontend dependencies are missing.
  echo Run: cd frontend ^&^& npm install
  pause
  exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
  echo [FAIL] npm was not found. Install Node.js and retry.
  pause
  exit /b 1
)

echo.
echo [1/3] Running backend unit tests...
.venv\Scripts\python.exe -m unittest discover -s tests -v
if errorlevel 1 goto :failed

echo [2/3] Compiling backend modules...
.venv\Scripts\python.exe -m compileall -q backend gis inference
if errorlevel 1 goto :failed

echo [3/3] Checking FastAPI import...
.venv\Scripts\python.exe -c "from backend.app import app; print('FastAPI import: PASS')"
if errorlevel 1 goto :failed

echo.
echo Starting backend at %BACKEND_URL% ...
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri '%BACKEND_URL%/health' -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  start "SatQuery Backend" /D "%~dp0" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000"
)

powershell -NoProfile -Command "$ok=$false; for($i=0;$i -lt 30;$i++){ try { Invoke-RestMethod -Uri '%BACKEND_URL%/health' -TimeoutSec 2 | Out-Null; $ok=$true; break } catch { Start-Sleep -Seconds 1 } }; if(-not $ok){ exit 1 }"
if errorlevel 1 (
  echo [FAIL] Backend did not become healthy at %BACKEND_URL%.
  echo Check the "SatQuery Backend" window for the error.
  pause
  exit /b 1
)

echo Starting frontend at %FRONTEND_URL% ...
set "NEXT_PUBLIC_BACKEND_URL=%BACKEND_URL%"
rem Do not launch another Next.js instance when the port is already occupied.
powershell -NoProfile -Command "$c=New-Object Net.Sockets.TcpClient; try { $a=$c.BeginConnect('127.0.0.1',3000,$null,$null); if($a.AsyncWaitHandle.WaitOne(500) -and $c.Connected){exit 0}; exit 1 } catch { exit 1 } finally { $c.Close() }"
if errorlevel 1 (
  start "SatQuery Frontend" /D "%~dp0frontend" cmd /k "npm.cmd run dev -- --hostname 127.0.0.1 --port 3000"
)

echo.
echo ============================================================
echo Backend:  %BACKEND_URL%
echo API docs: %BACKEND_URL%/docs
echo Dashboard: %FRONTEND_URL%
echo ============================================================
echo The dashboard will be opened when Next.js is ready.

powershell -NoProfile -Command "$ok=$false; $status=0; for($i=0;$i -lt 60;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing -Uri '%FRONTEND_URL%' -TimeoutSec 2; $status=[int]$r.StatusCode; if($status -eq 200){$ok=$true;break} } catch { if($_.Exception.Response){$status=[int]$_.Exception.Response.StatusCode} }; Start-Sleep -Seconds 1 }; if($ok){Start-Process '%FRONTEND_URL%';exit 0}; if($status -ne 0){Write-Output ('Frontend returned HTTP '+$status)};exit 1"
if errorlevel 1 (
  echo [FAIL] Frontend did not become ready at %FRONTEND_URL%.
  echo Check the "SatQuery Frontend" window for the error.
  exit /b 1
)
exit /b 0

:failed
echo [FAIL] Verification failed; services were not started.
pause
exit /b 1
