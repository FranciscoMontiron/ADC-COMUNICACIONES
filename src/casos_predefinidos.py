"""
Casos predefinidos y tutoriales para el simulador ADC
====================================================

Casos educativos que demuestran conceptos específicos de conversión ADC.
"""

import numpy as np

def obtener_casos_predefinidos(categoria=None):
    """Obtiene casos predefinidos filtrados por categoría"""
    casos = [
        # TUTORIALES BÁSICOS
        {
            "id": "tutorial_basico_nyquist",
            "categoria": "tutorial",
            "nombre": "Tutorial: Teorema de Nyquist",
            "descripcion": "Demostración paso a paso del criterio de Nyquist",
            "parametros": {
                "tipo": "Senoidal",
                "f0": 50,
                "amplitud": 1.0,
                "fs": 200,
                "bits": 16
            },
            "pasos_tutorial": [
                {
                    "titulo": "Señal sin aliasing",
                    "explicacion": "fs = 200 Hz > 2×f₀ = 100 Hz. Se cumple Nyquist.",
                    "concepto_clave": "Teorema de Nyquist",
                    "parametros_cambio": {"fs": 200},
                    "formula": "fs ≥ 2 × fmax"
                },
                {
                    "titulo": "Límite crítico",
                    "explicacion": "fs = 100 Hz = 2×f₀. Justo en el límite de Nyquist.",
                    "concepto_clave": "Frecuencia de Nyquist",
                    "parametros_cambio": {"fs": 100},
                    "formula": "fNyquist = fs/2"
                },
                {
                    "titulo": "Submuestreo con aliasing",
                    "explicacion": "fs = 80 Hz < 2×f₀ = 100 Hz. ¡Aparece aliasing!",
                    "concepto_clave": "Aliasing",
                    "parametros_cambio": {"fs": 80},
                    "formula": "falias = |f₀ - n×fs|"
                }
            ]
        },
        
        {
            "id": "tutorial_cuantizacion",
            "categoria": "tutorial", 
            "nombre": "Tutorial: Efectos de Cuantización",
            "descripcion": "Cómo afecta el número de bits a la calidad de la señal",
            "parametros": {
                "tipo": "Senoidal",
                "f0": 440,
                "amplitud": 1.0,
                "fs": 8000,
                "bits": 1
            },
            "pasos_tutorial": [
                {
                    "titulo": "1 bit - Cuantización extrema",
                    "explicacion": "Solo 2 niveles. Distorsión máxima pero se mantiene frecuencia.",
                    "concepto_clave": "Cuantización",
                    "parametros_cambio": {"bits": 1},
                    "formula": "Niveles = 2ⁿ"
                },
                {
                    "titulo": "4 bits - Calidad baja", 
                    "explicacion": "16 niveles. Mejora notable pero aún hay distorsión visible.",
                    "concepto_clave": "Resolución ADC",
                    "parametros_cambio": {"bits": 4},
                    "formula": "LSB = Vref/2ⁿ"
                },
                {
                    "titulo": "8 bits - Calidad aceptable",
                    "explicacion": "256 niveles. Calidad telefónica, distorsión mínima.",
                    "concepto_clave": "SNR de cuantización",
                    "parametros_cambio": {"bits": 8},
                    "formula": "SNR = 6.02n + 1.76 dB"
                },
                {
                    "titulo": "16 bits - Alta calidad",
                    "explicacion": "65536 niveles. Calidad CD, prácticamente sin distorsión audible.",
                    "concepto_clave": "Rango dinámico",
                    "parametros_cambio": {"bits": 16},
                    "formula": "DR = 20×log₁₀(2ⁿ) dB"
                }
            ]
        },

        # CONCEPTOS ESPECÍFICOS
        {
            "id": "concepto_aliasing_practico",
            "categoria": "concepto",
            "nombre": "Aliasing en Señales Complejas",
            "descripcion": "Demostración de aliasing con señal cuadrada",
            "parametros": {
                "tipo": "Cuadrada",
                "f0": 100,
                "amplitud": 1.0,
                "fs": 150,
                "bits": 16
            },
            "pasos_tutorial": [
                {
                    "titulo": "Señal cuadrada submuestreada",
                    "explicacion": "Las señales cuadradas tienen armónicos que pueden causar aliasing incluso si la fundamental cumple Nyquist.",
                    "concepto_clave": "Armónicos y aliasing",
                    "parametros_cambio": {},
                    "formula": "f_armónico = (2k+1) × f₀"
                }
            ]
        },

        {
            "id": "concepto_snr_bits",
            "categoria": "concepto",
            "nombre": "Relación SNR vs Bits",
            "descripcion": "Cómo cada bit adicional mejora el SNR en ~6 dB",
            "parametros": {
                "tipo": "Senoidal",
                "f0": 1000,
                "amplitud": 1.0,
                "fs": 8000,
                "bits": 8
            },
            "pasos_tutorial": [
                {
                    "titulo": "Ley de los 6 dB por bit",
                    "explicacion": "Cada bit adicional mejora el SNR en aproximadamente 6.02 dB.",
                    "concepto_clave": "SNR teórico",
                    "parametros_cambio": {},
                    "formula": "ΔSNR ≈ 6.02 dB por bit"
                }
            ]
        },

        # CASOS AVANZADOS
        {
            "id": "avanzado_frecuencias_bajas",
            "categoria": "avanzado",
            "nombre": "Análisis de Frecuencias Muy Bajas",
            "descripcion": "Comportamiento del ADC con señales de muy baja frecuencia",
            "parametros": {
                "tipo": "Senoidal",
                "f0": 1,
                "amplitud": 1.0,
                "fs": 10,
                "bits": 8
            },
            "pasos_tutorial": [
                {
                    "titulo": "Señal de 1 Hz",
                    "explicacion": "Con pocas muestras por período, se aprecia claramente el efecto del muestreo.",
                    "concepto_clave": "Muestreo de señales lentas",
                    "parametros_cambio": {},
                    "formula": "Muestras/período = fs/f₀"
                },
                {
                    "titulo": "Incrementar muestreo",
                    "explicacion": "Mayor fs da mejor representación de la señal lenta.",
                    "concepto_clave": "Factor de sobremuestreo",
                    "parametros_cambio": {"fs": 50},
                    "formula": "Factor = fs/(2×f₀)"
                }
            ]
        },

        {
            "id": "avanzado_suma_armonicos",
            "categoria": "avanzado",
            "nombre": "Señal con Múltiples Armónicos",
            "descripcion": "Análisis de señales complejas con varios componentes frecuenciales",
            "parametros": {
                "tipo": "Suma de armonicos",
                "f0": 50,
                "amplitud": 1.0,
                "fs": 1000,
                "bits": 12,
                "n_armonicos": 5
            },
            "pasos_tutorial": [
                {
                    "titulo": "Múltiples componentes",
                    "explicacion": "Señal con 5 armónicos. Cada uno debe cumplir individualmente con Nyquist.",
                    "concepto_clave": "Análisis espectral",
                    "parametros_cambio": {},
                    "formula": "f_armónico = n × f₀"
                },
                {
                    "titulo": "Submuestreo selectivo",
                    "explicacion": "Reducir fs para que algunos armónicos sufran aliasing.",
                    "concepto_clave": "Aliasing selectivo",
                    "parametros_cambio": {"fs": 300},
                    "formula": "Criterio: fs > 2 × f_max"
                }
            ]
        }
    ]
    
    if categoria:
        return [caso for caso in casos if caso["categoria"] == categoria]
    return casos

def obtener_caso_predefinido(caso_id):
    """Obtiene un caso específico por ID"""
    casos = obtener_casos_predefinidos()
    for caso in casos:
        if caso["id"] == caso_id:
            return caso
    return None

def generar_explicacion_paso(paso, parametros):
    """Genera explicación detallada para un paso del tutorial"""
    explicacion = {
        "que_observar": [],
        "parametros_relevantes": {},
        "teoria": ""
    }
    
    concepto = paso.get("concepto_clave", "").lower()
    
    if "nyquist" in concepto:
        fs = parametros.get("fs", 0)
        f0 = parametros.get("f0", 0)
        f_nyquist = fs / 2
        
        explicacion["que_observar"] = [
            f"Frecuencia de la señal: {f0} Hz",
            f"Frecuencia de Nyquist: {f_nyquist} Hz",
            f"Factor de sobremuestreo: {fs/(2*f0):.1f}×",
            "Presencia o ausencia de aliasing en el espectro"
        ]
        
        explicacion["parametros_relevantes"] = {
            "f₀": f"{f0} Hz",
            "fs": f"{fs} Hz",
            "fNyquist": f"{f_nyquist} Hz"
        }
        
    elif "cuantiz" in concepto:
        bits = parametros.get("bits", 0)
        niveles = 2**bits
        snr_teorico = 6.02 * bits + 1.76
        
        explicacion["que_observar"] = [
            f"Número de niveles de cuantización: {niveles}",
            f"Resolución (LSB): {2/niveles:.6f} V",
            "Escalones en la señal cuantizada",
            "Ruido de cuantización en el espectro"
        ]
        
        explicacion["parametros_relevantes"] = {
            "Bits": str(bits),
            "Niveles": f"{niveles:,}",
            "SNR teórico": f"{snr_teorico:.1f} dB"
        }
        
    elif "aliasing" in concepto:
        explicacion["que_observar"] = [
            "Componentes espectrales por encima de Nyquist",
            "Distorsión en la forma de onda reconstruida",
            "Aparición de frecuencias falsas (aliases)"
        ]
        
    return explicacion

def obtener_concepto_teorico(concepto_id):
    """Obtiene información teórica detallada sobre conceptos"""
    conceptos = {
        "teorema_de_nyquist": {
            "titulo": "Teorema de Nyquist-Shannon",
            "definicion": "Para reconstruir perfectamente una señal continua limitada en banda desde sus muestras, la frecuencia de muestreo debe ser al menos el doble de la frecuencia máxima de la señal.",
            "ecuacion": r"f_s \geq 2 \times f_{max}",
            "parametros": {
                "fs": "Frecuencia de muestreo (Hz)",
                "fmax": "Frecuencia máxima de la señal (Hz)",
                "fNyquist": "Frecuencia de Nyquist = fs/2 (Hz)"
            },
            "aplicaciones": ["Audio digital", "Comunicaciones", "Procesamiento de imágenes", "Sistemas de control"],
            "valores_tipicos": {
                "Audio CD": "44.1 kHz (para ~20 kHz de audio)",
                "Telefonía": "8 kHz (para ~4 kHz de voz)",
                "Audio profesional": "96 kHz o superior",
                "Video digital": "13.5 MHz (para ~6.75 MHz)"
            },
            "derivacion": "Basado en la teoría de muestreo de Nyquist-Shannon (1949)",
            "ejemplos": {
                "Bueno": "Señal de 1 kHz muestreada a 8 kHz",
                "Límite": "Señal de 4 kHz muestreada a 8 kHz",
                "Malo": "Señal de 5 kHz muestreada a 8 kHz"
            }
        },
        
        "frecuencia_de_nyquist": {
            "titulo": "Frecuencia de Nyquist",
            "definicion": "La frecuencia máxima que puede ser representada correctamente con una frecuencia de muestreo dada, igual a la mitad de la frecuencia de muestreo.",
            "ecuacion": r"f_{Nyquist} = \frac{f_s}{2}",
            "parametros": {
                "fNyquist": "Frecuencia de Nyquist (Hz)",
                "fs": "Frecuencia de muestreo (Hz)"
            },
            "aplicaciones": ["Diseño de filtros anti-aliasing", "Análisis espectral", "Muestreo óptimo", "Convertidores ADC"],
            "ejemplos": {
                "fs = 44.1 kHz": "fNyquist = 22.05 kHz",
                "fs = 8 kHz": "fNyquist = 4 kHz",
                "fs = 96 kHz": "fNyquist = 48 kHz"
            },
            "importancia": "Define el límite superior del contenido espectral reproducible",
            "relacion_aliasing": "Frecuencias > fNyquist causan aliasing"
        },
        
        "aliasing": {
            "titulo": "Aliasing (Solapamiento Espectral)",
            "definicion": "Distorsión que ocurre cuando una señal se muestrea por debajo de la frecuencia de Nyquist, causando que frecuencias altas aparezcan como frecuencias bajas falsas (aliases).",
            "ecuacion": r"f_{alias} = |f_{señal} - n \times f_s|",
            "parametros": {
                "falias": "Frecuencia alias resultante (Hz)",
                "fseñal": "Frecuencia original de la señal (Hz)",
                "n": "Entero que minimiza |falias|",
                "fs": "Frecuencia de muestreo (Hz)"
            },
            "aplicaciones": ["Filtros anti-aliasing", "Diseño de ADC", "Análisis espectral", "Procesamiento digital"],
            "prevencion": ["Filtros pasa-bajos anti-aliasing", "Sobremuestreo", "Limitación de ancho de banda"],
            "ejemplos": {
                "Ejemplo 1": "fs=8kHz, f=6kHz → falias=2kHz",
                "Ejemplo 2": "fs=1kHz, f=1.3kHz → falias=0.3kHz"
            },
            "efectos": ["Distorsión espectral", "Pérdida de información", "Artefactos audibles"]
        },
        
        "cuantizacion": {
            "titulo": "Cuantización Digital",
            "definicion": "Proceso de mapear valores continuos de amplitud a un conjunto finito de valores discretos, introduciendo ruido de cuantización proporcional al número de bits.",
            "ecuacion": r"SNR = 6.02n + 1.76 \text{ dB}",
            "parametros": {
                "n": "Número de bits del ADC",
                "LSB": "Bit menos significativo = Vref/2ⁿ (V)",
                "DR": "Rango dinámico = 20×log₁₀(2ⁿ) dB",
                "Vref": "Voltaje de referencia del ADC"
            },
            "valores_tipicos": {
                "8 bits": "256 niveles, ~50 dB SNR, 1/256 resolución",
                "16 bits": "65,536 niveles, ~98 dB SNR, calidad CD", 
                "24 bits": "16M+ niveles, ~146 dB SNR, audio profesional",
                "32 bits": "4G+ niveles, ~194 dB SNR, científico"
            },
            "formulas_adicionales": {
                "Resolución": "Δ = Vref/2ⁿ",
                "Error máximo": "±LSB/2",
                "Potencia ruido": "Δ²/12"
            },
            "tipo_errores": ["Error de cuantización", "Ruido térmico", "No linealidad"]
        },
        
        "snr_teorico": {
            "titulo": "SNR Teórico de Cuantización",
            "definicion": "La relación señal-ruido teórica para un conversor ADC ideal, que mejora aproximadamente 6.02 dB por cada bit adicional.",
            "ecuacion": r"SNR = 6.02n + 1.76 \text{ dB}",
            "parametros": {
                "n": "Número de bits del ADC",
                "SNR": "Relación señal-ruido en dB",
                "6.02": "Factor por bit (≈ 20×log₁₀(2))",
                "1.76": "Factor de corrección para señal sinusoidal"
            },
            "derivacion": "Basada en la potencia de una señal sinusoidal vs. ruido de cuantización uniforme",
            "ejemplos_reales": {
                "8 bits": "SNR ≈ 50 dB (calidad telefónica)",
                "16 bits": "SNR ≈ 98 dB (calidad CD)",
                "24 bits": "SNR ≈ 146 dB (límite físico)"
            },
            "limitaciones": ["Solo para ADC ideales", "Ruido térmico real", "No linealidades"]
        },
        
        "armonicos_y_aliasing": {
            "titulo": "Armónicos y Aliasing",
            "definicion": "Las señales no sinusoidales contienen armónicos que pueden causar aliasing incluso si la fundamental cumple el criterio de Nyquist.",
            "ecuacion": r"f_{armónico} = n \times f_0",
            "parametros": {
                "n": "Orden del armónico (1,2,3...)",
                "f0": "Frecuencia fundamental (Hz)",
                "farmónico": "Frecuencia del n-ésimo armónico"
            },
            "ejemplos": {
                "Señal cuadrada": "Armónicos impares: f, 3f, 5f, 7f... con amplitudes 1/n",
                "Señal diente de sierra": "Todos los armónicos: f, 2f, 3f, 4f... con amplitudes 1/n",
                "Señal triangular": "Armónicos impares: f, 3f, 5f... con amplitudes 1/n²"
            },
            "criterio_nyquist": "Cada armónico debe cumplir: f_armónico < fs/2",
            "solucion": "Filtrar armónicos antes del muestreo"
        },
        
        "analisis_espectral": {
            "titulo": "Análisis Espectral (FFT)",
            "definicion": "Descomposición de una señal en sus componentes frecuenciales usando la Transformada Rápida de Fourier (FFT).",
            "ecuacion": r"X(f) = \int_{-\infty}^{\infty} x(t) e^{-j2\pi ft} dt",
            "parametros": {
                "X(f)": "Espectro de frecuencia complejo",
                "x(t)": "Señal en el tiempo",
                "f": "Frecuencia (Hz)",
                "j": "Unidad imaginaria"
            },
            "herramientas": {
                "FFT": "Transformada rápida de Fourier (O(N log N))",
                "DFT": "Transformada discreta de Fourier (O(N²))",
                "Resolución": "Δf = fs/N",
                "Ventanas": "Hanning, Hamming, Blackman"
            },
            "aplicaciones": ["Análisis de distorsión", "Detección de aliasing", "Caracterización de ADC"],
            "interpretacion": {
                "Magnitud": "|X(f)| = amplitud del componente",
                "Fase": "∠X(f) = fase del componente",
                "Potencia": "|X(f)|² = densidad espectral"
            }
        },
        
        "muestreo_de_señales_lentas": {
            "titulo": "Muestreo de Señales Lentas",
            "definicion": "Muestreo de señales de baja frecuencia donde se pueden observar claramente las muestras individuales y el proceso de reconstrucción.",
            "ecuacion": r"N_{muestras} = \frac{f_s}{f_0}",
            "parametros": {
                "Nmuestras": "Número de muestras por período",
                "fs": "Frecuencia de muestreo (Hz)",
                "f0": "Frecuencia de la señal (Hz)"
            },
            "ventajas": [
                "Visualización clara del proceso de muestreo",
                "Menor carga computacional",
                "Fácil comprensión conceptual",
                "Memoria reducida"
            ],
            "aplicaciones": ["Enseñanza de conceptos", "Señales biomédicas", "Monitoreo ambiental"],
            "consideraciones": "Suficientes muestras para caracterizar la señal"
        },
        
        "factor_de_sobremuestreo": {
            "titulo": "Factor de Sobremuestreo (OSR)",
            "definicion": "Relación entre la frecuencia de muestreo real y la frecuencia de Nyquist mínima requerida.",
            "ecuacion": r"OSR = \frac{f_s}{2 \times f_{max}}",
            "parametros": {
                "OSR": "Factor de sobremuestreo (adimensional)",
                "fs": "Frecuencia de muestreo real (Hz)",
                "fmax": "Frecuencia máxima de la señal (Hz)"
            },
            "beneficios": {
                "OSR > 1": "Muestreo seguro sin aliasing",
                "OSR >> 1": "Mejora SNR, facilita filtrado anti-aliasing",
                "OSR = 2-4": "Típico en aplicaciones prácticas",
                "OSR = 64-256": "Convertidores sigma-delta"
            },
            "intercambios": ["Mayor frecuencia vs. mejor calidad", "Costo computacional vs. robustez"]
        },
        
        "aliasing_selectivo": {
            "titulo": "Aliasing Selectivo",
            "definicion": "Fenómeno donde solo algunos armónicos de una señal compleja sufren aliasing mientras otros se mantienen correctos, creando distorsión selectiva.",
            "ecuacion": r"f_{alias,n} = |n \times f_0 - k \times f_s|",
            "parametros": {
                "n": "Orden del armónico",
                "k": "Entero que minimiza |falias|",
                "f0": "Frecuencia fundamental",
                "fs": "Frecuencia de muestreo"
            },
            "efectos": [
                "Distorsión armónica no uniforme",
                "Aparición de frecuencias fantasma",
                "Pérdida de fidelidad espectral",
                "Modulación cruzada"
            ],
            "deteccion": "Análisis espectral antes y después del muestreo",
            "solucion": "Filtrado anti-aliasing apropiado"
        },
        
        "resolucion_adc": {
            "titulo": "Resolución de ADC",
            "definicion": "La precisión con la que un ADC puede discernir entre diferentes niveles de voltaje, determinada por el número de bits.",
            "ecuacion": r"Resolución = \frac{V_{ref}}{2^n}",
            "parametros": {
                "Vref": "Voltaje de referencia del ADC (V)",
                "n": "Número de bits",
                "LSB": "Voltaje del bit menos significativo"
            },
            "ejemplos": {
                "8-bit, 5V": "Resolución = 19.5 mV",
                "12-bit, 3.3V": "Resolución = 0.806 mV",
                "16-bit, 5V": "Resolución = 76.3 μV"
            },
            "impacto": "Determina la mínima señal detectable"
        },
        
        "rango_dinamico": {
            "titulo": "Rango Dinámico",
            "definicion": "La relación entre la señal más grande y más pequeña que puede manejar un sistema ADC, expresada en dB.",
            "ecuacion": r"DR = 20 \times \log_{10}(2^n) = 6.02n \text{ dB}",
            "parametros": {
                "DR": "Rango dinámico (dB)",
                "n": "Número de bits del ADC"
            },
            "valores_tipicos": {
                "8 bits": "48 dB (256:1)",
                "16 bits": "96 dB (65,536:1)",
                "24 bits": "144 dB (16,777,216:1)"
            },
            "aplicaciones": ["Audio de alta fidelidad", "Instrumentación", "Comunicaciones"]
        }
    }
    
    return conceptos.get(concepto_id, None)
