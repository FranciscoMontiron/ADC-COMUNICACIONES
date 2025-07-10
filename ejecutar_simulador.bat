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
echo    - Tutoriales interactivos paso a paso con casos de aliasing
echo ================================================================
echo.

echo Verificando dependencias...
python -c "import streamlit, numpy, plotly, sqlite3" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Faltan dependencias. Instalando...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: No se pudieron instalar las dependencias.
        echo Por favor ejecuta: pip install streamlit numpy plotly
        pause
        exit /b 1
    )
)

echo.
echo Iniciando el simulador...
echo Presiona Ctrl+C para detener el servidor
echo.
echo El simulador se abrira automaticamente en tu navegador
echo Si no se abre, ve a: http://localhost:8501
echo.

streamlit run apps\app_principal.py --server.port 8501 --server.headless false

echo Verificando dependencias...
pip install -q streamlit numpy plotly pandas

echo.
echo Iniciando simulador ADC consolidado...
echo Abrir en el navegador: http://localhost:8501
echo.
echo NOTA: La aplicacion esta completamente consolidada en un solo archivo
echo       - Sin warnings de Streamlit
echo       - Titulos de graficos perfectamente separados
echo       - Todas las funcionalidades integradas
echo.
echo Para detener el simulador, presiona Ctrl+C
echo.

streamlit run apps\app_principal.py
