# 📡 Simulador ADC - Digitalización de Señales

Simulador interactivo para entender el proceso de conversión analógico-digital con tutoriales paso a paso que demuestran conceptos como el Teorema de Nyquist y el aliasing.

## 🚀 Funcionalidades Principales

- **Generación de señales**: Sinusoidales, cuadradas, triangulares, diente de sierra
- **Muestreo configurable**: Desde 100 Hz hasta 200 kHz con presets estándar (8 kHz, 44.1 kHz, etc.)
- **Cuantización variable**: 8, 16, 24 y 32 bits con análisis de SNR
- **Visualización en tiempo real**: Gráficos interactivos con Plotly
- **Análisis espectral**: FFT y detección automática de aliasing
- **Tutoriales interactivos**: Casos paso a paso para aprender conceptos clave
- **Aplicación del Teorema de Nyquist**: Demostración visual de aliasing

## 📊 Tutoriales Incluidos

### 1. Señal Senoidal Básica
- Conceptos fundamentales de ADC
- Aplicación correcta del Teorema de Nyquist
- Proceso de muestreo y cuantización

### 2. Demostración de Aliasing
- **Caso Correcto**: f₀ < fs/2 (sin aliasing)
- **Caso Límite**: f₀ ≈ fs/2 (margen mínimo)
- **Violación Leve**: f₀ > fs/2 (aliasing moderado)
- **Violación Severa**: f₀ >> fs/2 (aliasing grave)
- **Caso Extremo**: f₀ ≈ fs (señal aparece como DC)
- **Solución**: Aumento de fs para corregir aliasing

### 3. Efectos de Cuantización
- Comparación entre diferentes resoluciones
- Análisis de ruido de cuantización
- Relación SNR vs. número de bits

## 🛠️ Instalación y Uso

### Opción 1: Ejecución Rápida
```bash
# Doble clic en el archivo
ejecutar_simulador.bat
```

### Opción 2: Manual
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar simulador
streamlit run apps/app_principal.py
```

## 📁 Estructura del Proyecto

```
ADC-COMUNICACIONES/
├── apps/
│   └── app_principal.py          # Aplicación principal consolidada
├── data/                         # Bases de datos de señales
├── scripts/                      # Scripts auxiliares
├── ejecutar_simulador.bat        # Ejecutor principal
├── requirements.txt              # Dependencias
└── README.md                     # Este archivo
```

## 📚 Conceptos Teóricos Implementados

### Teorema de Nyquist-Shannon
```
fs ≥ 2 × fmax
```
Condición necesaria para evitar aliasing en el muestreo.

### Aliasing
```
f_aparente = |f₀ - k × fs|
```
Frecuencia falsa que aparece cuando se viola Nyquist.

### SNR de Cuantización
```
SNR_dB = 6.02 × N + 1.76
```
Relación señal-ruido teórica según el número de bits.

## 🎯 Características Destacadas

- **Análisis automático de aliasing** con clasificación por severidad
- **Gráficos dinámicos** que cambian según los parámetros del tutorial
- **Métricas en tiempo real** de calidad de señal
- **Interfaz educativa** con explicaciones paso a paso
- **Casos predefinidos** para aprendizaje guiado

## 🔧 Dependencias

- Python 3.7+
- Streamlit
- NumPy
- Plotly
- SQLite3 (incluido con Python)

## 💡 Uso Educativo

Este simulador está diseñado para:
- Estudiantes de ingeniería en telecomunicaciones
- Cursos de procesamiento de señales digitales
- Comprensión práctica del Teorema de Nyquist
- Visualización de efectos de aliasing
- Análisis de sistemas ADC

## 🎮 Modos de Uso

### Modo Tutorial
Experiencia guiada paso a paso con casos predefinidos que demuestran conceptos específicos.

### Modo Libre
Experimentación libre con todos los parámetros configurables para exploración avanzada.

---

**Desarrollado para demostrar de manera visual e interactiva los conceptos fundamentales de la conversión analógico-digital.**
