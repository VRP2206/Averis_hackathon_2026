# SDOC dashboard (web + Android)

React 19 + Vite + Tailwind v4 + shadcn/ui components (installed from the shadcn and 21st.dev registries). The same build ships as a static website and, through Capacitor, as an Android app.

## Run against the local API

```bash
# terminal 1, repo root
.venv\Scripts\activate && sdoc serve

# terminal 2
cd web
npm install
npm run dev            # http://localhost:5173  (API at http://127.0.0.1:8000 by default)
```

Set the API base URL with `VITE_API_URL` (see `.env.example`). Click **Process inbox** once to populate results.

## Build the website

```bash
VITE_API_URL=https://<your-api> npm run build     # -> dist/
```

`dist/` is static: upload to Amplify Hosting, Netlify, Vercel or S3. Routing uses hash URLs so no server rewrite rules are needed.

## Build the Android app

Requirements: Android Studio (for its SDK and bundled JDK 17).

```bash
set JAVA_HOME=C:\Program Files\Android\Android Studio\jbr
set ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk
set VITE_API_URL=http://10.0.2.2:8000        # emulator to host machine; use your HTTPS URL for a real phone
npm run build && npx cap sync android
cd android && gradlew assembleDebug
# APK: android/app/build/outputs/apk/debug/app-debug.apk
```

Or open `android/` in Android Studio and press Run. For a phone, install the APK by side-loading (Settings → allow unknown sources).

## Screens

- **Inbox** (`#/`): triaged list, filters, KPI strip, "Process inbox".
- **Compare** (`#/emails/:id`): email body, SI vs BL field table with mismatch/missing highlighting, source-line tooltips, approve / override (with consent), drafted reply.
- **Invoices** (`#/invoices`): billing emails with invoice numbers, order refs and amounts pulled from the text, with evidence tooltips.
- **Impact** (`#/impact`): live operations counts and accuracy vs the answer key from `/metrics`.
- Legal: `#/privacy`, `#/terms`, `#/cookies`, `#/accessibility`. See `../docs/COMPLIANCE.md`.

## Before submitting

Fill `src/content/business.ts` (team name, members, contact email).
