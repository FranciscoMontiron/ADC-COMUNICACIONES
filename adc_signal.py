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
    q = np.round(muestras / paso) * paso
    return q

def filtro_antialias(senal: np.ndarray, fs: float, fc_factor=0.9, orden=5):
    """Aplica filtro pasa-bajo Butterworth con fc configurable."""
    fc = fc_factor * fs / 2  # frecuencia de corte ajustable
    # Normalizar la frecuencia de corte respecto a la frecuencia de Nyquist del filtro
    fc_normalizada = fc / (len(senal) / (len(senal) * (1/fs)) / 2)
    if fc_normalizada >= 1.0:
        fc_normalizada = 0.99  # Evitar errores por frecuencia muy alta
    
    b, a = sp.butter(orden, fc_normalizada, btype='low')
    return sp.filtfilt(b, a, senal)
