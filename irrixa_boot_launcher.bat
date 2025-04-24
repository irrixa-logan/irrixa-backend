@echo off
:: Irrixa All-in-One Launcher 🚀

cd /d "%~dp0"
echo Starting Irrixa weather fetcher...
python src\weather_fetcher.py

echo Starting Irrixa NDVI fetcher...
python src\ndvi_fetcher.py

:: Launch Flask Config Server
start cmd /k "cd /d %~dp0 && python src\irrixa_config_server.py"

:: Launch Irrixa Irrigation Engine
python src\irrigation_engine.py

:: Launch React Dashboard (must be inside dashboard folder)
echo Starting Irrixa dashboard (Vite)...
cd dashboard
start cmd /k "npm run dev"

:: Wait 3 seconds to allow Vite to start
timeout /t 3 /nobreak > NUL

:: Open default browser to dashboard
start http://localhost:5173

cd ..
echo ✅ Irrixa boot complete. All systems online.
 