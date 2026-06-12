@echo off
echo ================================
echo   Installing SKU System Dependencies
echo ================================
echo.

echo [1/3] Installing Flask API dependencies...
cd BackendCodes
pip install -r requirements_flask.txt
cd ..

echo.
echo [2/3] Installing FastAPI Backend dependencies...
cd agentSystem
pip install -r requirements.txt
cd ..

echo.
echo [3/3] Installing React Frontend dependencies...
cd C.O.R.E
call npm install
cd ..

echo.
echo ================================
echo   Installation Complete!
echo ================================
echo.
echo Next steps:
echo 1. Start Flask API:    cd BackendCodes ^&^& python sku_matching_api.py
echo 2. Start FastAPI:      cd agentSystem ^&^& uvicorn app:app --reload
echo 3. Start React:        cd C.O.R.E ^&^& npm start
echo.
pause
