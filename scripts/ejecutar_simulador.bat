@echo off
cls
echo ================================================================
echo             SIMULADOR ADC - DIGITALIZACION DE SEÑALES
echo ================================================================
echo  Simulador interactivo para entender la conversion analogico-digital
echo  
echo  Funcionalidades:
echo    - Generacion de señales analogicas (sinusoides, cuadradas, etc.)
echo    - Muestreo con diferentes tasas (8 kHz, 44.1 kHz, etc.)
echo    - Cuantizacion con distintos niveles (8, 16, 24 bits)
echo    - Visualizacion comparativa original vs. digitalizada
echo    - Aplicacion del Teorema de Nyquist y demostracion de aliasing
echo ================================================================
echo.

echo Activando entorno virtual...
call .\venv\Scripts\activate

echo Verificando dependencias...
pip install -q streamlit numpy plotly pandas

echo Inicializando base de datos...
python -c "import sys; sys.path.append('src'); from database import inicializarBaseDeDatos; inicializarBaseDeDatos(); print('Base de datos inicializada.')"

echo.
echo Iniciando simulador ADC...
echo Abrir en el navegador: http://localhost:8501
echo.
echo Para detener el simulador, presiona Ctrl+C
echo.

streamlit run apps\app_principal.py
