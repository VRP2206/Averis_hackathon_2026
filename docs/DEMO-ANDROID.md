# Showcasing the Android app from any laptop

Goal: in under 10 minutes, have the SDOC Android app running on an emulator (or a phone) on *your* laptop, talking to the API on the same laptop. No rebuild needed: the app has a Settings (gear) dialog where you type the API address.

## Why it "didn't work" before

The app is a thin shell around the web dashboard; **it shows nothing unless the API is reachable**. Two things must be true:

1. `sdoc serve` is running on the laptop.
2. The app points at the right address: `http://10.0.2.2:8000` from the Android emulator (that IP means "the host laptop"), or `http://<laptop-LAN-IP>:8000` from a real phone on the same Wi-Fi.

If you see an empty inbox or "Could not reach the API", it is always one of those two.

## One-time setup (15 min, once)

1. Install **Android Studio** (it brings the SDK, the emulator and a JDK). Open it once, go to *More Actions → Virtual Device Manager*, create any Pixel device with a recent system image, and start it once so it boots.
2. Clone the repo and set up Python:
   ```powershell
   git clone https://github.com/VRP2206/Averis_hackathon_2026.git
   cd Averis_hackathon_2026
   py -3.12 -m venv .venv
   .venv\Scripts\activate
   pip install -e ".[dev]"
   ```
3. That's it. The prebuilt APK is in `apk/sdoc-debug.apk`.

## Every demo (2 min)

Run the script from the repo root in PowerShell:

```powershell
.\scripts\demo-android.ps1
```

It starts the API (`sdoc serve --host 0.0.0.0`), processes the inbox once, starts the first emulator it finds, waits for boot, installs `apk/sdoc-debug.apk`, and launches the app. Leave the PowerShell window open.

Manual equivalent, if you prefer:

```powershell
.venv\Scripts\activate
sdoc serve --host 0.0.0.0                                  # window 1
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -list-avds
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd <NAME>   # window 2
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install -r apk\sdoc-debug.apk
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell am start -n com.sdoc.app/.MainActivity
```

In the app: if the inbox is empty, tap the **gear icon**, set the API base URL to `http://10.0.2.2:8000`, *Save and reload*, then tap **Process inbox** once.

## On a real phone (optional)

1. Laptop and phone on the same Wi-Fi. Find the laptop IP: `ipconfig` → IPv4 address, e.g. `192.168.1.20`.
2. Allow port 8000 through Windows Firewall the first time (Windows will prompt when `sdoc serve --host 0.0.0.0` starts; choose *Allow*).
3. Copy `apk/sdoc-debug.apk` to the phone (USB, Drive, WhatsApp to yourself) and open it; allow "install unknown apps".
4. In the app, gear icon → `http://192.168.1.20:8000` → Save and reload.

## What to show (60 seconds)

1. Inbox tiles: 520 emails, 46 mismatches, 20 needing review.
2. Tap a Mismatch row → the comparison with the two wrong fields highlighted.
3. Scroll to the drafted reply.
4. Tap a Needs-review row → the reason.
5. Say: "Same code as the website; ships as an APK through Capacitor."

## Rebuilding the APK (only if the web code changed)

```powershell
cd web
npm install
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
npm run build; npx cap sync android
cd android; .\gradlew assembleDebug
copy app\build\outputs\apk\debug\app-debug.apk ..\..\apk\sdoc-debug.apk
```
