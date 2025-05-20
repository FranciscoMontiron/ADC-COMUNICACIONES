# app.py
import streamlit as st
import numpy as np
import plotly.graph_objs as go
from adc_signal import generar_señal, muestrear, cuantizar, filtro_antialias

st.title("Simulador de Conversion de Senales (ADC)")

# aca van los parametros de la senal analogica
col1, col2 = st.columns(2)
with col1:
    tipo = st.selectbox("Tipo de senal", ["Senoidal", "Cuadrada", "Diente de sierra"])
    f0   = st.slider("Frecuencia (Hz)", min_value=1.0, max_value=5000.0, value=50.0, step=1.0)
    amp  = st.slider("Amplitud", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
with col2:
    fs   = st.slider("Tasa de muestreo (Hz)", min_value=1.0, max_value=10000.0, value=200.0, step=1.0)
    bits = st.selectbox("Cuantizacion (bits)", [1,2,3,4,8,16])
    mostrar_alias = st.checkbox("Mostrar aliasing", value=True)
    aplicar_filtro = st.checkbox("Aplicar filtro antialias", value=False)

# genero la senal analogica con mucha resolucion
# (o sea, como si fuera continua)
dur = 0.05  # segundos
t_analog = np.linspace(0, dur, 10000)
s_analog = generar_señal(tipo, f0, amp, t_analog)

# hago el muestreo
t_sample, s_sample = muestrear(s_analog, t_analog, fs)

# si se marca, aplico el filtro antialias antes de muestrear
if aplicar_filtro:
    s_analog = filtro_antialias(s_analog, fs)

# cuantizo la senal muestreada
s_quant = cuantizar(s_sample, bits, amp)

# grafico la senal analogica
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=t_analog, y=s_analog, mode='lines', name='Analogica'))
fig1.update_layout(title="Senal Analogica", xaxis_title="Tiempo [s]", yaxis_title="Amplitud")

# grafico la senal digitalizada (muestras y cuantizada)
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=t_sample, y=s_sample, mode='markers+lines', name='Muestras'))
fig2.add_trace(go.Scatter(x=t_sample, y=s_quant, mode='markers', name='Cuantizada'))
fig2.update_layout(title="Senal Digitalizada", xaxis_title="Tiempo [s]", yaxis_title="Amplitud")

# muestro las dos graficas al lado
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(fig1, use_container_width=True)
with c2:
    st.plotly_chart(fig2, use_container_width=True)

# aviso si hay aliasing segun Nyquist
if mostrar_alias:
    if fs < 2*f0:
        st.error(
            "Ojo! Hay aliasing porque fs < 2*f0. La senal se va a ver deformada porque no se cumple Nyquist."
        )
    else:
        st.success("Todo ok, fs >= 2*f0: se cumple Nyquist.")
