"""
Simulador ADC - Conversión Analógico-Digital
============================================

Simulador interactivo para visualizar el proceso de conversión analógico-digital
consolidado en un solo archivo principal.

Funcionalidades principales:
- Generación de señales analógicas (sinusoides, cuadradas, etc.)
- Muestreo con diferentes tasas (8 kHz, 44.1 kHz, etc.)
- Cuantización con distintos niveles (8, 16, 24 bits)
- Visualización comparativa original vs. digitalizada
- Aplicación del Teorema de Nyquist y demostración de aliasing
- Sistema de tutoriales interactivos paso a paso (integrado)
"""

import streamlit as st
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import sqlite3
import time

# ===== FUNCIONES DE SEÑALES (CONSOLIDADAS) =====
def generar_señal(tipo, f0, amplitud, t, n_armonicos=3, snr_db=20):
    """Genera una señal analógica según el tipo especificado"""
    if tipo == "Senoidal":
        return amplitud * np.sin(2 * np.pi * f0 * t)
    elif tipo == "Cuadrada":
        return amplitud * np.sign(np.sin(2 * np.pi * f0 * t))
    elif tipo == "Triangular":
        return amplitud * 2 * np.arcsin(np.sin(2 * np.pi * f0 * t)) / np.pi
    elif tipo == "Diente de sierra":
        return amplitud * 2 * (t * f0 - np.floor(t * f0 + 0.5))
    elif tipo == "Suma de armonicos":
        signal = np.zeros_like(t)
        for n in range(1, n_armonicos + 1):
            signal += (amplitud / n) * np.sin(2 * np.pi * f0 * n * t)
        return signal
    elif tipo == "Señal con ruido":
        signal = amplitud * np.sin(2 * np.pi * f0 * t)
        noise_power = amplitud**2 / (10**(snr_db/10))
        noise = np.sqrt(noise_power) * np.random.randn(len(t))
        return signal + noise
    else:
        return amplitud * np.sin(2 * np.pi * f0 * t)

def muestrear(signal, t, fs):
    """Muestrea la señal a la frecuencia especificada"""
    dt = 1 / fs
    t_sample = np.arange(0, t[-1], dt)
    if len(t_sample) > len(signal):
        t_sample = t_sample[:len(signal)]
    signal_interpolated = np.interp(t_sample, t, signal)
    return t_sample, signal_interpolated

def cuantizar(signal, bits, amplitud_max):
    """Cuantiza la señal con el número de bits especificado"""
    niveles = 2**bits
    delta = 2 * amplitud_max / niveles
    signal_clamped = np.clip(signal, -amplitud_max, amplitud_max)
    signal_quantized = np.round(signal_clamped / delta) * delta
    return signal_quantized

def filtro_antialias(signal, t, fc, order=5):
    """Aplica filtro anti-aliasing básico"""
    from scipy import signal as scipy_signal
    try:
        nyquist = 0.5 * (1 / (t[1] - t[0]))
        normal_cutoff = fc / nyquist
        b, a = scipy_signal.butter(order, normal_cutoff, btype='low', analog=False)
        return scipy_signal.filtfilt(b, a, signal)
    except:
        return signal

def calcular_error_cuantizacion(original, quantized):
    """Calcula métricas de error de cuantización"""
    error = original - quantized
    mse = np.mean(error**2)
    error_max = np.max(np.abs(error))
    snr = 10 * np.log10(np.var(original) / np.var(error)) if np.var(error) > 0 else float('inf')
    return {
        'mse': mse, 
        'snr': snr, 
        'error_signal': error,
        'error_cuadratico_medio': mse,
        'error_maximo': error_max,
        'snr_cuantizacion_db': snr
    }

def reconstruir_senal(t_sample, signal_sample, t_reconstruct):
    """Reconstruye la señal usando interpolación"""
    return np.interp(t_reconstruct, t_sample, signal_sample)

def analizar_aliasing(f0, fs):
    """Analiza si hay aliasing y calcula frecuencias resultantes"""
    f_nyquist = fs / 2
    
    if f0 <= f_nyquist:
        # Caso sin aliasing
        margen = f_nyquist - f0
        nivel_riesgo = "SEGURO" if margen > f_nyquist * 0.1 else "RIESGO" if margen > 0 else "LÍMITE"
        return {
            'aliasing': False, 
            'f_aparente': f0, 
            'f_nyquist': f_nyquist,
            'margen_hz': margen,
            'nivel_riesgo': nivel_riesgo,
            'mensaje': f"✅ Sin aliasing. Margen: {margen:.1f}Hz"
        }
    else:
        # Caso con aliasing
        f_aparente = abs(f0 - fs) if f0 < fs else f0 % fs
        if f_aparente > f_nyquist:
            f_aparente = fs - f_aparente
        
        factor_violacion = f0 / f_nyquist
        if factor_violacion < 1.2:
            severidad = "LEVE"
        elif factor_violacion < 2.0:
            severidad = "MODERADO"
        elif factor_violacion < 3.0:
            severidad = "SEVERO"
        else:
            severidad = "EXTREMO"
            
        return {
            'aliasing': True, 
            'f_aparente': f_aparente, 
            'f_nyquist': f_nyquist,
            'factor_violacion': factor_violacion,
            'severidad': severidad,
            'mensaje': f"🚨 ALIASING {severidad}: {f0:.0f}Hz → {f_aparente:.0f}Hz"
        }

# ===== BASE DE DATOS (CONSOLIDADA) =====
def inicializarBaseDeDatos():
    """Inicializa la base de datos SQLite"""
    conn = sqlite3.connect('señales_adc.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS senales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tipo TEXT NOT NULL,
        f0 REAL NOT NULL,
        amplitud REAL NOT NULL,
        fs REAL NOT NULL,
        bits INTEGER NOT NULL,
        duracion REAL NOT NULL,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        datos_originales BLOB,
        datos_muestreados BLOB,
        datos_cuantizados BLOB
    )''')
    conn.commit()
    conn.close()

def guardar_senal(nombre, tipo, f0, amplitud, fs, bits, duracion, datos_orig, datos_mues, datos_quant):
    """Guarda una señal en la base de datos"""
    try:
        conn = sqlite3.connect('señales_adc.db')
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO senales (nombre, tipo, f0, amplitud, fs, bits, duracion, 
                         datos_originales, datos_muestreados, datos_cuantizados) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (nombre, tipo, f0, amplitud, fs, bits, duracion, 
                       datos_orig.tobytes(), datos_mues.tobytes(), datos_quant.tobytes()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error guardando señal: {e}")
        return False

def obtener_todas_senales():
    """Obtiene todas las señales guardadas"""
    try:
        conn = sqlite3.connect('señales_adc.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, tipo, f0, amplitud, fs, bits, duracion, fecha_creacion FROM senales")
        senales = cursor.fetchall()
        conn.close()
        return senales
    except:
        return []

def obtener_senal(senal_id):
    """Obtiene una señal específica por ID"""
    try:
        conn = sqlite3.connect('señales_adc.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM senales WHERE id = ?", (senal_id,))
        senal = cursor.fetchone()
        conn.close()
        return senal
    except:
        return None

def eliminar_senal(senal_id):
    """Elimina una señal de la base de datos"""
    try:
        conn = sqlite3.connect('señales_adc.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM senales WHERE id = ?", (senal_id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# ===== CASOS PREDEFINIDOS (CONSOLIDADOS) =====
def obtener_casos_predefinidos(categoria=None):
    """Obtiene casos predefinidos para tutoriales"""
    casos = [
        {
            'id': 'basico_senoidal',
            'categoria': 'tutorial',
            'nombre': 'Señal Senoidal Básica',
            'descripcion': 'Conceptos fundamentales con una señal simple',
            'parametros': {'tipo': 'Senoidal', 'f0': 50, 'amplitud': 1.0, 'fs': 1000, 'bits': 16},
            'pasos_tutorial': [
                {
                    'titulo': 'Señal Original',
                    'explicacion': 'Observamos una señal senoidal pura de 50 Hz.',
                    'concepto_clave': 'Señal Analógica',
                    'parametros_cambio': {},
                    'formula': 's(t) = A * sin(2πf₀t)'
                },
                {
                    'titulo': 'Teorema de Nyquist',
                    'explicacion': 'La frecuencia de muestreo debe ser al menos 2×f₀.',
                    'concepto_clave': 'Teorema de Nyquist',
                    'parametros_cambio': {},
                    'formula': 'fs ≥ 2 × f₀'
                },
                {
                    'titulo': 'Muestreo Correcto',
                    'explicacion': 'Con fs=1000Hz > 2×50Hz, no hay aliasing.',
                    'concepto_clave': 'Muestreo',
                    'parametros_cambio': {},
                    'formula': 'fs/f₀ = factor de sobremuestreo'
                },
                {
                    'titulo': 'Cuantización',
                    'explicacion': 'La señal muestreada se convierte a niveles discretos.',
                    'concepto_clave': 'Cuantización',
                    'parametros_cambio': {},
                    'formula': 'Niveles = 2^bits'
                }
            ]
        },
        {
            'id': 'aliasing_demo',
            'categoria': 'concepto',
            'nombre': 'Demostración de Aliasing',
            'descripcion': 'Observa qué pasa cuando no se cumple Nyquist',
            'parametros': {'tipo': 'Senoidal', 'f0': 300, 'amplitud': 1.0, 'fs': 1000, 'bits': 16},
            'pasos_tutorial': [
                {
                    'titulo': '✅ Caso Correcto: Sin Aliasing',
                    'explicacion': 'f₀=300Hz < fs/2=500Hz. La señal se muestrea correctamente. Observa que la reconstrucción mantiene la frecuencia original.',
                    'concepto_clave': 'Teorema de Nyquist',
                    'parametros_cambio': {},
                    'formula': 'Teorema: f₀ = 300Hz < fs/2 = 500Hz ✅'
                },
                {
                    'titulo': '⚠️ Caso Límite: Cerca del borde',
                    'explicacion': 'f₀=480Hz se acerca mucho a fs/2=500Hz. Aún cumple Nyquist pero con poco margen de seguridad.',
                    'concepto_clave': 'Teorema de Nyquist',
                    'parametros_cambio': {'f0': 480},
                    'formula': 'f₀ = 480Hz < fs/2 = 500Hz (margen: solo 20Hz)'
                },
                {
                    'titulo': '🚨 PRIMERA VIOLACIÓN: Aliasing Leve',
                    'explicacion': '¡ATENCIÓN! f₀=600Hz > fs/2=500Hz. Primera violación de Nyquist. La señal aparece como 400Hz en lugar de 600Hz.',
                    'concepto_clave': 'Aliasing',
                    'parametros_cambio': {'f0': 600},
                    'formula': '🚨 ALIASING: f_aparente = |600 - 1000| = 400Hz'
                },
                {
                    'titulo': '� VIOLACIÓN SEVERA: Aliasing Grave',
                    'explicacion': '¡CRÍTICO! f₀=800Hz >> fs/2=500Hz. Aliasing muy evidente: 800Hz aparece como 200Hz. Compara con el paso anterior.',
                    'concepto_clave': 'Aliasing',
                    'parametros_cambio': {'f0': 800},
                    'formula': '💥 ALIASING GRAVE: f_aparente = |800 - 1000| = 200Hz'
                },
                {
                    'titulo': '🔥 CASO EXTREMO: Casi DC',
                    'explicacion': '¡EXTREMO! f₀=950Hz ≈ fs=1000Hz. Una señal de alta frecuencia aparece como 50Hz (casi DC). ¡El peor escenario!',
                    'concepto_clave': 'Aliasing',
                    'parametros_cambio': {'f0': 950},
                    'formula': '🔥 EXTREMO: f_aparente = |950 - 1000| = 50Hz'
                },
                {
                    'titulo': '✅ SOLUCIÓN: Aumentar fs',
                    'explicacion': 'Solucionamos aumentando fs=2000Hz. Ahora f₀=950Hz < fs/2=1000Hz. ¡La señal se recupera correctamente!',
                    'concepto_clave': 'Teorema de Nyquist',
                    'parametros_cambio': {'f0': 950, 'fs': 2000},
                    'formula': '✅ CORRECTO: fs = 2000Hz → f₀ = 950Hz < fs/2 = 1000Hz'
                }
            ]
        },
        {
            'id': 'cuantizacion_baja',
            'categoria': 'concepto',
            'nombre': 'Cuantización de Baja Resolución',
            'descripcion': 'Efectos visibles con pocos bits',
            'parametros': {'tipo': 'Senoidal', 'f0': 50, 'amplitud': 1.0, 'fs': 1000, 'bits': 3},
            'pasos_tutorial': [
                {
                    'titulo': 'Pocos Niveles',
                    'explicacion': 'Con 3 bits solo hay 8 niveles de cuantización.',
                    'concepto_clave': 'Cuantización',
                    'parametros_cambio': {},
                    'formula': 'Δ = 2×Amax/2^bits'
                },
                {
                    'titulo': 'Mejorando Resolución',
                    'explicacion': 'Aumentamos a 8 bits para mayor precisión.',
                    'concepto_clave': 'Cuantización',
                    'parametros_cambio': {'bits': 8},
                    'formula': 'SNR ≈ 6.02×bits + 1.76 dB'
                }
            ]
        }
    ]
    
    if categoria:
        return [caso for caso in casos if caso['categoria'] == categoria]
    return casos

def obtener_caso_predefinido(caso_id):
    """Obtiene un caso específico por ID"""
    casos = obtener_casos_predefinidos()
    for caso in casos:
        if caso['id'] == caso_id:
            return caso
    return None

def generar_explicacion_paso(paso, parametros):
    """Genera explicación detallada para un paso con valores específicos"""
    concepto = paso.get('concepto_clave', '').lower()
    f0 = parametros.get('f0', 50)
    fs = parametros.get('fs', 1000)
    bits = parametros.get('bits', 16)
    amplitud = parametros.get('amplitud', 1.0)
    
    explicacion = {'que_observar': []}
    
    if 'nyquist' in concepto:
        f_nyquist = fs / 2
        factor = fs / (2 * f0) if f0 > 0 else float('inf')
        analisis = analizar_aliasing(f0, fs)
        
        if not analisis['aliasing']:
            margen = analisis.get('margen_hz', 0)
            nivel_riesgo = analisis.get('nivel_riesgo', 'SEGURO')
            
            explicacion['que_observar'] = [
                f"✅ CUMPLE NYQUIST: f₀={f0}Hz < fs/2={f_nyquist}Hz",
                f"📊 En el espectro: pico principal exactamente en {f0}Hz",
                f"🎵 En tiempo: la señal muestreada reproduce la original",
                f"📏 Margen de seguridad: {margen:.0f}Hz ({nivel_riesgo})",
                f"🔢 Factor de sobremuestreo: {factor:.1f}x (recomendado >2x)"
            ]
        else:
            explicacion['que_observar'] = [
                f"❌ VIOLA NYQUIST: f₀={f0}Hz > fs/2={f_nyquist}Hz",
                f"📊 En el espectro: la energía aparece en frecuencias falsas",
                f"🎵 En tiempo: la señal reconstruida tiene frecuencia incorrecta",
                f"⚠️ Frecuencia aparente: {analisis['f_aparente']:.0f}Hz en lugar de {f0}Hz"
            ]
    
    elif 'aliasing' in concepto:
        analisis = analizar_aliasing(f0, fs)
        
        if analisis['aliasing']:
            severidad = analisis.get('severidad', 'MODERADO')
            f_aparente = analisis['f_aparente']
            factor_violacion = analisis.get('factor_violacion', 1.0)
            
            explicacion['que_observar'] = [
                f"🚨 ALIASING {severidad}: factor de violación {factor_violacion:.2f}x",
                f"🎵 Señal real: {f0}Hz → Señal aparente: {f_aparente:.0f}Hz",
                f"📊 En el espectro: pico principal FALSO en {f_aparente:.0f}Hz",
                f"🔍 Comparar señal original vs reconstruida: ¡son diferentes!",
                f"💡 Solución: fs ≥ {2*f0:.0f}Hz para evitar aliasing"
            ]
        else:
            explicacion['que_observar'] = [
                f"✅ Sin aliasing: f₀={f0}Hz respeta el límite de Nyquist",
                f"📊 Espectro correcto: energía en la frecuencia real",
                f"🎵 Reconstrucción fiel de la señal original"
            ]
    
    elif 'cuantiz' in concepto:
        niveles = 2**bits
        delta = 2 * amplitud / niveles
        snr_teorico = 6.02 * bits + 1.76
        
        explicacion['que_observar'] = [
            f"🔢 Cuantización con {bits} bits = {niveles:,} niveles discretos",
            f"📏 Paso de cuantización (Δ): {delta:.4f}V",
            f"🎵 Forma escalonada: cada muestra se redondea al nivel más cercano",
            f"📊 Error máximo teórico: ±{delta/2:.4f}V",
            f"📡 SNR teórico: {snr_teorico:.1f}dB"
        ]
        
        if bits <= 4:
            explicacion['que_observar'].extend([
                f"⚠️ BAJA RESOLUCIÓN: Solo {niveles} niveles causan distorsión visible",
                f"🔍 Observa la forma muy escalonada de la señal cuantizada"
            ])
        elif bits >= 16:
            explicacion['que_observar'].extend([
                f"✅ ALTA RESOLUCIÓN: {niveles:,} niveles minimizan la distorsión",
                f"🔍 La señal cuantizada es casi indistinguible de la original"
            ])
    
    elif 'muestreo' in concepto:
        periodo_muestreo = 1/fs * 1000  # en ms
        periodo_señal = 1/f0 * 1000      # en ms
        muestras_por_periodo = fs / f0
        
        explicacion['que_observar'] = [
            f"⏱️ Período de muestreo: {periodo_muestreo:.2f}ms",
            f"🎵 Período de la señal: {periodo_señal:.1f}ms",
            f"📊 Muestras por período: {muestras_por_periodo:.1f}",
            f"🔍 Puntos rojos: instantes de muestreo discretos",
            f"📈 Línea azul: señal analógica continua original"
        ]
        
        if muestras_por_periodo < 4:
            explicacion['que_observar'].append(
                f"⚠️ POCAS MUESTRAS: <4 muestras/período puede causar pérdida de información"
            )
    
    return explicacion

def obtener_concepto_teorico(concepto_id):
    """Obtiene información teórica detallada de conceptos"""
    conceptos = {
        'señal_analógica': {
            'titulo': 'Señal Analógica',
            'definicion': 'Una señal continua en tiempo y amplitud que representa información del mundo real.',
            'ecuacion': r's(t) = A \sin(2\pi f_0 t + \phi)',
            'parametros': {
                'A': 'Amplitud (V)',
                'f₀': 'Frecuencia fundamental (Hz)', 
                't': 'Tiempo (s)',
                'φ': 'Fase inicial (rad)'
            },
            'aplicaciones': ['Audio', 'Sensores', 'Comunicaciones'],
            'valores_tipicos': {
                'Audio': '20 Hz - 20 kHz',
                'Voz': '300 Hz - 3.4 kHz'
            }
        },
        'teorema_de_nyquist': {
            'titulo': 'Teorema de Nyquist-Shannon',
            'definicion': 'Para reconstruir perfectamente una señal, la frecuencia de muestreo debe ser al menos el doble de la máxima frecuencia de la señal.',
            'ecuacion': r'f_s \geq 2 \cdot f_{max}',
            'parametros': {
                'fs': 'Frecuencia de muestreo (Hz)',
                'fmax': 'Máxima frecuencia de la señal (Hz)',
                'fN': 'Frecuencia de Nyquist = fs/2 (Hz)'
            },
            'aplicaciones': ['Conversión ADC', 'Audio digital', 'Comunicaciones'],
            'ejemplos': {
                'CD Audio': 'fs = 44.1 kHz para audio hasta 20 kHz',
                'Teléfono': 'fs = 8 kHz para voz hasta 4 kHz'
            }
        },
        'muestreo': {
            'titulo': 'Muestreo (Sampling)',
            'definicion': 'Proceso de convertir una señal continua en tiempo a una secuencia de valores discretos en instantes específicos.',
            'ecuacion': r's[n] = s(nT_s) = s(n/f_s)',
            'parametros': {
                'Ts': 'Período de muestreo (s)',
                'fs': 'Frecuencia de muestreo (Hz)',
                'n': 'Índice de muestra (entero)'
            },
            'valores_tipicos': {
                'Audio CD': '44.1 kHz',
                'Audio profesional': '96 kHz',
                'Telefonía': '8 kHz'
            }
        },
        'cuantización': {
            'titulo': 'Cuantización',
            'definicion': 'Proceso de convertir valores continuos de amplitud a un conjunto finito de niveles discretos.',
            'ecuacion': r'SNR_{dB} = 6.02 \cdot N + 1.76',
            'parametros': {
                'N': 'Número de bits',
                'Δ': 'Paso de cuantización (V)',
                'LSB': 'Bit menos significativo'
            },
            'aplicaciones': ['Conversión ADC', 'Compresión', 'Transmisión digital'],
            'valores_tipicos': {
                '16-bit': '96 dB SNR (CD Audio)',
                '24-bit': '144 dB SNR (Audio profesional)',
                '8-bit': '48 dB SNR (aplicaciones básicas)'
            }
        },
        'aliasing': {
            'titulo': 'Aliasing',
            'definicion': 'Fenómeno que ocurre cuando una señal se muestrea a una frecuencia insuficiente, haciendo que componentes de alta frecuencia aparezcan como frecuencias más bajas.',
            'ecuacion': r'f_{aparente} = |f_0 - k \cdot f_s|',
            'parametros': {
                'f₀': 'Frecuencia original (Hz)',
                'fs': 'Frecuencia de muestreo (Hz)',
                'k': 'Entero que minimiza f_aparente'
            },
            'aplicaciones': ['Filtros anti-aliasing', 'Sobremuestreo', 'Diseño ADC'],
            'ejemplos': {
                'Rueda de carreta': 'Efecto visual en películas',
                'Moiré': 'Patrones en imágenes digitales'
            }
        }
    }
    return conceptos.get(concepto_id, None)

# ===== TUTORIAL MANAGER (CONSOLIDADO) =====
class TutorialManager:
    def __init__(self):
        self.reset_tutorial()
    
    def reset_tutorial(self):
        """Reinicia el estado del tutorial"""
        if 'tutorial_activo' not in st.session_state:
            st.session_state.tutorial_activo = False
        if 'tutorial_caso_id' not in st.session_state:
            st.session_state.tutorial_caso_id = None
        if 'tutorial_paso_actual' not in st.session_state:
            st.session_state.tutorial_paso_actual = 0
        if 'tutorial_pasos_completados' not in st.session_state:
            st.session_state.tutorial_pasos_completados = []
        if 'tutorial_parametros_base' not in st.session_state:
            st.session_state.tutorial_parametros_base = {}
    
    def iniciar_tutorial(self, caso_id):
        """Inicia un tutorial específico"""
        caso = obtener_caso_predefinido(caso_id)
        if caso:
            st.session_state.tutorial_activo = True
            st.session_state.tutorial_caso_id = caso_id
            st.session_state.tutorial_paso_actual = 0
            st.session_state.tutorial_pasos_completados = []
            st.session_state.tutorial_parametros_base = caso['parametros'].copy()
            return True
        return False
    
    def detener_tutorial(self):
        """Detiene el tutorial actual"""
        st.session_state.tutorial_activo = False
    
    def siguiente_paso(self):
        """Avanza al siguiente paso del tutorial"""
        caso = obtener_caso_predefinido(st.session_state.tutorial_caso_id)
        if caso and st.session_state.tutorial_paso_actual < len(caso['pasos_tutorial']) - 1:
            st.session_state.tutorial_pasos_completados.append(st.session_state.tutorial_paso_actual)
            st.session_state.tutorial_paso_actual += 1
            return True
        return False
    
    def paso_anterior(self):
        """Retrocede al paso anterior del tutorial"""
        if st.session_state.tutorial_paso_actual > 0:
            st.session_state.tutorial_paso_actual -= 1
            if st.session_state.tutorial_paso_actual in st.session_state.tutorial_pasos_completados:
                st.session_state.tutorial_pasos_completados.remove(st.session_state.tutorial_paso_actual)
            return True
        return False
    
    def obtener_paso_actual(self):
        """Obtiene información del paso actual"""
        caso = obtener_caso_predefinido(st.session_state.tutorial_caso_id)
        if caso and st.session_state.tutorial_paso_actual < len(caso['pasos_tutorial']):
            return caso['pasos_tutorial'][st.session_state.tutorial_paso_actual]
        return None
    
    def obtener_parametros_paso(self):
        """Obtiene los parámetros que deben aplicarse en el paso actual"""
        parametros = st.session_state.tutorial_parametros_base.copy()
        
        caso = obtener_caso_predefinido(st.session_state.tutorial_caso_id)
        if caso:
            # Aplicar cambios acumulativos hasta el paso actual
            for i in range(st.session_state.tutorial_paso_actual + 1):
                if i < len(caso['pasos_tutorial']):
                    paso = caso['pasos_tutorial'][i]
                    cambios = paso.get('parametros_cambio', {})
                    parametros.update(cambios)
        
        return parametros
    
    def mostrar_tutorial_actual(self):
        """Muestra la interfaz del tutorial actual con gráficos compactos y títulos claros"""
        if not st.session_state.get('tutorial_activo', False):
            return None
        
        caso = obtener_caso_predefinido(st.session_state.tutorial_caso_id)
        if not caso:
            st.error("No se pudo cargar el tutorial.")
            self.detener_tutorial()
            return None
        
        paso_actual = self.obtener_paso_actual()
        if not paso_actual:
            st.error("No se pudo cargar el paso del tutorial.")
            return None
        
        # Obtener parámetros del paso actual
        parametros = self.obtener_parametros_paso()
        
        # Obtener información del caso y pasos
        total_pasos = len(caso['pasos_tutorial'])
        paso_num = st.session_state.tutorial_paso_actual + 1
        
        try:
            # ===== CONFIGURACIÓN DE DATOS PARA TUTORIAL =====
            duracion = 0.1  # Duración más larga para ver varios períodos
            t_analog = np.linspace(0, duracion, 4000)  # Señal analógica suave
            
            # Usar parámetros del tutorial
            tipo = parametros.get('tipo', 'Senoidal')
            f0 = parametros.get('f0', 50)
            amplitud = parametros.get('amplitud', 1.0)
            fs = parametros.get('fs', 1000)
            bits = parametros.get('bits', 16)
            
            # Generar señal
            kwargs = {}
            if tipo == "Suma de armonicos":
                kwargs["n_armonicos"] = parametros.get('n_armonicos', 3)
            elif tipo == "Señal con ruido":
                kwargs["snr_db"] = parametros.get('snr_db', 20)
            
            s_analog = generar_señal(tipo, f0, amplitud, t_analog, **kwargs)
            
            # Muestreo y cuantización
            t_sample, s_sample = muestrear(s_analog, t_analog, fs)
            s_quant = cuantizar(s_sample, bits, amplitud)
            
            # ===== LAYOUT COMPACTO EN COLUMNAS =====
            col_params, col_graficos = st.columns([1, 2])
            
            # ===== COLUMNA DE PARÁMETROS Y MÉTRICAS =====
            with col_params:
                # Progreso del tutorial
                progreso = paso_num / total_pasos
                
                st.progress(progreso)
                st.caption(f"📍 Paso {paso_num}/{total_pasos}")
                
                # Título del paso
                st.markdown(f"### {paso_actual['titulo']}")
                st.markdown(f"*{paso_actual['explicacion']}*")
                
                # ===== MÉTRICAS CLAVE =====
                st.markdown("**⚙️ Parámetros:**")
                
                # Fila 1: Señal
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Senal f0", f"{f0} Hz", help="Frecuencia fundamental")
                with col2:
                    st.metric("Amp", f"{amplitud:.1f} V", help="Amplitud de la señal")
                
                # Fila 2: ADC
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("fs", f"{fs} Hz", help="Frecuencia de muestreo")
                with col2:
                    st.metric("Bits", f"{bits}", help="Resolucion del ADC")
                
                # ===== ANÁLISIS AUTOMÁTICO =====
                st.markdown("**📈 Análisis:**")
                
                # Análisis de Nyquist mejorado
                analisis_alias = analizar_aliasing(f0, fs)
                f_nyquist = analisis_alias['f_nyquist']
                
                if not analisis_alias['aliasing']:
                    # Caso sin aliasing
                    factor_sobremuestreo = fs / (2 * f0) if f0 > 0 else float('inf')
                    nivel_riesgo = analisis_alias.get('nivel_riesgo', 'SEGURO')
                    margen = analisis_alias.get('margen_hz', f_nyquist - f0)
                    
                    if nivel_riesgo == 'SEGURO':
                        st.success(f"✅ Nyquist: OK (Seguro)")
                    elif nivel_riesgo == 'RIESGO':
                        st.warning(f"⚠️ Nyquist: OK (Riesgo)")
                    else:
                        st.info(f"🟡 Nyquist: OK (Límite)")
                    
                    st.metric("Factor OSR", f"{factor_sobremuestreo:.1f}x", help="Factor de sobremuestreo")
                    st.metric("Margen", f"{margen:.0f} Hz", help="Margen de seguridad hasta Nyquist")
                else:
                    # Caso con aliasing
                    severidad = analisis_alias.get('severidad', 'MODERADO')
                    f_aparente = analisis_alias['f_aparente']
                    
                    emoji_severidad = {
                        'LEVE': '⚠️',
                        'MODERADO': '🚨',
                        'SEVERO': '💥',
                        'EXTREMO': '🔥'
                    }.get(severidad, '🚨')
                    
                    st.error(f"{emoji_severidad} ALIASING {severidad}")
                    st.metric("f real", f"{f0:.0f} Hz", help="Frecuencia real de la señal")
                    st.metric("f aparente", f"{f_aparente:.0f} Hz", help="Frecuencia que aparece tras el aliasing")
                    
                    deficit = 2 * f0 - fs
                    st.metric("fs mínima", f"{2*f0:.0f} Hz", help="Frecuencia mínima para evitar aliasing")
                
                # Métricas de cuantización
                niveles = 2**bits
                snr_teorico = 6.02 * bits + 1.76
                
                st.metric("Niveles", f"{niveles:,}", help="Niveles de cuantización")
                st.metric("SNR teórico", f"{snr_teorico:.0f} dB", help="SNR de cuantización")
                
                # ===== FÓRMULA DEL PASO =====
                if 'formula' in paso_actual and paso_actual['formula']:
                    st.markdown("**📐 Fórmula clave:**")
                    st.code(paso_actual['formula'], language="text")
            
            # ===== COLUMNA DE GRÁFICOS =====
            with col_graficos:
                # ===== GRÁFICO PRINCIPAL: SEÑALES EN TIEMPO (TÍTULOS SEPARADOS Y CLAROS) =====
                fig_main = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=[
                        '🎵 Señal Analógica vs Muestras', 
                        '📊 Espectro de Frecuencias', 
                        '🔢 Señal Cuantizada', 
                        '📈 Comparación por Resolución'
                    ],
                    specs=[[{"secondary_y": False}, {"secondary_y": False}],
                           [{"secondary_y": False}, {"secondary_y": False}]],
                    vertical_spacing=0.20,  # Más espacio entre filas para títulos
                    horizontal_spacing=0.15  # Más espacio entre columnas
                )
                
                # --- Subplot 1: Señal original y muestras ---
                # Señal analógica (solo algunos puntos para claridad)
                indices_plot = np.linspace(0, len(t_analog)-1, 1500, dtype=int)
                fig_main.add_trace(
                    go.Scatter(
                        x=t_analog[indices_plot]*1000, 
                        y=s_analog[indices_plot],
                        mode='lines', 
                        name='Original',
                        line=dict(color='blue', width=2),
                        opacity=0.8,
                        showlegend=False
                    ), row=1, col=1
                )
                
                # Muestras destacadas
                if len(t_sample) < 200:  # Evitar demasiados puntos
                    fig_main.add_trace(
                        go.Scatter(
                            x=t_sample*1000, 
                            y=s_sample,
                            mode='markers+lines', 
                            name='Muestras',
                            marker=dict(color='orange', size=6),
                            line=dict(color='orange', width=1, dash='dot'),
                            opacity=0.9,
                            showlegend=False
                        ), row=1, col=1
                    )
                
                # --- Subplot 2: Espectro de frecuencia ---
                if len(s_analog) > 100:
                    N = len(s_analog)
                    fft_orig = np.fft.fft(s_analog)
                    freq_orig = np.fft.fftfreq(N, t_analog[1] - t_analog[0])
                    
                    # Solo frecuencias positivas hasta 2*fs para mostrar aliasing
                    max_freq = min(2 * fs, 1500)  # Limitar para mejor visualización
                    mask = (freq_orig >= 0) & (freq_orig <= max_freq)
                    
                    fig_main.add_trace(
                        go.Scatter(
                            x=freq_orig[mask],
                            y=20*np.log10(np.abs(fft_orig[mask]) + 1e-10),
                            mode='lines', 
                            name='Espectro',
                            line=dict(color='purple', width=2),
                            showlegend=False
                        ), row=1, col=2
                    )
                    
                    # Marcar Nyquist y frecuencia fundamental
                    fig_main.add_vline(x=f0, line_dash="solid", line_color="blue", 
                                     row=1, col=2, annotation_text=f"f₀: {f0:.0f}Hz")
                    fig_main.add_vline(x=f_nyquist, line_dash="dash", line_color="red", 
                                     row=1, col=2, annotation_text=f"Nyquist: {f_nyquist:.0f}Hz")
                
                # --- Subplot 3: Señal cuantizada ---
                if len(t_sample) < 200:  # Mostrar solo si no son demasiados puntos
                    fig_main.add_trace(
                        go.Scatter(
                            x=t_sample*1000, 
                            y=s_quant,
                            mode='markers+lines',
                            name='Cuantizada',
                            marker=dict(color='red', size=5, symbol='square'),
                            line=dict(color='red', width=2),
                            showlegend=False
                        ), row=2, col=1
                    )
                
                # --- Subplot 4: Comparación de resoluciones ---
                # Mostrar cómo se vería con diferentes bits
                bits_comparacion = [1, 4, 8, bits] if bits not in [1, 4, 8] else [1, 4, 8, 16]
                colores = ['red', 'orange', 'green', 'blue']
                
                for i, b in enumerate(bits_comparacion[:4]):  # Solo 4 para claridad
                    if b <= 16:  # Evitar calcular demasiados niveles
                        s_temp = cuantizar(s_sample[:30], b, amplitud)  # Solo primeras 30 muestras
                        fig_main.add_trace(
                            go.Scatter(
                                x=t_sample[:30]*1000,
                                y=s_temp,
                                mode='markers+lines',
                                name=f'{b}-bit',
                                marker=dict(color=colores[i], size=4),
                                line=dict(color=colores[i], width=1),
                                opacity=0.8,
                                showlegend=False
                            ), row=2, col=2
                        )
                
                # Configurar ejes con títulos claros y separados
                fig_main.update_xaxes(title_text="Tiempo [ms]", row=1, col=1, title_standoff=10)
                fig_main.update_xaxes(title_text="Frecuencia [Hz]", row=1, col=2, title_standoff=10)
                fig_main.update_xaxes(title_text="Tiempo [ms]", row=2, col=1, title_standoff=10)
                fig_main.update_xaxes(title_text="Tiempo [ms]", row=2, col=2, title_standoff=10)
                
                fig_main.update_yaxes(title_text="Amplitud [V]", row=1, col=1, title_standoff=10)
                fig_main.update_yaxes(title_text="Magnitud [dB]", row=1, col=2, title_standoff=10)
                fig_main.update_yaxes(title_text="Amplitud [V]", row=2, col=1, title_standoff=10)
                fig_main.update_yaxes(title_text="Amplitud [V]", row=2, col=2, title_standoff=10)
                
                # Layout con títulos bien espaciados e información de aliasing
                analisis_alias_titulo = analizar_aliasing(f0, fs)
                if analisis_alias_titulo['aliasing']:
                    severidad = analisis_alias_titulo.get('severidad', 'MODERADO')
                    f_aparente = analisis_alias_titulo['f_aparente']
                    emoji_titulo = {
                        'LEVE': '⚠️',
                        'MODERADO': '🚨',
                        'SEVERO': '💥',
                        'EXTREMO': '🔥'
                    }.get(severidad, '🚨')
                    titulo_aliasing = f"{emoji_titulo} ALIASING {severidad}: {f0}Hz→{f_aparente:.0f}Hz"
                    titulo_principal = f"📊 Tutorial: {tipo} - {titulo_aliasing} @ {fs} Hz, {bits}-bit"
                else:
                    titulo_principal = f"📊 Tutorial: {tipo} - {f0} Hz @ {fs} Hz, {bits}-bit ✅"
                
                fig_main.update_layout(
                    title={
                        'text': titulo_principal,
                        'y': 0.98,
                        'x': 0.5,
                        'xanchor': 'center',
                        'yanchor': 'top'
                    },
                    template="plotly_white",
                    height=600,  # Más altura para separar mejor los títulos
                    showlegend=False,
                    margin=dict(l=60, r=60, t=120, b=60),  # Más margen superior para título
                    font=dict(size=11)  # Fuente un poco más pequeña para que quepa todo
                )
                
                # Anotaciones específicas según el concepto
                concepto = paso_actual.get('concepto_clave', '').lower()
                analisis_current = analizar_aliasing(f0, fs)
                
                if 'aliasing' in concepto and analisis_current['aliasing']:
                    severidad = analisis_current.get('severidad', 'MODERADO')
                    f_aparente = analisis_current['f_aparente']
                    
                    # Color y texto según severidad
                    color_map = {
                        'LEVE': '#ff9500',
                        'MODERADO': '#ff3838',
                        'SEVERO': '#ff1744',
                        'EXTREMO': '#d50000'
                    }
                    
                    emoji_map = {
                        'LEVE': '⚠️',
                        'MODERADO': '🚨',
                        'SEVERO': '💥',
                        'EXTREMO': '🔥'
                    }
                    
                    color = color_map.get(severidad, '#ff3838')
                    emoji = emoji_map.get(severidad, '🚨')
                    
                    fig_main.add_annotation(
                        x=0.5, y=0.95, xref="paper", yref="paper",
                        text=f"{emoji} ALIASING {severidad}<br>{f0:.0f}Hz → {f_aparente:.0f}Hz",
                        showarrow=False,
                        font=dict(size=14, color=color),
                        bgcolor="rgba(255,255,255,0.95)",
                        bordercolor=color,
                        borderwidth=3
                    )
                elif 'nyquist' in concepto and not analisis_current['aliasing']:
                    nivel_riesgo = analisis_current.get('nivel_riesgo', 'SEGURO')
                    margen = analisis_current.get('margen_hz', 0)
                    
                    if nivel_riesgo == 'SEGURO':
                        color, emoji = '#00c851', '✅'
                    elif nivel_riesgo == 'RIESGO':
                        color, emoji = '#ffbb33', '⚠️'
                    else:
                        color, emoji = '#33b5e5', '🟡'
                    
                    fig_main.add_annotation(
                        x=0.5, y=0.95, xref="paper", yref="paper",
                        text=f"{emoji} NYQUIST CUMPLIDO<br>Margen: {margen:.0f}Hz",
                        showarrow=False,
                        font=dict(size=14, color=color),
                        bgcolor="rgba(255,255,255,0.95)",
                        bordercolor=color,
                        borderwidth=2
                    )
                elif 'cuantiz' in concepto:
                    fig_main.add_annotation(
                        x=0.5, y=0.05, xref="paper", yref="paper",
                        text=f"🔢 {niveles} niveles de cuantización ({bits} bits)",
                        showarrow=False,
                        font=dict(size=12, color="blue"),
                        bgcolor="rgba(255,255,255,0.9)",
                        bordercolor="blue"
                    )
                
                st.plotly_chart(fig_main, use_container_width=True)
            
            # ===== EXPLICACIÓN TEÓRICA EXPANDIBLE =====
            st.markdown("---")
            
            # Concepto clave con información completa
            if 'concepto_clave' in paso_actual:
                concepto_id = paso_actual['concepto_clave'].lower().replace(' ', '_').replace('-', '_')
                concepto = obtener_concepto_teorico(concepto_id)
                
                with st.expander(f"💡 **{paso_actual['concepto_clave']}** - Fundamentos Teóricos", expanded=True):
                    if concepto:
                        col_teoria, col_aplicacion = st.columns([2, 1])
                        
                        with col_teoria:
                            st.markdown(f"**{concepto.get('titulo', 'Concepto')}**")
                            st.write(concepto.get('definicion', 'Definición no disponible'))
                            
                            if 'ecuacion' in concepto:
                                st.markdown("**📐 Ecuación principal:**")
                                st.latex(concepto['ecuacion'])
                            
                            if 'parametros' in concepto:
                                st.markdown("**📋 Parámetros:**")
                                for param, desc in concepto['parametros'].items():
                                    st.markdown(f"• **{param}**: {desc}")
                        
                        with col_aplicacion:
                            if 'aplicaciones' in concepto:
                                st.markdown("**🔧 Aplicaciones:**")
                                for app in concepto['aplicaciones']:
                                    st.markdown(f"• {app}")
                            
                            if 'valores_tipicos' in concepto:
                                st.markdown("**📊 Valores típicos:**")
                                for caso, valor in concepto['valores_tipicos'].items():
                                    st.markdown(f"• **{caso}**: {valor}")
                            
                            if 'ejemplos' in concepto:
                                st.markdown("**💡 Ejemplos:**")
                                for ej, valor in concepto['ejemplos'].items():
                                    st.markdown(f"• **{ej}**: {valor}")
                    else:
                        st.info("Información teórica detallada no disponible para este concepto.")
            
            # ===== QUÉ OBSERVAR =====
            explicacion_detallada = generar_explicacion_paso(paso_actual, parametros)
            if explicacion_detallada and 'que_observar' in explicacion_detallada:
                with st.expander("🔍 **Qué observar en los gráficos**", expanded=False):
                    for item in explicacion_detallada['que_observar']:
                        st.markdown(f"• {item}")
                    
                    # Añadir análisis contextual
                    analisis_check = analizar_aliasing(f0, fs)
                    if analisis_check['aliasing']:
                        st.warning(f"⚠️ **Análisis de Aliasing**: La frecuencia de la señal ({f0} Hz) supera la frecuencia de Nyquist ({analisis_check['f_nyquist']} Hz). Observa cómo aparecen componentes espectrales falsas.")
                    
                    if bits <= 4:
                        st.info(f"🔢 **Análisis de Cuantización**: Con {bits} bits solo hay {niveles} niveles disponibles. Observa la forma escalonada de la señal cuantizada.")
            
            # ===== CONTROLES DE NAVEGACIÓN COMPACTOS =====
            st.markdown("---")
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            
            with col1:
                if st.button("⬅️ Anterior", disabled=st.session_state.tutorial_paso_actual == 0, use_container_width=True):
                    self.paso_anterior()
                    st.rerun()
            
            with col2:
                # Indicador de progreso compacto
                pasos_completados = len(st.session_state.tutorial_pasos_completados)
                st.metric("✅ Completados", f"{pasos_completados}/{total_pasos}")
            
            with col3:
                # Botón de reinicio
                if st.button("🔄 Reiniciar", help="Volver al primer paso", use_container_width=True):
                    st.session_state.tutorial_paso_actual = 0
                    st.session_state.tutorial_pasos_completados = []
                    st.rerun()
            
            with col4:
                es_ultimo = st.session_state.tutorial_paso_actual >= total_pasos - 1
                if st.button("Siguiente ➡️", disabled=es_ultimo, use_container_width=True):
                    if not self.siguiente_paso():
                        st.success("🎉 ¡Tutorial completado!")
                        st.balloons()
                        # No detener automáticamente el tutorial para permitir revisión
                    st.rerun()
            
            return parametros
            
        except Exception as e:
            st.error(f"Error generando gráficos del tutorial: {e}")
            # Mostrar solo la información teórica si hay error con los gráficos
            st.markdown(f"### {paso_actual['titulo']}")
            st.markdown(paso_actual['explicacion'])
            
            # Mostrar concepto teórico aunque fallen los gráficos
            if 'concepto_clave' in paso_actual:
                concepto_id = paso_actual['concepto_clave'].lower().replace(' ', '_')
                concepto = obtener_concepto_teorico(concepto_id)
                if concepto:
                    st.markdown(f"**{concepto.get('titulo', 'Concepto')}**")
                    st.write(concepto.get('definicion', ''))
                    if 'ecuacion' in concepto:
                        st.latex(concepto['ecuacion'])
            
            return parametros

def generar_graficos_concepto(concepto_clave, parametros, t_analog, s_analog, t_sample, s_sample, s_quant):
    """Genera gráficos específicos optimizados para cada concepto del tutorial"""
    
    concepto = concepto_clave.lower()
    f0 = parametros.get('f0', 50)
    fs = parametros.get('fs', 1000)
    bits = parametros.get('bits', 16)
    amplitud = parametros.get('amplitud', 1.0)
    
    # Configuración específica por concepto
    if 'nyquist' in concepto or 'aliasing' in concepto:
        # Para conceptos de Nyquist/aliasing: enfocar en dominio tiempo y frecuencia
        fig_main = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                f'🎵 Señal {f0}Hz @ fs={fs}Hz', 
                f'📊 Espectro - Nyquist: {fs/2}Hz', 
                f'🔍 Muestras vs Analógica', 
                f'⚡ Análisis de Aliasing'
            ],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]],
            vertical_spacing=0.25,
            horizontal_spacing=0.15
        )
        
        # --- Subplot 1: Señal completa con más períodos para ver claramente la frecuencia ---
        periodos_mostrar = min(4, max(2, int(0.05 * f0)))  # Mostrar 2-4 períodos
        tiempo_mostrar = periodos_mostrar / f0
        indices_tiempo = t_analog <= tiempo_mostrar
        
        fig_main.add_trace(
            go.Scatter(
                x=t_analog[indices_tiempo]*1000, 
                y=s_analog[indices_tiempo],
                mode='lines', 
                name='Original',
                line=dict(color='blue', width=3),
                showlegend=False
            ), row=1, col=1
        )
        
        # Muestras visibles
        indices_muestra = t_sample <= tiempo_mostrar
        if np.sum(indices_muestra) < 50:  # Solo si no son demasiadas
            fig_main.add_trace(
                go.Scatter(
                    x=t_sample[indices_muestra]*1000, 
                    y=s_sample[indices_muestra],
                    mode='markers', 
                    name='Muestras',
                    marker=dict(color='red', size=8, symbol='circle'),
                    showlegend=False
                ), row=1, col=1
            )
        
        # --- Subplot 2: Espectro con líneas de referencia importantes ---
        if len(s_analog) > 100:
            N = len(s_analog)
            fft_orig = np.fft.fft(s_analog)
            freq_orig = np.fft.fftfreq(N, t_analog[1] - t_analog[0])
            
            # Rango útil del espectro
            max_freq = min(2 * fs, 2000)
            mask = (freq_orig >= 0) & (freq_orig <= max_freq)
            
            fig_main.add_trace(
                go.Scatter(
                    x=freq_orig[mask],
                    y=20*np.log10(np.abs(fft_orig[mask]) + 1e-10),
                    mode='lines', 
                    name='Espectro',
                    line=dict(color='purple', width=2),
                    showlegend=False
                ), row=1, col=2
            )
            
            # Líneas de referencia críticas
            fig_main.add_vline(x=f0, line_dash="solid", line_color="blue", 
                             row=1, col=2, annotation_text=f"f₀: {f0}Hz")
            fig_main.add_vline(x=fs/2, line_dash="dash", line_color="red", 
                             row=1, col=2, annotation_text=f"Nyquist: {fs/2:.0f}Hz")
            
            # Si hay aliasing, mostrar frecuencia aparente
            analisis_alias = analizar_aliasing(f0, fs)
            if analisis_alias['aliasing']:
                f_aparente = analisis_alias['f_aparente']
                fig_main.add_vline(x=f_aparente, line_dash="dot", line_color="orange", 
                                 row=1, col=2, annotation_text=f"f_aparente: {f_aparente:.0f}Hz")
        
        # --- Subplot 3: Comparación detallada analógica vs muestreada ---
        # Mostrar solo un período para ver detalles
        tiempo_detalle = 2 / f0  # 2 períodos
        indices_detalle = t_analog <= tiempo_detalle
        
        fig_main.add_trace(
            go.Scatter(
                x=t_analog[indices_detalle]*1000, 
                y=s_analog[indices_detalle],
                mode='lines', 
                name='Analógica',
                line=dict(color='blue', width=2, dash='solid'),
                showlegend=False
            ), row=2, col=1
        )
        
        # Interpolación de muestras para mostrar reconstrucción
        if len(t_sample) > 0:
            s_reconstruida = np.interp(t_analog, t_sample, s_sample)
            fig_main.add_trace(
                go.Scatter(
                    x=t_analog[indices_detalle]*1000, 
                    y=s_reconstruida[indices_detalle],
                    mode='lines', 
                    name='Reconstruida',
                    line=dict(color='orange', width=2, dash='dot'),
                    showlegend=False
                ), row=2, col=1
            )
        
        # --- Subplot 4: Métricas de análisis visual ---
        # Crear un gráfico de barras con métricas clave
        metricas = ['f₀', 'fs/2', 'Factor OSR']
        valores = [f0, fs/2, fs/(2*f0) if f0 > 0 else 0]
        colores = ['blue', 'red', 'green' if fs >= 2*f0 else 'orange']
        
        fig_main.add_trace(
            go.Bar(
                x=metricas,
                y=valores,
                marker_color=colores,
                showlegend=False
            ), row=2, col=2
        )
    
    elif 'cuantiz' in concepto:
        # Para cuantización: enfocar en niveles y errores
        fig_main = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                f'🎵 Señal Original vs Cuantizada', 
                f'📊 Niveles de Cuantización ({2**bits})', 
                f'🔍 Error de Cuantización', 
                f'📈 Comparación por Bits'
            ],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]],
            vertical_spacing=0.25,
            horizontal_spacing=0.15
        )
        
        # Mostrar menos muestras para ver claramente la cuantización
        num_muestras_mostrar = min(100, len(t_sample))
        indices_mostrar = np.linspace(0, len(t_sample)-1, num_muestras_mostrar, dtype=int)
        
        # --- Subplot 1: Original vs Cuantizada ---
        fig_main.add_trace(
            go.Scatter(
                x=t_sample[indices_mostrar]*1000, 
                y=s_sample[indices_mostrar],
                mode='lines+markers', 
                name='Original',
                line=dict(color='blue', width=2),
                marker=dict(size=4),
                showlegend=False
            ), row=1, col=1
        )
        
        fig_main.add_trace(
            go.Scatter(
                x=t_sample[indices_mostrar]*1000, 
                y=s_quant[indices_mostrar],
                mode='lines+markers', 
                name='Cuantizada',
                line=dict(color='red', width=2),
                marker=dict(size=6, symbol='square'),
                showlegend=False
            ), row=1, col=1
        )
        
        # --- Subplot 2: Mostrar niveles de cuantización ---
        niveles = 2**bits
        delta = 2 * amplitud / niveles
        nivel_values = np.arange(-amplitud, amplitud + delta, delta)
        
        # Histograma de valores cuantizados
        fig_main.add_trace(
            go.Histogram(
                x=s_quant,
                nbinsx=min(50, niveles),
                name='Distribución',
                marker_color='green',
                opacity=0.7,
                showlegend=False
            ), row=1, col=2
        )
        
        # --- Subplot 3: Error de cuantización ---
        error = s_sample[indices_mostrar] - s_quant[indices_mostrar]
        fig_main.add_trace(
            go.Scatter(
                x=t_sample[indices_mostrar]*1000, 
                y=error,
                mode='lines+markers', 
                name='Error',
                line=dict(color='red', width=1),
                marker=dict(size=3),
                showlegend=False
            ), row=2, col=1
        )
        
        # Línea de error máximo teórico
        error_max_teorico = delta / 2
        fig_main.add_hline(y=error_max_teorico, line_dash="dash", line_color="orange", 
                          row=2, col=1, annotation_text=f"Error máx: ±{error_max_teorico:.3f}V")
        fig_main.add_hline(y=-error_max_teorico, line_dash="dash", line_color="orange", 
                          row=2, col=1)
        
        # --- Subplot 4: Comparación de resoluciones ---
        bits_comparacion = [1, 4, 8, bits] if bits not in [1, 4, 8] else [1, 4, 8, 16]
        colores_bits = ['red', 'orange', 'green', 'blue']
        
        # Mostrar solo algunas muestras para claridad
        muestras_comp = min(30, len(t_sample))
        for i, b in enumerate(bits_comparacion[:4]):
            if b <= 16:  # Evitar calcular demasiados niveles
                s_temp = cuantizar(s_sample[:muestras_comp], b, amplitud)
                fig_main.add_trace(
                    go.Scatter(
                        x=t_sample[:muestras_comp]*1000,
                        y=s_temp,
                        mode='lines+markers',
                        name=f'{b}-bit',
                        marker=dict(color=colores_bits[i], size=4),
                        line=dict(color=colores_bits[i], width=1),
                        opacity=0.8,
                        showlegend=False
                    ), row=2, col=2
                )
    
    else:
        # Gráfico general para otros conceptos
        fig_main = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                '🎵 Señal Analógica', 
                '📊 Espectro de Frecuencias', 
                '🔢 Proceso Completo', 
                '📈 Métricas del Sistema'
            ],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]],
            vertical_spacing=0.25,
            horizontal_spacing=0.15
        )
        
        # Gráficos estándar
        indices_plot = np.linspace(0, len(t_analog)-1, 1000, dtype=int)
        fig_main.add_trace(
            go.Scatter(
                x=t_analog[indices_plot]*1000, 
                y=s_analog[indices_plot],
                mode='lines', 
                name='Original',
                line=dict(color='blue', width=2),
                showlegend=False
            ), row=1, col=1
        )
    
    return fig_main

# Inicializar la base de datos y el tutorial manager
inicializarBaseDeDatos()
tutorial_manager = TutorialManager()

st.set_page_config(
    page_title="Simulador ADC - Digitalización de Señales", 
    page_icon="📡", 
    layout="wide"
)

# CSS optimizado para tutoriales compactos
st.markdown("""
<style>
    .main { padding-top: 1rem; }
    
    /* Tarjetas de tutoriales */
    .tutorial-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 1px solid #dee2e6;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .tutorial-card:hover {
        box-shadow: 0 8px 15px rgba(0,0,0,0.15);
        transform: translateY(-2px);
        border-color: #007bff;
    }
    
    /* Métricas compactas */
    .compact-metric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.75rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.25rem;
        font-size: 0.9rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Métricas del sistema (tarjetas principales) */
    .metric-box {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .metric-box:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .metric-box h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1.1rem;
        font-weight: 600;
        opacity: 0.9;
    }
    .metric-box p {
        margin: 0 0 0.25rem 0;
        font-size: 1.8rem;
        font-weight: 700;
        line-height: 1;
    }
    .metric-box small {
        font-size: 0.8rem;
        opacity: 0.8;
        font-weight: 400;
    }
    
    /* Alertas mejoradas */
    .alert-warning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .alert-success {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .alert-error {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .alert-danger {
        background: linear-gradient(135deg, #f8d7da 0%, #f1aeb5 100%);
        border: 1px solid #f1aeb5;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #dc3545;
    }
    
    /* Alertas específicas para aliasing */
    .alert-aliasing-leve {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #ff9500;
    }
    .alert-aliasing-severo {
        background: linear-gradient(135deg, #f8d7da 0%, #f1aeb5 100%);
        border: 1px solid #f1aeb5;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #ff1744;
        animation: pulse-red 2s infinite;
    }
    .alert-aliasing-extremo {
        background: linear-gradient(135deg, #f8d7da 0%, #e3342f 100%);
        border: 1px solid #e3342f;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        border-left: 4px solid #d50000;
        animation: pulse-red 1.5s infinite;
    }
    
    /* Animaciones para casos críticos */
    @keyframes pulse-red {
        0% { box-shadow: 0 4px 8px rgba(213,0,0,0.3); }
        50% { box-shadow: 0 6px 12px rgba(213,0,0,0.6); }
        100% { box-shadow: 0 4px 8px rgba(213,0,0,0.3); }
    }
    
    /* Pasos del tutorial */
    .tutorial-step {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border-left: 4px solid #007bff;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Iconos y badges */
    .tutorial-icon {
        font-size: 2rem;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: white;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
    }
    
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 700;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 0.375rem;
    }
    .badge-primary { background-color: #007bff; color: white; }
    .badge-success { background-color: #28a745; color: white; }
    .badge-warning { background-color: #ffc107; color: #212529; }
    .badge-info { background-color: #17a2b8; color: white; }
    
    /* Mejoras para el modo tutorial */
    .tutorial-mode .stSelectbox > div > div {
        background-color: #e3f2fd;
        border: 2px solid #2196f3;
    }
    
    /* Progreso visual */
    .progress-container {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    /* Iconos y elementos adicionales */
    .tutorial-icon {
        font-size: 2rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .step-indicator {
        background: #28a745;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    /* Hacer gráficos más compactos */
    .js-plotly-plot {
        margin: 0.5rem 0;
    }
    
    /* Reducir padding en expanders */
    .streamlit-expanderHeader {
        padding: 0.5rem 1rem;
    }
    .streamlit-expanderContent {
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("📡 Simulador ADC - Digitalización de Señales")
st.markdown("**Simulador interactivo para entender la conversión analógico-digital**")

# ===========================================
# SELECTOR DE MODO
# ===========================================
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("---")
with col2:
    modo = st.selectbox("Modo:", ["🔬 Libre", "🎓 Tutorial", "📊 Señales Guardadas"], key="modo_selector")

if modo == "🎓 Tutorial":
    # ===========================================
    # INTERFAZ DE TUTORIALES COMPACTA
    # ===========================================
    
    # Verificar si hay un tutorial activo
    if st.session_state.get('tutorial_activo', False):
        # Header compacto del tutorial activo
        caso_actual = obtener_caso_predefinido(st.session_state.tutorial_caso_id)
        if caso_actual:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                if st.button("⏹️ Salir", help="Volver al selector de tutoriales"):
                    tutorial_manager.detener_tutorial()
                    st.rerun()
            with col2:
                st.markdown(f"### 🎓 {caso_actual['nombre']}")
            with col3:
                paso_actual = st.session_state.tutorial_paso_actual
                total_pasos = len(caso_actual.get('pasos_tutorial', []))
                st.metric("Progreso", f"{paso_actual + 1}/{total_pasos}", "pasos")
        
        # Contenido principal del tutorial (compacto)
        tutorial_manager.mostrar_tutorial_actual()
        
    else:
        # Selector de tutoriales mejorado
        st.markdown("### 🎓 Tutoriales Interactivos")
        st.markdown("*Aprende conceptos de conversión ADC paso a paso*")
        
        try:
            casos = obtener_casos_predefinidos()
            tutoriales = [caso for caso in casos if caso.get('categoria') == 'tutorial']
            
            if tutoriales:
                # Grid de tutoriales en tarjetas
                for i, tutorial in enumerate(tutoriales):
                    # Crear una tarjeta por tutorial
                    with st.container():
                        col_icon, col_content, col_action = st.columns([1, 4, 1])
                        
                        with col_icon:
                            # Icono según el tutorial
                            if 'nyquist' in tutorial['id'].lower():
                                st.markdown("### �")
                            elif 'aliasing' in tutorial['id'].lower():
                                st.markdown("### ⚡")
                            elif 'cuantiz' in tutorial['id'].lower():
                                st.markdown("### 🔢")
                            else:
                                st.markdown("### 📚")
                        
                        with col_content:
                            st.markdown(f"**{tutorial['nombre']}**")
                            st.markdown(tutorial['descripcion'])
                            
                            # Información del tutorial
                            pasos = tutorial.get('pasos_tutorial', [])
                            col_info1, col_info2 = st.columns(2)
                            with col_info1:
                                st.caption(f"📝 {len(pasos)} pasos")
                            with col_info2:
                                # Mostrar parámetros clave
                                params = tutorial.get('parametros', {})
                                st.caption(f"🎵 {params.get('tipo', 'N/A')} - {params.get('f0', 'N/A')} Hz")
                        
                        with col_action:
                            if st.button("▶️", key=f"start_{tutorial['id']}", 
                                        help=f"Iniciar {tutorial['nombre']}"):
                                tutorial_manager.iniciar_tutorial(tutorial['id'])
                                st.rerun()
                        
                        # Separador
                        if i < len(tutoriales) - 1:
                            st.markdown("---")
                
                # Información adicional
                st.markdown("---")
                with st.expander("ℹ️ Cómo usar los tutoriales", expanded=False):
                    st.markdown("""
                    **Instrucciones:**
                    1. **Selecciona** un tutorial haciendo clic en ▶️
                    2. **Navega** usando los botones ⬅️ Anterior y Siguiente ➡️
                    3. **Observa** los gráficos y parámetros en tiempo real
                    4. **Lee** las explicaciones y conceptos teóricos
                    5. **Aprende** visualizando el efecto de cada cambio
                    
                    **Consejos:**
                    - Presta atención a los gráficos que cambian con cada paso
                    - Lee la sección "Qué observar" para enfocar tu análisis
                    - Expande los conceptos teóricos para profundizar
                    - Completa todos los pasos para una comprensión integral
                    """)
            else:
                st.info("No hay tutoriales disponibles.")
                
        except Exception as e:
            st.error(f"Error al cargar tutoriales: {e}")
            st.error("Verifica que los módulos de tutoriales estén correctamente instalados.")

elif modo == "📊 Señales Guardadas":
    # ===========================================
    # MODO SEÑALES GUARDADAS
    # ===========================================
    st.markdown("---")
    st.markdown("### 📊 Señales Guardadas")
    st.markdown("*Visualiza y carga señales previamente guardadas*")
    
    # Obtener todas las señales guardadas
    senales_guardadas = obtener_todas_senales()
    
    if not senales_guardadas:
        st.info("📭 No hay señales guardadas aún. Ve al modo libre y guarda algunas configuraciones.")
    else:
        # Mostrar lista de señales
        st.markdown(f"**🎵 {len(senales_guardadas)} señales encontradas:**")
        
        # Crear un selectbox para elegir la señal
        opciones_senales = {}
        for senal in senales_guardadas:
            id_senal, nombre, tipo, f0, amplitud, fs, bits, duracion, fecha = senal
            label = f"{nombre} | {tipo} {f0}Hz @ {fs}Hz {bits}bit | {fecha}"
            opciones_senales[label] = senal
        
        senal_seleccionada = st.selectbox(
            "Selecciona una señal para visualizar:",
            list(opciones_senales.keys())
        )
        
        if senal_seleccionada:
            senal_datos = opciones_senales[senal_seleccionada]
            id_senal, nombre, tipo, f0, amplitud, fs, bits, duracion, fecha = senal_datos
            
            # Mostrar información de la señal
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**📋 Información:**")
                st.write(f"**Nombre:** {nombre}")
                st.write(f"**Tipo:** {tipo}")
                st.write(f"**Fecha:** {fecha}")
            
            with col2:
                st.markdown("**🎚️ Parámetros:**")
                st.write(f"**Frecuencia:** {f0} Hz")
                st.write(f"**Amplitud:** {amplitud} V")
                st.write(f"**Duración:** {duracion} s")
            
            with col3:
                st.markdown("**🔧 ADC:**")
                st.write(f"**Muestreo:** {fs} Hz")
                st.write(f"**Resolución:** {bits} bits")
                f_nyquist = fs / 2
                aliasing = "❌ Sí" if f0 > f_nyquist else "✅ No"
                st.write(f"**Aliasing:** {aliasing}")
            
            # Botones de acción
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Regenerar y Visualizar", use_container_width=True):
                    st.session_state.regenerar_senal = id_senal
            
            with col2:
                if st.button("📋 Copiar a Modo Libre", use_container_width=True):
                    st.session_state.copiar_parametros = {
                        'tipo': tipo, 'f0': f0, 'amplitud': amplitud,
                        'fs': fs, 'bits': bits
                    }
                    st.success("✅ Parámetros copiados. Ve al modo libre para usarlos.")
            
            with col3:
                if st.button("🗑️ Eliminar Señal", use_container_width=True):
                    if eliminar_senal(id_senal):
                        st.success("✅ Señal eliminada")
                        st.rerun()
                    else:
                        st.error("❌ Error al eliminar")
            
            # Regenerar señal si se solicitó
            if st.session_state.get('regenerar_senal') == id_senal:
                st.markdown("---")
                st.markdown("### 📈 Visualización Regenerada")
                
                try:
                    # Regenerar la señal con los parámetros guardados
                    duracion_vis = 0.1
                    t_analog = np.linspace(0, duracion_vis, 20000)
                    s_analog = generar_señal(tipo, f0, amplitud, t_analog)
                    
                    # Procesar
                    t_sample, s_sample = muestrear(s_analog, t_analog, fs)
                    s_quant = cuantizar(s_sample, bits, amplitud)
                    s_reconstruida = reconstruir_senal(t_sample, s_quant, t_analog)
                    
                    # Análisis
                    analisis_alias = analizar_aliasing(f0, fs)
                    error_metrics = calcular_error_cuantizacion(s_sample, s_quant)
                    
                    # Métricas regeneradas
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(
                            f'<div class="metric-box">'
                            f'<h3>🎚️ Muestreo</h3>'
                            f'<p>{fs:,.0f} Hz</p>'
                            f'<small>Frecuencia de muestreo</small>'
                            f'</div>', 
                            unsafe_allow_html=True
                        )
                    
                    with col2:
                        f_nyquist = fs / 2
                        nyquist_ok = f0 <= f_nyquist
                        color = "#00b894" if nyquist_ok else "#e17055"
                        st.markdown(
                            f'<div class="metric-box" style="background: {color};">'
                            f'<h3>📏 Nyquist</h3>'
                            f'<p>{f_nyquist:,.0f} Hz</p>'
                            f'<small>{"✅ OK" if nyquist_ok else "❌ Aliasing"}</small>'
                            f'</div>', 
                            unsafe_allow_html=True
                        )
                    
                    with col3:
                        niveles = 2**bits
                        st.markdown(
                            f'<div class="metric-box">'
                            f'<h3>🔢 Cuantización</h3>'
                            f'<p>{niveles:,} niveles</p>'
                            f'<small>{bits} bits</small>'
                            f'</div>', 
                            unsafe_allow_html=True
                        )
                    
                    with col4:
                        snr_db = error_metrics['snr_cuantizacion_db']
                        st.markdown(
                            f'<div class="metric-box">'
                            f'<h3>📡 SNR</h3>'
                            f'<p>{snr_db:.1f} dB</p>'
                            f'<small>Calidad de señal</small>'
                            f'</div>', 
                            unsafe_allow_html=True
                        )
                    
                    # Gráficos regenerados
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig1 = go.Figure()
                        
                        fig1.add_trace(go.Scatter(
                            x=t_analog*1000, y=s_analog,
                            mode='lines', name='Señal original',
                            line=dict(color='blue', width=2)
                        ))
                        
                        fig1.add_trace(go.Scatter(
                            x=t_analog*1000, y=s_reconstruida,
                            mode='lines', name='Reconstruida',
                            line=dict(color='purple', width=1, dash='dot')
                        ))
                        
                        fig1.update_layout(
                            title=f"🎵 {tipo} - {f0} Hz",
                            xaxis_title="Tiempo [ms]",
                            yaxis_title="Amplitud [V]",
                            template="plotly_white"
                        )
                        
                        st.plotly_chart(fig1, use_container_width=True)
                    
                    with col2:
                        fig2 = go.Figure()
                        
                        fig2.add_trace(go.Scatter(
                            x=t_sample*1000, y=s_sample,
                            mode='lines+markers', name='Muestras',
                            line=dict(color='orange', width=2),
                            marker=dict(size=6)
                        ))
                        
                        fig2.add_trace(go.Scatter(
                            x=t_sample*1000, y=s_quant,
                            mode='markers', name='Cuantizada',
                            marker=dict(color='red', size=8, symbol='square')
                        ))
                        
                        fig2.update_layout(
                            title=f"🔢 Digitalizada - {bits} bits",
                            xaxis_title="Tiempo [ms]",
                            yaxis_title="Amplitud [V]",
                            template="plotly_white"
                        )
                        
                        st.plotly_chart(fig2, use_container_width=True)
                    
                    # Análisis espectral
                    st.markdown("### 🔬 Análisis Espectral")
                    
                    N = len(s_analog)
                    fft_orig = np.fft.fft(s_analog)
                    freq_orig = np.fft.fftfreq(N, t_analog[1] - t_analog[0])
                    
                    s_quant_interp = np.interp(t_analog, t_sample, s_quant)
                    fft_quant = np.fft.fft(s_quant_interp)
                    
                    fig_fft = go.Figure()
                    
                    fig_fft.add_trace(go.Scatter(
                        x=freq_orig[:N//2],
                        y=20*np.log10(np.abs(fft_orig)[:N//2] + 1e-10),
                        mode='lines', name='Original',
                        line=dict(color='blue', width=2)
                    ))
                    
                    fig_fft.add_trace(go.Scatter(
                        x=freq_orig[:N//2],
                        y=20*np.log10(np.abs(fft_quant)[:N//2] + 1e-10),
                        mode='lines', name='Cuantizada',
                        line=dict(color='red', width=2, dash='dash')
                    ))
                    
                    fig_fft.add_vline(x=f_nyquist, line_dash="dash", line_color="green",
                                      annotation_text=f"Nyquist: {f_nyquist:.0f} Hz")
                    
                    fig_fft.update_layout(
                        title="📊 Espectro de Frecuencia",
                        xaxis_title="Frecuencia [Hz]",
                        yaxis_title="Magnitud [dB]",
                        template="plotly_white",
                        xaxis=dict(range=[0, min(2000, fs)])
                    )
                    
                    st.plotly_chart(fig_fft, use_container_width=True)
                    
                    # Análisis teórico
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if analisis_alias['aliasing']:
                            severidad = analisis_alias.get('severidad', 'MODERADO')
                            factor = analisis_alias.get('factor_violacion', f0/f_nyquist)
                            
                            emoji = {
                                'LEVE': '⚠️', 'MODERADO': '🚨', 'SEVERO': '💥', 'EXTREMO': '🔥'
                            }.get(severidad, '🚨')
                            
                            st.markdown(
                                f'<div class="alert-warning">'
                                f'{emoji} <strong>ALIASING {severidad}</strong><br>'
                                f'Frecuencia real: {f0:.1f} Hz<br>'
                                f'Frecuencia aparente: {analisis_alias["f_aparente"]:.1f} Hz<br>'
                                f'Factor de violación: {factor:.2f}x<br>'
                                f'<strong>Solución:</strong> fs ≥ {2*f0:.0f} Hz'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            margen = analisis_alias.get('margen_hz', f_nyquist - f0)
                            st.markdown(
                                f'<div class="alert-success">'
                                f'✅ <strong>TEOREMA DE NYQUIST CUMPLIDO</strong><br>'
                                f'fs = {fs:.0f} Hz > 2×f₀ = {2*f0:.0f} Hz<br>'
                                f'Margen de seguridad: {margen:.1f} Hz'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                    
                    with col2:
                        snr_teorico = 6.02 * bits + 1.76
                        st.markdown(
                            f'**📚 Métricas de Calidad**\n\n'
                            f'• **SNR teórico:** {snr_teorico:.1f} dB\n'
                            f'• **SNR medido:** {snr_db:.1f} dB\n'
                            f'• **Error cuadrático medio:** {error_metrics["error_cuadratico_medio"]:.6f}\n'
                            f'• **Error máximo:** {error_metrics["error_maximo"]:.6f}'
                        )
                    
                    if st.button("🔄 Ocultar Visualización"):
                        del st.session_state.regenerar_senal
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error regenerando la señal: {e}")

else:
    # ===========================================
    # MODO LIBRE (INTERFAZ ORIGINAL)
    # ===========================================
    st.markdown("---")

    # ===========================================
    # CONFIGURACIÓN DE SEÑAL
    # ===========================================
    st.sidebar.header("⚙️ Configuración de Señal")

    # Tipo de señal
    tipo = st.sidebar.selectbox(
        "Tipo de señal:",
        ["Senoidal", "Cuadrada", "Diente de sierra", "Triangular", "Suma de armonicos", "Señal con ruido"]
    )

    # Parámetros básicos
    f0 = st.sidebar.slider("Frecuencia fundamental (Hz)", 1.0, 1000.0, 50.0)
    amplitud = st.sidebar.slider("Amplitud (V)", 0.1, 5.0, 1.0)

    # Parámetros específicos
    kwargs = {}
    if tipo == "Suma de armonicos":
        n_armonicos = st.sidebar.slider("Número de armónicos", 2, 10, 3)
        kwargs = {"n_armonicos": n_armonicos}
    elif tipo == "Señal con ruido":
        snr_db = st.sidebar.slider("SNR (dB)", 0, 50, 20)
        kwargs = {"snr_db": snr_db}

    st.sidebar.markdown("---")

    # ===========================================
    # CONFIGURACIÓN ADC
    # ===========================================
    st.sidebar.header("🔄 Configuración ADC")

    # Muestreo con opciones estándar
    fs_opciones = {
        "100 Hz (Muy baja - Experimentos)": 100,
        "500 Hz (Baja - Análisis)": 500,
        "1 kHz (Señales lentas)": 1000,
        "8 kHz (Telefónica)": 8000,
        "22.05 kHz (Radio FM)": 22050,
        "44.1 kHz (CD Audio)": 44100,
        "48 kHz (Profesional)": 48000,
        "96 kHz (Alta fidelidad)": 96000,
        "Personalizada": None
    }

    fs_seleccion = st.sidebar.selectbox("Tasa de muestreo:", list(fs_opciones.keys()))
    if fs_seleccion == "Personalizada":
        # Selector de rango para mejor control
        rango_fs = st.sidebar.selectbox(
            "Rango de frecuencias:",
            ["Muy bajas (1 Hz - 100 Hz)", "Bajas (100 Hz - 1 kHz)", "Medias (1 kHz - 10 kHz)", "Altas (10 kHz - 200 kHz)"]
        )
        
        if rango_fs == "Muy bajas (1 Hz - 100 Hz)":
            fs = st.sidebar.slider("Frecuencia de muestreo (Hz)", 1.0, 100.0, 50.0, 1.0)
        elif rango_fs == "Bajas (100 Hz - 1 kHz)":
            fs = st.sidebar.slider("Frecuencia de muestreo (Hz)", 100.0, 1000.0, 500.0, 10.0)
        elif rango_fs == "Medias (1 kHz - 10 kHz)":
            fs = st.sidebar.slider("Frecuencia de muestreo (Hz)", 1000.0, 10000.0, 5000.0, 100.0)
        else:  # Altas
            fs = st.sidebar.slider("Frecuencia de muestreo (Hz)", 10000.0, 200000.0, 50000.0, 1000.0)
    else:
        fs = fs_opciones[fs_seleccion]

    # Cuantización con opciones estándar
    bits_opciones = {
        "8 bits (Baja calidad)": 8,
        "16 bits (CD Audio)": 16,
        "24 bits (Profesional)": 24,
        "32 bits (Estudio)": 32
    }

    bits_seleccion = st.sidebar.selectbox("Resolución de cuantización:", list(bits_opciones.keys()))
    bits = bits_opciones[bits_seleccion]

    # Opciones avanzadas
    st.sidebar.markdown("---")
    st.sidebar.header("🔧 Opciones Avanzadas")
    aplicar_filtro = st.sidebar.checkbox("Aplicar filtro anti-alias")
    mostrar_reconstruccion = st.sidebar.checkbox("Mostrar reconstrucción", True)

    # ===========================================
    # PROCESAMIENTO DE SEÑAL
    # ===========================================

    # Generar señal analógica
    duracion = 0.1
    t_analog = np.linspace(0, duracion, 20000)
    s_analog = generar_señal(tipo, f0, amplitud, t_analog, **kwargs)

    # Filtro anti-alias
    if aplicar_filtro:
        try:
            s_analog_filtrada = filtro_antialias(s_analog, fs, 0.45, 5)
        except:
            s_analog_filtrada = s_analog.copy()
    else:
        s_analog_filtrada = s_analog.copy()

    # Muestreo y cuantización
    t_sample, s_sample = muestrear(s_analog_filtrada, t_analog, fs)
    s_quant = cuantizar(s_sample, bits, amplitud)

    # Reconstrucción
    if mostrar_reconstruccion:
        s_reconstruida = reconstruir_senal(t_sample, s_quant, t_analog)

    # Análisis
    analisis_alias = analizar_aliasing(f0, fs)
    error_metrics = calcular_error_cuantizacion(s_sample, s_quant)

    # ===========================================
    # MÉTRICAS PRINCIPALES
    # ===========================================
    st.subheader("📊 Métricas del Sistema")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f'<div class="metric-box">'
            f'<h3>🎚️ Muestreo</h3>'
            f'<p>{fs:,.0f} Hz</p>'
            f'<small>Frecuencia de muestreo</small>'
            f'</div>', 
            unsafe_allow_html=True
        )

    with col2:
        f_nyquist = fs / 2
        nyquist_ok = f0 <= f_nyquist
        color = "#00b894" if nyquist_ok else "#e17055"
        st.markdown(
            f'<div class="metric-box" style="background: {color};">'
            f'<h3>📏 Nyquist</h3>'
            f'<p>{f_nyquist:,.0f} Hz</p>'
            f'<small>{"✅ OK" if nyquist_ok else "❌ Aliasing"}</small>'
            f'</div>', 
            unsafe_allow_html=True
        )

    with col3:
        niveles = 2**bits
        st.markdown(
            f'<div class="metric-box">'
            f'<h3>🔢 Cuantización</h3>'
            f'<p>{niveles:,} niveles</p>'
            f'<small>{bits} bits</small>'
            f'</div>', 
            unsafe_allow_html=True
        )

    with col4:
        snr_db = error_metrics['snr_cuantizacion_db']
        st.markdown(
            f'<div class="metric-box">'
            f'<h3>📡 SNR</h3>'
            f'<p>{snr_db:.1f} dB</p>'
            f'<small>Calidad de señal</small>'
            f'</div>', 
            unsafe_allow_html=True
        )

    # ===========================================
    # VISUALIZACIONES
    # ===========================================
    st.subheader("📈 Visualización de Señales")

    # Gráfico 1: Señal analógica
    col1, col2 = st.columns(2)

    with col1:
        fig1 = go.Figure()
        
        fig1.add_trace(go.Scatter(
            x=t_analog*1000, y=s_analog,
            mode='lines', name='Señal original',
            line=dict(color='blue', width=2)
        ))
        
        if aplicar_filtro:
            fig1.add_trace(go.Scatter(
                x=t_analog*1000, y=s_analog_filtrada,
                mode='lines', name='Filtrada',
                line=dict(color='green', width=2, dash='dash')
            ))
        
        if mostrar_reconstruccion:
            fig1.add_trace(go.Scatter(
                x=t_analog*1000, y=s_reconstruida,
                mode='lines', name='Reconstruida',
                line=dict(color='purple', width=1, dash='dot')
            ))
        
        fig1.update_layout(
            title="🎵 Señal Analógica",
            xaxis_title="Tiempo [ms]",
            yaxis_title="Amplitud [V]",
            template="plotly_white"
        )
        
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        
        fig2.add_trace(go.Scatter(
            x=t_sample*1000, y=s_sample,
            mode='lines+markers', name='Muestras',
            line=dict(color='orange', width=2),
            marker=dict(size=6)
        ))
        
        fig2.add_trace(go.Scatter(
            x=t_sample*1000, y=s_quant,
            mode='markers', name='Cuantizada',
            marker=dict(color='red', size=8, symbol='square')
        ))
        
        fig2.update_layout(
            title="🔢 Señal Digitalizada",
            xaxis_title="Tiempo [ms]",
            yaxis_title="Amplitud [V]",
            template="plotly_white"
        )
        
        st.plotly_chart(fig2, use_container_width=True)

    # ===========================================
    # ANÁLISIS ESPECTRAL
    # ===========================================
    st.subheader("🔬 Análisis Espectral")

    # FFT
    N = len(s_analog)
    fft_orig = np.fft.fft(s_analog)
    freq_orig = np.fft.fftfreq(N, t_analog[1] - t_analog[0])

    s_quant_interp = np.interp(t_analog, t_sample, s_quant)
    fft_quant = np.fft.fft(s_quant_interp)

    fig_fft = go.Figure()

    fig_fft.add_trace(go.Scatter(
        x=freq_orig[:N//2],
        y=20*np.log10(np.abs(fft_orig)[:N//2] + 1e-10),
        mode='lines', name='Original',
        line=dict(color='blue', width=2)
    ))

    fig_fft.add_trace(go.Scatter(
        x=freq_orig[:N//2],
        y=20*np.log10(np.abs(fft_quant)[:N//2] + 1e-10),
        mode='lines', name='Cuantizada',
        line=dict(color='red', width=2, dash='dash')
    ))

    fig_fft.add_vline(x=f_nyquist, line_dash="dash", line_color="green",
                      annotation_text=f"Nyquist: {f_nyquist:.0f} Hz")

    fig_fft.update_layout(
        title="📊 Espectro de Frecuencia",
        xaxis_title="Frecuencia [Hz]",
        yaxis_title="Magnitud [dB]",
        template="plotly_white",
        xaxis=dict(range=[0, min(2000, fs)])
    )

    st.plotly_chart(fig_fft, use_container_width=True)

    # ===========================================
    # ANÁLISIS TEÓRICO
    # ===========================================
    st.subheader("🔬 Análisis Teórico")

    col1, col2 = st.columns(2)

    with col1:
        if analisis_alias['aliasing']:
            severidad = analisis_alias.get('severidad', 'MODERADO')
            factor = analisis_alias.get('factor_violacion', f0/f_nyquist)
            
            # Color basado en severidad
            color_class = {
                'LEVE': 'alert-warning',
                'MODERADO': 'alert-danger',
                'SEVERO': 'alert-danger',
                'EXTREMO': 'alert-danger'
            }.get(severidad, 'alert-danger')
            
            emoji = {
                'LEVE': '⚠️',
                'MODERADO': '🚨',
                'SEVERO': '💥',
                'EXTREMO': '🔥'
            }.get(severidad, '🚨')
            
            st.markdown(
                f'<div class="{color_class}">'
                f'{emoji} <strong>ALIASING {severidad}</strong><br>'
                f'Frecuencia real: {f0:.1f} Hz<br>'
                f'Frecuencia aparente: {analisis_alias["f_aparente"]:.1f} Hz<br>'
                f'Factor de violación: {factor:.2f}x<br>'
                f'Frecuencia de Nyquist: {f_nyquist:.1f} Hz<br>'
                f'<strong>Solución:</strong> fs ≥ {2*f0:.0f} Hz'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            margen = analisis_alias.get('margen_hz', f_nyquist - f0)
            nivel = analisis_alias.get('nivel_riesgo', 'SEGURO')
            
            emoji = '✅' if nivel == 'SEGURO' else '⚠️' if nivel == 'RIESGO' else '🟡'
            
            st.markdown(
                f'<div class="alert-success">'
                f'{emoji} <strong>TEOREMA DE NYQUIST CUMPLIDO</strong><br>'
                f'fs = {fs:.0f} Hz > 2×f₀ = {2*f0:.0f} Hz<br>'
                f'Margen de seguridad: {margen:.1f} Hz<br>'
                f'Nivel de riesgo: {nivel}'
                f'</div>',
                unsafe_allow_html=True
            )

    with col2:
        # Fórmulas teóricas
        snr_teorico = 6.02 * bits + 1.76
        resolucion = 2 * amplitud / (2**bits)
        
        st.markdown(
            f'**📚 Fórmulas Teóricas**\n\n'
            f'• **SNR teórico:** {snr_teorico:.1f} dB\n'
            f'• **SNR medido:** {snr_db:.1f} dB\n'
            f'• **Resolución:** {resolucion:.4f} V\n'
            f'• **Rango dinámico:** {20*np.log10(2**bits):.1f} dB'
        )

    # ===========================================
    # MÉTRICAS DETALLADAS
    # ===========================================
    st.subheader("📋 Métricas Detalladas")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Error cuadrático medio", f"{error_metrics['error_cuadratico_medio']:.6f}")
        st.metric("Error máximo", f"{error_metrics['error_maximo']:.6f}")

    with col2:
        st.metric("Número de muestras", len(t_sample))
        st.metric("Periodo de muestreo", f"{1/fs*1000:.3f} ms")

    with col3:
        st.metric("Relación fs/f0", f"{fs/f0:.1f}")
        st.metric("Factor de sobremuestreo", f"{fs/(2*f0):.1f}×")

    # ===========================================
    # GUARDAR CONFIGURACIÓN
    # ===========================================
    if st.button("💾 Guardar Configuración Actual"):
        nombre_senal = f"{tipo}_{f0}Hz_{fs}Hz_{bits}bit"
        
        if guardar_senal(nombre_senal, tipo, f0, amplitud, fs, bits, duracion, 
                        s_analog, s_sample, s_quant):
            st.success("✅ Configuración guardada correctamente")
        else:
            st.error("❌ Error al guardar la configuración")

# ===========================================
# FOOTER
# ===========================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; margin-top: 2rem;'>
        <p><strong>📡 Simulador ADC - Digitalización de Señales</strong></p>
        <p>Funcionalidades: Generación de señales • Muestreo • Cuantización • Teorema de Nyquist • Análisis de aliasing • Tutoriales interactivos</p>
    </div>
    """,
    unsafe_allow_html=True
)
