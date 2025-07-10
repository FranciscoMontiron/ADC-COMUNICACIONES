import numpy as np
from scipy import signal as sp

def generar_señal(tipo: str, freq: float, amp: float, t: np.ndarray, n_armonicos=3, amplitudes_armonicos=None, snr_db=20, f_portadora=None, indice_mod=None) -> np.ndarray:
    """Devuelve la señal analogica continua en el vector de tiempos t."""
    if tipo == "Senoidal":
        return amp * np.sin(2*np.pi*freq*t)
    elif tipo == "Cuadrada":
        return amp * sp.square(2*np.pi*freq*t)
    elif tipo == "Diente de sierra":
        return amp * sp.sawtooth(2*np.pi*freq*t)
    elif tipo == "Triangular":
        return amp * sp.sawtooth(2*np.pi*freq*t, 0.5)
    elif tipo == "Suma de armonicos":
        senal = np.zeros_like(t)
        if amplitudes_armonicos is None:
            # Usar amplitudes por defecto si no se especifican
            amplitudes_armonicos = [1.0/(i+1) for i in range(n_armonicos)]
        for i, a in enumerate(amplitudes_armonicos):
            senal += a * np.sin(2*np.pi*freq*(i+1)*t)
        return amp * senal
    elif tipo == "Señal con ruido":
        senal = amp * np.sin(2*np.pi*freq*t)
        power_senal = np.mean(senal**2)
        power_ruido = power_senal / (10**(snr_db / 10))
        ruido = np.sqrt(power_ruido) * np.random.normal(size=t.shape)
        return senal + ruido
    elif tipo == "AM (Modulada en amplitud)":
        senal = (1 + indice_mod * np.sin(2*np.pi*freq*t)) * np.cos(2*np.pi*f_portadora*t)
        return amp * senal
    else:
        raise ValueError("Tipo de señal no soportado")

def muestrear(senal: np.ndarray, t: np.ndarray, fs: float):
    """Toma muestras de la señal a frecuencia fs."""
    Ts = 1/fs
    indices = np.arange(t[0], t[-1], Ts)
    muestras = np.interp(indices, t, senal)
    return indices, muestras

def cuantizar(muestras: np.ndarray, bits: int, amp: float):
    """Cuantiza la señal a un numero de niveles 2^bits centrados en cero."""
    N = 2**bits
    paso = 2*amp / N
    
    # Cuantización con límites para evitar valores fuera del rango
    q = np.round(muestras / paso) * paso
    
    # Limitar los valores al rango válido
    q = np.clip(q, -amp, amp - paso)
    
    return q

def filtro_antialias(senal: np.ndarray, fs: float, fc_factor=0.9, orden=5):
    """Aplica filtro pasa-bajo Butterworth con fc configurable."""
    try:
        fc = fc_factor * fs / 2  # frecuencia de corte ajustable
        
        # Calcular la frecuencia de Nyquist basada en la frecuencia de muestreo
        nyquist = fs / 2
        fc_normalizada = fc / nyquist
        
        # Asegurar que la frecuencia normalizada esté en el rango válido
        if fc_normalizada >= 1.0:
            fc_normalizada = 0.99
        elif fc_normalizada <= 0:
            fc_normalizada = 0.01
            
        b, a = sp.butter(orden, fc_normalizada, btype='low')
        senal_filtrada = sp.filtfilt(b, a, senal)
        return senal_filtrada
    except Exception as e:
        print(f"Error en filtro anti-alias: {e}")
        return senal  # Devolver señal original si hay error

def calcular_error_cuantizacion(senal_original: np.ndarray, senal_cuantizada: np.ndarray):
    """Calcula métricas de error de cuantización."""
    error_absoluto = np.abs(senal_original - senal_cuantizada)
    error_cuadratico_medio = np.mean((senal_original - senal_cuantizada)**2)
    snr_cuantizacion = 10 * np.log10(np.mean(senal_original**2) / error_cuadratico_medio)
    
    return {
        'error_cuadratico_medio': error_cuadratico_medio,
        'error_maximo': np.max(error_absoluto),
        'snr_cuantizacion_db': snr_cuantizacion
    }

def reconstruir_senal(muestras: np.ndarray, t_muestras: np.ndarray, t_reconstruccion: np.ndarray, metodo='lineal'):
    """Reconstruye la señal continua a partir de muestras discretas."""
    if metodo == 'lineal':
        return np.interp(t_reconstruccion, t_muestras, muestras)
    elif metodo == 'sinc':
        # Reconstrucción ideal usando interpolación sinc (para demostración)
        fs = 1 / (t_muestras[1] - t_muestras[0])
        senal_reconstruida = np.zeros_like(t_reconstruccion)
        
        for i, muestra in enumerate(muestras):
            t_shift = t_reconstruccion - t_muestras[i]
            sinc_vals = np.sinc(fs * t_shift)
            senal_reconstruida += muestra * sinc_vals
            
        return senal_reconstruida
    else:
        raise ValueError("Método de reconstrucción no soportado")

def analizar_aliasing(senal: np.ndarray, t: np.ndarray, fs: float):
    """Analiza si hay aliasing en la señal."""
    # Calcular FFT
    fft_senal = np.fft.fft(senal)
    freqs = np.fft.fftfreq(len(senal), t[1] - t[0])
    
    # Frecuencia de Nyquist
    f_nyquist = fs / 2
    
    # Encontrar energía por encima de Nyquist
    idx_nyquist = np.where(np.abs(freqs) > f_nyquist)[0]
    energia_total = np.sum(np.abs(fft_senal)**2)
    energia_aliasing = np.sum(np.abs(fft_senal[idx_nyquist])**2)
    
    ratio_aliasing = energia_aliasing / energia_total if energia_total > 0 else 0
    
    return {
        'hay_aliasing': ratio_aliasing > 0.01,  # 1% de energía como umbral
        'ratio_aliasing': ratio_aliasing,
        'f_nyquist': f_nyquist,
        'energia_aliasing': energia_aliasing
    }
