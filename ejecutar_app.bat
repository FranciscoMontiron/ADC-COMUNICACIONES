@echo off
echo 📡 Simulador de Conversion de Senales (ADC)
echo ==========================================
echo.
echo Activando entorno virtual...
call .\venv\Scripts\activate.bat
echo.
echo Ejecutando aplicacion Streamlit...
echo Abre tu navegador en: http://localhost:8501
echo.
echo Para detener la aplicacion, presiona Ctrl+C
echo.
streamlit run app.py
pause

