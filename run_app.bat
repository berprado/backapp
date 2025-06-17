@echo off
:: Cambiar al directorio principal (donde está api.py de FastAPI)
cd /d %~dp0

:: Iniciar FastAPI desde el directorio actual (usando api.py en lugar de main.py)
start cmd /k "uvicorn api:app --reload"

:: Cambiar al subdirectorio de Streamlit
cd facturador

:: Iniciar Streamlit desde el subdirectorio
start cmd /k "streamlit run main.py"

:: Mensaje de confirmación
echo "FastAPI y Streamlit están en ejecución."
pause

