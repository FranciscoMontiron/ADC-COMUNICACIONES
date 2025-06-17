import streamlit as st
import numpy as np
import plotly.graph_objs as go
from adc_signal import generar_señal, muestrear, cuantizar, filtro_antialias
from database import guardar_senal, inicializarBaseDeDatos, obtener_senal

inicializarBaseDeDatos()
# configuro la pagina y meto un poco de css para que quede mas fachero
st.set_page_config(
    page_title="Simulador ADC",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# css para que no se vea tan feo
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    .stSelectbox > div > div > select {
        background-color: #f0f2f6;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e9ecef;
    }
    .warning-box {
        color:black;
        font-weight: bold;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("📡 Simulador de Conversion de Senales (ADC)")
st.markdown("---")

# sidebar para los parametros
st.sidebar.header("⚙️ Configuracion de Senal")

# parametros de la señal analogica
st.sidebar.subheader("Senal de Entrada")
tipo = st.sidebar.selectbox(
    "Tipo de señal", 
    ["Senoidal", "Cuadrada", "Diente de sierra", "Triangular", "Suma de armonicos", "Señal con ruido", "AM (Modulada en amplitud)"],
    help="Tipo de onda analogica a simular. Senoidal: la clasica, Cuadrada: dos niveles, Diente de sierra: sube y baja lineal."
)

f0 = st.sidebar.slider(
    "Frecuencia fundamental (Hz)", 
    min_value=1.0, max_value=1000.0, value=50.0, step=1.0,
    help="Frecuencia de la señal original en Hz. Si es muy alta respecto al muestreo, aparece aliasing."
)
amp = st.sidebar.slider(
    "Amplitud", 
    min_value=0.1, max_value=5.0, value=1.0, step=0.1,
    help="Valor maximo de la señal analogica. Afecta el rango de cuantizacion."
)

n_armonicos = 0
amplitudes_armonicos = []
snr_db = 0
f_portadora = 0
indice_mod = 0
orden_filtro = 0
fc_factor = 0
# parametros extra segun el tipo de señal
if tipo == "Suma de armonicos":
    n_armonicos = st.sidebar.slider("Numero de armonicos", min_value=2, max_value=10, value=3)
    for i in range(n_armonicos):
        amp_harm = st.sidebar.slider(
            f"Amplitud armonico {i+1}", 
            min_value=0.0, max_value=1.0, value=1.0/(i+1), step=0.1,
            help="Amplitud del armonico. Cambia la forma de la señal compuesta."
        )
        amplitudes_armonicos.append(amp_harm)
elif tipo == "Señal con ruido":
    snr_db = st.sidebar.slider(
        "SNR (dB)", 
        min_value=0, max_value=50, value=20,
        help="Relacion señal-ruido en dB. Mas alto = menos ruido."
    )
elif tipo == "AM (Modulada en amplitud)":
    f_portadora = st.sidebar.slider(
        "Frecuencia portadora (Hz)", 
        min_value=100.0, max_value=2000.0, value=500.0, step=10.0,
        help="Frecuencia de la portadora en la AM."
    )
    indice_mod = st.sidebar.slider(
        "Indice de modulacion", 
        min_value=0.1, max_value=1.0, value=0.5, step=0.1,
        help="Indice de modulacion de la AM. Cuanto modula la portadora."
    )

st.sidebar.markdown("---")

# parametros del ADC
st.sidebar.subheader("Conversion ADC")
fs = st.sidebar.slider(
    "Tasa de muestreo (Hz)", 
    min_value=1.0, max_value=5000.0, value=200.0, step=1.0,
    help="Cuantas muestras por segundo se toman. Si es menor que 2*f0, hay aliasing (no se cumple Nyquist)."
)
bits = st.sidebar.selectbox(
    "Cuantizacion (bits)", 
    [1,2,3,4,6,8,10,12,16],
    help="Cuantos bits para cada muestra. Mas bits = mas niveles y menos error."
)

st.sidebar.markdown("---")

# opciones de visualizacion y filtrado
st.sidebar.subheader("Opciones")
mostrar_alias = st.sidebar.checkbox(
    "Mostrar avisos de aliasing", 
    value=True,
    help="Si esta activado, la app avisa si la tasa de muestreo no cumple Nyquist."
)
aplicar_filtro = st.sidebar.checkbox(
    "Aplicar filtro anti-alias", 
    value=False,
    help="Si se activa, se filtra la señal antes de muestrear para evitar aliasing."
)

if aplicar_filtro:
    orden_filtro = st.sidebar.slider(
        "Orden del filtro", 
        min_value=1, max_value=10, value=5,
        help="Orden del filtro pasa-bajos. Mas orden = filtro mas fuerte."
    )
    fc_factor = st.sidebar.slider(
        "Factor de freq. de corte (x fs/2)", 
        min_value=0.1, max_value=1.0, value=0.9, step=0.1,
        help="Frecuencia de corte del filtro como un factor de fs/2. Menor que 1."
    )

# armo los parametros extra para la funcion de señal
kwargs = {}
if tipo == "Suma de armonicos":
    kwargs = {"n_armonicos": n_armonicos, "amplitudes_armonicos": amplitudes_armonicos}
elif tipo == "Señal con ruido":
    kwargs = {"snr_db": snr_db}
elif tipo == "AM (Modulada en amplitud)":
    kwargs = {"f_portadora": f_portadora, "indice_mod": indice_mod}

# genero la señal analogica con mucha resolucion (como si fuera continua)
dur = 0.1  # segundos
t_analog = np.linspace(0, dur, 20000)
s_analog = generar_señal(tipo, f0, amp, t_analog, **kwargs)

# si se marca, aplico el filtro anti-alias antes de muestrear
if aplicar_filtro:
    fc = fc_factor * fs / 2
    from scipy import signal as sp
    b, a = sp.butter(orden_filtro, fc/(len(t_analog)/dur/2), btype='low')
    s_analog_filtrada = sp.filtfilt(b, a, s_analog)
else:
    s_analog_filtrada = s_analog.copy()

# hago el muestreo
t_sample, s_sample = muestrear(s_analog_filtrada, t_analog, fs)

# cuantizo la señal muestreada
s_quant = cuantizar(s_sample, bits, amp)

# metricas principales
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Frecuencia Nyquist", f"{fs/2:.1f} Hz")
with col2:
    nyquist_ratio = fs / (2 * f0)
    st.metric("Factor Nyquist", f"{nyquist_ratio:.2f}")
with col3:
    niveles_cuant = 2**bits
    st.metric("Niveles de cuantizacion", niveles_cuant)
with col4:
    resolucion = 2*amp / niveles_cuant
    st.metric("Resolucion ADC", f"{resolucion:.4f} V")

st.markdown("---")

# grafico la señal analogica
fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=t_analog*1000, y=s_analog, 
    mode='lines', name='Original', 
    line=dict(color='blue', width=2)
))

if aplicar_filtro:
    fig1.add_trace(go.Scatter(
        x=t_analog*1000, y=s_analog_filtrada, 
        mode='lines', name='Filtrada', 
        line=dict(color='green', width=2, dash='dash')
    ))

fig1.update_layout(
    title="📊 Señal Analogica", 
    xaxis_title="Tiempo [ms]", 
    yaxis_title="Amplitud [V]",
    template="plotly_white",
    hovermode='x unified'
)

# grafico la señal digitalizada
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
    title="🔢 Señal Digitalizada (ADC)", 
    xaxis_title="Tiempo [ms]", 
    yaxis_title="Amplitud [V]",
    template="plotly_white",
    hovermode='x unified'
)

# muestro las dos graficas
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    st.plotly_chart(fig2, use_container_width=True)

# analisis espectral
st.markdown("### 📈 Analisis Espectral")

# fft de la señal original
fft_orig = np.fft.fft(s_analog)
freq_orig = np.fft.fftfreq(len(s_analog), t_analog[1] - t_analog[0])

# fft de la señal cuantizada (interpolada para comparar)
fft_quant = np.fft.fft(np.interp(t_analog, t_sample, s_quant))

fig_fft = go.Figure()
fig_fft.add_trace(go.Scatter(
    x=freq_orig[:len(freq_orig)//2], 
    y=np.abs(fft_orig)[:len(fft_orig)//2],
    mode='lines', name='Original',
    line=dict(color='blue')
))
fig_fft.add_trace(go.Scatter(
    x=freq_orig[:len(freq_orig)//2], 
    y=np.abs(fft_quant)[:len(fft_quant)//2],
    mode='lines', name='Cuantizada',
    line=dict(color='red', dash='dash')
))

# linea vertical en frecuencia de Nyquist
fig_fft.add_vline(
    x=fs/2, line_dash="dash", line_color="green",
    annotation_text="Frecuencia de Nyquist"
)

fig_fft.update_layout(
    title="Espectro de Frecuencia",
    xaxis_title="Frecuencia [Hz]",
    yaxis_title="Magnitud",
    template="plotly_white",
    xaxis=dict(range=[0, min(1000, fs*2)])
)

st.plotly_chart(fig_fft, use_container_width=True)

# avisos y analisis
st.markdown("### ⚠️ Analisis de Calidad")

if mostrar_alias:
    if fs < 2*f0:
        st.markdown(
            '<div class="warning-box">'
            '⚠️ <strong>ALIASING DETECTADO!</strong><br>'
            f'La frecuencia de muestreo ({fs} Hz) es menor que el doble de la frecuencia fundamental ({2*f0} Hz). '
            'Esto viola el teorema de Nyquist y va a distorsionar la señal reconstruida.'
            '</div>', 
            unsafe_allow_html=True
        )
    else:
        st.success(f"✅ Sin aliasing: fs ({fs} Hz) >= 2xf0 ({2*f0} Hz). Se cumple Nyquist.")

# error de cuantizacion
error_cuant = np.mean((s_sample - s_quant)**2)
st.info(f"📊 Error cuadratico medio de cuantizacion: {error_cuant:.6f}")

# info extra segun el tipo de señal
if tipo == "Suma de armonicos":
    st.info(f"🎵 Señal compuesta: {n_armonicos} armonicos con amplitudes {[f'{a:.2f}' for a in amplitudes_armonicos]}")
elif tipo == "Señal con ruido":
    st.info(f"🔊 Señal con ruido: SNR = {snr_db} dB")
elif tipo == "AM (Modulada en amplitud)":
    st.info(f"📡 Mod AM: Portadora = {f_portadora} Hz, Indice = {indice_mod}")

# funcion para guardar la señal en la base de datos
def guardar_senal_callback():
    if(guardar_senal(
        tipo,
        f0,
        amp,
        fs,
        bits,
        mostrar_alias,
        aplicar_filtro,
        n_armonicos,
        amplitudes_armonicos,
        snr_db,
        f_portadora,
        indice_mod,
        orden_filtro,
        fc_factor,
    )):
        st.success("Señal guardada correctamente")
    else:
        st.error("Error al guardar la señal")

st.sidebar.button("Guardar señal", on_click=guardar_senal_callback)