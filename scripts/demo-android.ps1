# Start the SDOC API, boot an Android emulator, install the prebuilt APK and launch it.
# Run from the repo root:  .\scripts\demo-android.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$sdk = Join-Path $env:LOCALAPPDATA "Android\Sdk"
$emu = Join-Path $sdk "emulator\emulator.exe"
$adb = Join-Path $sdk "platform-tools\adb.exe"
$apk = Join-Path $root "apk\sdoc-debug.apk"

if (-not (Test-Path (Join-Path $root ".venv\Scripts\python.exe"))) { throw "Create the venv first: py -3.12 -m venv .venv; .venv\Scripts\activate; pip install -e .[dev]" }
if (-not (Test-Path $emu)) { throw "Android SDK not found at $sdk. Install Android Studio and create a virtual device." }
if (-not (Test-Path $apk)) { throw "APK missing at $apk. See docs\DEMO-ANDROID.md to rebuild it." }

Write-Host "Starting API on http://0.0.0.0:8000 ..."
Start-Process -FilePath (Join-Path $root ".venv\Scripts\python.exe") -ArgumentList "-m","uvicorn","sdoc.api:app","--host","0.0.0.0","--port","8000" -WorkingDirectory $root -WindowStyle Minimized
Start-Sleep -Seconds 5
try { Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/process" | Out-Null; Write-Host "Inbox processed." } catch { Write-Warning "API not ready yet; press Process inbox in the app." }

$avd = (& $emu -list-avds | Select-Object -First 1)
if (-not $avd) { throw "No virtual device. In Android Studio: Virtual Device Manager -> Create device." }
Write-Host "Booting emulator $avd ..."
Start-Process -FilePath $emu -ArgumentList "-avd",$avd -WindowStyle Normal
& $adb wait-for-device | Out-Null
do { Start-Sleep -Seconds 4; $booted = (& $adb shell getprop sys.boot_completed 2>$null).Trim() } while ($booted -ne "1")
Write-Host "Installing app ..."
& $adb install -r $apk | Out-Null
& $adb shell am start -n com.sdoc.app/.MainActivity | Out-Null
Write-Host ""
Write-Host "Done. If the inbox is empty: gear icon -> API base URL -> http://10.0.2.2:8000 -> Save and reload."
Write-Host "Website: http://localhost:5173 (cd web; npm run dev)   API docs: http://127.0.0.1:8000/docs"
