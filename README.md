# Simulador de Conversion de Senales (ADC)

Este proyecto es un simulador interactivo de conversion analogico-digital (ADC) hecho en Python usando Streamlit. Permite ver como se muestrea y cuantiza una senal analogica, y como afecta el aliasing y el filtro antialias.

## Como levantar el proyecto (Windows, PowerShell)

1. **Clona o descarga este repo y entra a la carpeta**

2. **Crea el entorno virtual**

```powershell
python -m venv venv
```

3. **Activa el entorno virtual**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

4. **Instala las dependencias**

```powershell
pip install -r requirements.txt
```

5. **Levanta la app**

```powershell
streamlit run app.py
```

6. **Abri el navegador en la URL que te tira Streamlit (por defecto http://localhost:8501)**

---

## Proximos pasos y mejoras: TODO

- Mejorar los colores y el layout (se puede usar CSS o el tema de Streamlit)
- Agregar mas tipos de senal: suma de armonicos, ruido, moduladas, etc
- Hacer el filtro antialias mas avanzado (elegir orden y fc)
- Desplegar
