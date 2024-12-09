@echo off
:: Cambiar al directorio principal (donde está app.py de FastAPI)
cd /d %~dp0

:: Iniciar FastAPI desde el directorio actual
start cmd /k "uvicorn main:app --reload"

:: Cambiar al subdirectorio de Streamlit
cd facturador

:: Iniciar Streamlit desde el subdirectorio
start cmd /k "streamlit run main.py"

:: Mensaje de confirmación
echo "FastAPI y Streamlit están en ejecución."
pause

