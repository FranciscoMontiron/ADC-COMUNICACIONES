# Simulador de Conversion de Senales (ADC)

Este proyecto es un simulador interactivo de conversion analogico-digital (ADC) hecho en Python usando Streamlit. Permite ver como se muestrea y cuantiza una senal analogica, y como afecta el aliasing y el filtro antialias.

## Como levantar el proyecto en local (Windows, PowerShell)

1. Clona o descarga este repo y entra a la carpeta
2. (Importante) Si tenias un archivo llamado `signal.py`, renombralo a `adc_signal.py` para evitar conflictos con la libreria estandar de Python.
3. Crea el entorno virtual:
   ```powershell
   python -m venv venv
   ```
4. Activa el entorno virtual:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\venv\Scripts\Activate.ps1
   ```
5. Instala las dependencias:
   ```powershell
   pip install -r requirements.txt
   ```
6. Levanta la app:
   ```powershell
   streamlit run app.py
   ```
7. Abri el navegador en la URL que te tira Streamlit (por defecto http://localhost:8501)

---

## Produccion (app online)

No hace falta instalar nada, simplemente entra a:

👉 [https://franciscomontiron-adc-comunicaciones-app-dev-do4mg4.streamlit.app/](https://franciscomontiron-adc-comunicaciones-app-dev-do4mg4.streamlit.app/)

La app funciona directo desde el navegador.


