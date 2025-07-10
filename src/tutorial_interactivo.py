"""
Sistema de tutorial interactivo para el simulador ADC
====================================================

Gestiona tutoriales paso a paso con explicaciones y visualizaciones.
"""

import streamlit as st
import time
from casos_predefinidos import (obtener_casos_predefinidos, obtener_caso_predefinido, 
                                generar_explicacion_paso, obtener_concepto_teorico)

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
        if 'tutorial_auto_play' not in st.session_state:
            st.session_state.tutorial_auto_play = False
        if 'tutorial_velocidad' not in st.session_state:
            st.session_state.tutorial_velocidad = 3.0
    
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
        st.session_state.tutorial_auto_play = False
    
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
        """Muestra la interfaz del tutorial actual con gráficos compactos y representativos"""
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
        
        # Generar datos para los gráficos con parámetros predefinidos del tutorial
        import numpy as np
        import plotly.graph_objs as go
        from plotly.subplots import make_subplots
        import sys
        import os
        
        # Agregar path para adc_signal si no está disponible
        if 'adc_signal' not in sys.modules:
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
        
        try:
            from adc_signal import generar_señal, muestrear, cuantizar
            
            # ===== CONFIGURACIÓN DE DATOS PARA TUTORIAL =====
            # Parámetros optimizados para visualización educativa
            duracion = 0.08  # Duración más larga para ver varios períodos
            t_analog = np.linspace(0, duracion, 8000)  # Señal analógica suave
            
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
                total_pasos = len(caso['pasos_tutorial'])
                paso_num = st.session_state.tutorial_paso_actual + 1
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
                    st.metric("🎵 f₀", f"{f0} Hz", help="Frecuencia fundamental")
                with col2:
                    st.metric("📊 Amp", f"{amplitud:.1f} V", help="Amplitud de la señal")
                
                # Fila 2: ADC
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🔄 fs", f"{fs} Hz", help="Frecuencia de muestreo")
                with col2:
                    st.metric("🔢 Bits", f"{bits}", help="Resolución del ADC")
                
                # ===== ANÁLISIS AUTOMÁTICO =====
                st.markdown("**📈 Análisis:**")
                
                # Análisis de Nyquist
                f_nyquist = fs / 2
                nyquist_ok = f0 <= f_nyquist
                factor_sobremuestreo = fs / (2 * f0) if f0 > 0 else float('inf')
                
                if nyquist_ok:
                    st.success(f"✅ Nyquist: OK")
                    st.metric("Factor OSR", f"{factor_sobremuestreo:.1f}×", help="Factor de sobremuestreo")
                else:
                    st.error(f"❌ Aliasing!")
                    deficit = 2 * f0 - fs
                    st.metric("Déficit", f"{deficit:.0f} Hz", help="Frecuencia faltante")
                
                # Métricas de cuantización
                niveles = 2**bits
                snr_teorico = 6.02 * bits + 1.76
                resolucion = 2 * amplitud / niveles
                
                st.metric("Niveles", f"{niveles:,}", help="Niveles de cuantización")
                st.metric("SNR teórico", f"{snr_teorico:.0f} dB", help="SNR de cuantización")
                
                # ===== FÓRMULA DEL PASO =====
                if 'formula' in paso_actual and paso_actual['formula']:
                    st.markdown("**📐 Fórmula clave:**")
                    st.code(paso_actual['formula'], language="text")
            
            # ===== COLUMNA DE GRÁFICOS =====
            with col_graficos:
                # ===== GRÁFICO PRINCIPAL: SEÑALES EN TIEMPO =====
                fig_main = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=['🎵 Señal y Muestras', '📊 Espectro de Frecuencia', 
                                   '🔢 Señal Cuantizada', '📈 Comparación Niveles'],
                    specs=[[{"secondary_y": False}, {"secondary_y": False}],
                           [{"secondary_y": False}, {"secondary_y": False}]],
                    vertical_spacing=0.15,
                    horizontal_spacing=0.12
                )
                
                # --- Subplot 1: Señal original y muestras ---
                # Señal analógica (solo algunos puntos para claridad)
                indices_plot = np.linspace(0, len(t_analog)-1, 2000, dtype=int)
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
                
                # Anotaciones según el concepto
                concepto = paso_actual.get('concepto_clave', '').lower()
                if 'nyquist' in concepto:
                    # Marcar el período de la señal
                    if f0 > 0:
                        periodo_ms = 1000 / f0
                        fig_main.add_vline(x=periodo_ms, line_dash="dash", line_color="green", 
                                         row=1, col=1, annotation_text=f"T={periodo_ms:.1f}ms")
                
                # --- Subplot 2: Espectro de frecuencia ---
                if len(s_analog) > 100:
                    N = len(s_analog)
                    fft_orig = np.fft.fft(s_analog)
                    freq_orig = np.fft.fftfreq(N, t_analog[1] - t_analog[0])
                    
                    # Solo frecuencias positivas hasta 2*fs para mostrar aliasing
                    max_freq = min(2 * fs, 1000)  # Limitar para mejor visualización
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
                    
                    # Marcar Nyquist
                    fig_main.add_vline(x=f_nyquist, line_dash="dash", line_color="red", 
                                     row=1, col=2, annotation_text=f"Nyquist: {f_nyquist:.0f}Hz")
                    
                    if not nyquist_ok:
                        # Marcar frecuencia de aliasing
                        f_alias = abs(f0 - fs) if f0 > f_nyquist else None
                        if f_alias and f_alias <= max_freq:
                            fig_main.add_vline(x=f_alias, line_dash="dot", line_color="orange",
                                             row=1, col=2, annotation_text=f"Alias: {f_alias:.0f}Hz")
                
                # --- Subplot 3: Señal cuantizada ---
                fig_main.add_trace(
                    go.Scatter(
                        x=t_sample*1000, 
                        y=s_quant,
                        mode='markers+lines',
                        name='Cuantizada',
                        marker=dict(color='red', size=5, symbol='square'),
                        line=dict(color='red', width=1),
                        showlegend=False
                    ), row=2, col=1
                )
                
                # Añadir líneas de niveles de cuantización si bits es bajo
                if bits <= 4:
                    for nivel in np.linspace(-amplitud, amplitud, niveles+1):
                        fig_main.add_hline(y=nivel, line_dash="dot", line_color="gray", 
                                         opacity=0.5, row=2, col=1)
                
                # --- Subplot 4: Comparación de resoluciones ---
                # Mostrar cómo se vería con diferentes bits
                bits_comparacion = [1, 4, 8, bits] if bits not in [1, 4, 8] else [1, 4, 8, 16]
                colores = ['red', 'orange', 'green', 'blue']
                
                for i, b in enumerate(bits_comparacion):
                    if b <= 16:  # Evitar calcular demasiados niveles
                        s_temp = cuantizar(s_sample[:50], b, amplitud)  # Solo primeras 50 muestras
                        fig_main.add_trace(
                            go.Scatter(
                                x=t_sample[:50]*1000,
                                y=s_temp,
                                mode='markers',
                                name=f'{b}-bit',
                                marker=dict(color=colores[i], size=4),
                                opacity=0.7,
                                showlegend=False
                            ), row=2, col=2
                        )
                
                # Configurar layout de subplots
                fig_main.update_xaxes(title_text="Tiempo [ms]", row=1, col=1)
                fig_main.update_xaxes(title_text="Frecuencia [Hz]", row=1, col=2)
                fig_main.update_xaxes(title_text="Tiempo [ms]", row=2, col=1)
                fig_main.update_xaxes(title_text="Tiempo [ms]", row=2, col=2)
                
                fig_main.update_yaxes(title_text="Amplitud [V]", row=1, col=1)
                fig_main.update_yaxes(title_text="Magnitud [dB]", row=1, col=2)
                fig_main.update_yaxes(title_text="Amplitud [V]", row=2, col=1)
                fig_main.update_yaxes(title_text="Amplitud [V]", row=2, col=2)
                
                fig_main.update_layout(
                    title=f"📊 {tipo} - {f0} Hz @ {fs} Hz, {bits}-bit",
                    template="plotly_white",
                    height=500,
                    showlegend=False,
                    margin=dict(l=50, r=50, t=80, b=50)
                )
                
                # Destacar aspectos específicos según el concepto
                if 'aliasing' in concepto and not nyquist_ok:
                    fig_main.add_annotation(
                        x=0.5, y=0.9, xref="paper", yref="paper",
                        text="⚠️ DETECTADO ALIASING",
                        showarrow=False,
                        font=dict(size=16, color="red"),
                        bgcolor="rgba(255,255,255,0.8)",
                        bordercolor="red"
                    )
                elif 'cuantiz' in concepto:
                    fig_main.add_annotation(
                        x=0.5, y=0.1, xref="paper", yref="paper",
                        text=f"🔢 {niveles} niveles de cuantización",
                        showarrow=False,
                        font=dict(size=12, color="blue"),
                        bgcolor="rgba(255,255,255,0.8)",
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
                    if not nyquist_ok:
                        st.warning(f"⚠️ **Análisis de Aliasing**: La frecuencia de la señal ({f0} Hz) supera la frecuencia de Nyquist ({f_nyquist} Hz). Observa cómo aparecen componentes espectrales falsas.")
                    
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

    # ...existing code...

def mostrar_selector_casos():
    """Muestra el selector de casos predefinidos"""
    st.subheader("📚 Casos Predefinidos y Tutoriales")
    
    # Obtener casos por categoría
    casos_tutorial = obtener_casos_predefinidos("tutorial")
    casos_concepto = obtener_casos_predefinidos("concepto") 
    casos_avanzado = obtener_casos_predefinidos("avanzado")
    
    # Tabs por categoría
    tab_tutorial, tab_concepto, tab_avanzado = st.tabs([
        "🎓 Tutoriales Básicos", 
        "💡 Conceptos Clave", 
        "🚀 Casos Avanzados"
    ])
    
    caso_seleccionado = None
    
    with tab_tutorial:
        st.write("**Perfecto para comenzar** - Explicaciones paso a paso")
        for caso in casos_tutorial:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{caso['nombre']}**")
                st.caption(caso['descripcion'])
            with col2:
                st.metric("Pasos", len(caso['pasos_tutorial']))
            with col3:
                if st.button("▶️ Iniciar", key=f"tutorial_{caso['id']}"):
                    caso_seleccionado = caso['id']
    
    with tab_concepto:
        st.write("**Conceptos específicos** - Demostraciones enfocadas")
        for caso in casos_concepto:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{caso['nombre']}**")
                st.caption(caso['descripcion'])
            with col2:
                if 'pasos_tutorial' in caso:
                    st.metric("Pasos", len(caso['pasos_tutorial']))
            with col3:
                if st.button("▶️ Ejecutar", key=f"concepto_{caso['id']}"):
                    caso_seleccionado = caso['id']
    
    with tab_avanzado:
        st.write("**Casos complejos** - Para usuarios experimentados")
        for caso in casos_avanzado:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{caso['nombre']}**")
                st.caption(caso['descripcion'])
            with col2:
                if 'pasos_tutorial' in caso:
                    st.metric("Pasos", len(caso['pasos_tutorial']))
            with col3:
                if st.button("🔬 Analizar", key=f"avanzado_{caso['id']}"):
                    caso_seleccionado = caso['id']
    
    return caso_seleccionado

def mostrar_modal_tutorial():
    """Muestra el modal del tutorial activo"""
    if not st.session_state.get('tutorial_activo', False):
        return None
    
    tutorial_manager = TutorialManager()
    paso_actual = tutorial_manager.obtener_paso_actual()
    caso = obtener_caso_predefinido(st.session_state.tutorial_caso_id)
    
    if not paso_actual or not caso:
        return None
    
    # Modal container
    with st.container():
        # Header del modal
        st.markdown("### 🎓 Tutorial Activo")
        
        col1, col2, col3 = st.columns([6, 1, 1])
        with col1:
            st.markdown(f"**{caso['nombre']}**")
            progress = (st.session_state.tutorial_paso_actual + 1) / len(caso['pasos_tutorial'])
            st.progress(progress)
            st.caption(f"Paso {st.session_state.tutorial_paso_actual + 1} de {len(caso['pasos_tutorial'])}")
        
        with col2:
            if st.button("⏸️" if st.session_state.get('tutorial_auto_play', False) else "▶️"):
                st.session_state.tutorial_auto_play = not st.session_state.get('tutorial_auto_play', False)
                if st.session_state.tutorial_auto_play:
                    st.rerun()
        
        with col3:
            if st.button("❌"):
                tutorial_manager.detener_tutorial()
                st.rerun()
        
        st.markdown("---")
        
        # Contenido principal del paso
        col_content, col_controls = st.columns([3, 1])
        
        with col_content:
            # Título del paso
            st.markdown(f"#### {paso_actual['titulo']}")
            
            # Explicación principal
            st.write(paso_actual['explicacion'])
            
            # Concepto clave
            with st.expander(f"💡 {paso_actual['concepto_clave']}", expanded=True):
                concepto = obtener_concepto_teorico(paso_actual['concepto_clave'].lower().replace(' ', '_'))
                if concepto:
                    st.write(f"**{concepto.get('definicion', 'No disponible')}**")
                    if 'ecuacion' in concepto:
                        st.latex(concepto['ecuacion'])
                else:
                    st.write("Información teórica no disponible.")
            
            # Fórmula del paso
            if 'formula' in paso_actual and paso_actual['formula']:
                st.code(paso_actual['formula'], language="text")
            
            # Qué observar
            explicacion_detallada = generar_explicacion_paso(
                paso_actual, 
                tutorial_manager.obtener_parametros_paso()
            )
            
            if explicacion_detallada['que_observar']:
                st.markdown("**🔍 Qué observar:**")
                for item in explicacion_detallada['que_observar']:
                    st.write(f"• {item}")
        
        with col_controls:
            st.markdown("#### 🎮 Controles")
            
            # Controles de navegación
            col_prev, col_next = st.columns(2)
            with col_prev:
                if st.button("⬅️", disabled=st.session_state.tutorial_paso_actual == 0):
                    tutorial_manager.paso_anterior()
                    st.rerun()
            
            with col_next:
                es_ultimo = st.session_state.tutorial_paso_actual >= len(caso['pasos_tutorial']) - 1
                if st.button("➡️", disabled=es_ultimo):
                    if not tutorial_manager.siguiente_paso():
                        st.success("🎉 ¡Tutorial completado!")
                        tutorial_manager.detener_tutorial()
                    st.rerun()
            
            # Lista de pasos
            st.markdown("**📋 Progreso:**")
            for i, paso in enumerate(caso['pasos_tutorial']):
                emoji = "✅" if i in st.session_state.tutorial_pasos_completados else "🔄" if i == st.session_state.tutorial_paso_actual else "⭕"
                st.write(f"{emoji} {i+1}. {paso['titulo']}")
    
    # Auto-play logic
    if st.session_state.get('tutorial_auto_play', False):
        time.sleep(st.session_state.tutorial_velocidad)
        if not tutorial_manager.siguiente_paso():
            st.success("🎉 ¡Tutorial completado!")
            tutorial_manager.detener_tutorial()
        st.rerun()
    
    return tutorial_manager.obtener_parametros_paso()

# Funciones auxiliares
def inicializar_tutorial_manager():
    """Inicializa el manager de tutoriales"""
    if 'tutorial_manager' not in st.session_state:
        st.session_state.tutorial_manager = TutorialManager()
    return st.session_state.tutorial_manager

def esta_tutorial_activo():
    """Verifica si hay un tutorial activo"""
    return st.session_state.get('tutorial_activo', False)

def obtener_parametros_tutorial():
    """Obtiene los parámetros del tutorial actual"""
    if esta_tutorial_activo():
        manager = TutorialManager()
        return manager.obtener_parametros_paso()
    return None
