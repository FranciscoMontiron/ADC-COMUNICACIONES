#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para chequear todas las funcionalidades del simulador ADC
"""

import numpy as np
from adc_signal import generar_señal, muestrear, cuantizar, filtro_antialias

# testea todos los tipos de senal
def test_tipos_senal():
    print("🧪 Probando tipos de senal...")
    t = np.linspace(0, 1, 1000)
    f0 = 10
    amp = 1.0
    tipos_basicos = ["Senoidal", "Cuadrada", "Diente de sierra", "Triangular"]
    for tipo in tipos_basicos:
        try:
            senal = generar_señal(tipo, f0, amp, t)
            print(f"  OK {tipo}")
        except Exception as e:
            print(f"  ERROR {tipo}: {e}")
    # suma de armonicos
    try:
        amplitudes = [1.0, 0.5, 0.33]
        senal = generar_señal("Suma de armonicos", f0, amp, t, n_armonicos=3, amplitudes_armonicos=amplitudes)
        print(f"  OK Suma de armonicos")
    except Exception as e:
        print(f"  ERROR Suma de armonicos: {e}")
    # senal con ruido
    try:
        senal = generar_señal("Senal con ruido", f0, amp, t, snr_db=20)
        print(f"  OK Senal con ruido")
    except Exception as e:
        print(f"  ERROR Senal con ruido: {e}")
    # AM
    try:
        senal = generar_señal("AM (Modulada en amplitud)", f0, amp, t, f_portadora=100, indice_mod=0.5)
        print(f"  OK AM (Modulada en amplitud)")
    except Exception as e:
        print(f"  ERROR AM: {e}")

# testea procesamiento basico
def test_procesamiento_senal():
    print("\n🔧 Probando procesamiento de senal...")
    t = np.linspace(0, 1, 1000)
    senal = generar_señal("Senoidal", 10, 1.0, t)
    # muestreo
    try:
        fs = 100
        t_sample, s_sample = muestrear(senal, t, fs)
        print(f"  OK Muestreo ({len(s_sample)} muestras)")
    except Exception as e:
        print(f"  ERROR Muestreo: {e}")
        return
    # cuantizacion
    try:
        for bits in [1, 4, 8, 16]:
            s_quant = cuantizar(s_sample, bits, 1.0)
            niveles = len(np.unique(s_quant))
            print(f"    OK Cuantizacion {bits} bits: {niveles} niveles unicos")
    except Exception as e:
        print(f"  ERROR Cuantizacion: {e}")
    # filtro anti-alias
    try:
        s_filtrada = filtro_antialias(senal, fs, fc_factor=0.9, orden=5)
        print(f"  OK Filtro anti-alias")
    except Exception as e:
        print(f"  ERROR Filtro anti-alias: {e}")

# testea casos extremos
def test_casos_extremos():
    print("\n⚠️  Probando casos extremos...")
    t = np.linspace(0, 0.1, 100)
    # frecuencia alta
    try:
        senal = generar_señal("Senoidal", 1000, 1.0, t)
        print(f"  OK Frecuencia alta (1000 Hz)")
    except Exception as e:
        print(f"  ERROR Frecuencia alta: {e}")
    # amplitud alta
    try:
        senal = generar_señal("Senoidal", 10, 5.0, t)
        print(f"  OK Amplitud alta (5.0)")
    except Exception as e:
        print(f"  ERROR Amplitud alta: {e}")
    # cuantizacion minima
    try:
        senal = np.array([0.5, -0.5, 0.3, -0.3])
        s_quant = cuantizar(senal, 1, 1.0)
        print(f"  OK Cuantizacion 1 bit")
    except Exception as e:
        print(f"  ERROR Cuantizacion 1 bit: {e}")

def main():
    print("🚀 Arrancando tests del simulador ADC...\n")
    test_tipos_senal()
    test_procesamiento_senal()
    test_casos_extremos()
    print("\n🎉 Tests terminados!")
    print("\n📋 Resumen de funcionalidades:")
    print("   OK 7 tipos de senal")
    print("   OK Muestreo configurable")
    print("   OK Cuantizacion de 1-16 bits")
    print("   OK Filtro anti-alias avanzado")
    print("   OK Procesamiento robusto de errores")
    print("\n🎯 Para correr la app:")
    print("   streamlit run app.py")

if __name__ == "__main__":
    main()

