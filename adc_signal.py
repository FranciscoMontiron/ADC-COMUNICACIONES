# signal.py
import numpy as np
from scipy import signal as sp

def generar_señal(tipo: str, freq: float, amp: float, t: np.ndarray) -> np.ndarray:
    """Devuelve la señal analógica continua en el vector de tiempos t."""
    if tipo == "Senoidal":
        return amp * np.sin(2*np.pi*freq*t)
    elif tipo == "Cuadrada":
        return amp * sp.square(2*np.pi*freq*t)
    elif tipo == "Diente de sierra":
        return amp * sp.sawtooth(2*np.pi*freq*t)
    else:
        raise ValueError("Tipo de señal no soportado")

def muestrear(señal: np.ndarray, t: np.ndarray, fs: float):
    """Toma muestras de la señal a frecuencia fs."""
    Ts = 1/fs
    indices = np.arange(t[0], t[-1], Ts)
    muestras = np.interp(indices, t, señal)
    return indices, muestras

def cuantizar(muestras: np.ndarray, bits: int, amp: float):
    """Cuantiza la señal a un número de niveles 2^bits centrados en cero."""
    N = 2**bits
    paso = 2*amp / N
    q = np.round(muestras / paso) * paso
    return q

def filtro_antialias(señal: np.ndarray, fs: float, orden=5):
    """Aplica filtro pasa‐bajo Butterworth con fc = fs/2."""
    fc = fs/2  # frecuencia de corte
    b, a = sp.butter(orden, fc/(fs*2), btype='low')
    return sp.filtfilt(b, a, señal)
