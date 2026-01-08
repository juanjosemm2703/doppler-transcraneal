import streamlit as st
import pandas as pd
import io

# Configuración de página
st.set_page_config(page_title="DTC Pro - Análisis Hemodinámico", layout="wide")

# --- Base de Datos de Referencia (Valores promedio adultos) ---
# Fuentes: Aaslid, Ringelstein, et al.
REFERENCIAS = {
    "ACMd (Derecha)": {"vps": 110, "vfd": 40, "vm": 62},
    "ACMi (Izquierda)": {"vps": 110, "vfd": 40, "vm": 62},
    "ACAd (Derecha)": {"vps": 90, "vfd": 35, "vm": 50},
    "ACAi (Izquierda)": {"vps": 90, "vfd": 35, "vm": 50},
    "ACPd (Derecha)": {"vps": 70, "vfd": 25, "vm": 40},
    "ACPi (Izquierda)": {"vps": 70, "vfd": 25, "vm": 40},
    "Basilar": {"vps": 70, "vfd": 25, "vm": 40},
    "ACId (Sifón/Extracraneal)": {"vps": 80, "vfd": 30, "vm": 45},
    "ACIi (Sifón/Extracraneal)": {"vps": 80, "vfd": 30, "vm": 45},
}

# Límites generales de normalidad para índices
NORMAL_IP = (0.6, 1.1)
NORMAL_IR = (0.4, 0.7)
NORMAL_LINDEGAARD = (0.0, 3.0)

st.title("🧠 DTC Pro: Analizador de Doppler Transcraneal")
st.markdown("Cálculo automático con validación frente a valores de referencia clínicos.")

# Inicializar almacenamiento
if 'df_resultados' not in st.session_state:
    st.session_state.df_resultados = pd.DataFrame(columns=[
        "Arteria", "VPS", "VFD", "Vm", "IP", "IR", "Lindegaard", "Estado"
    ])

# --- Panel Lateral: Entrada de Datos ---
with st.sidebar:
    st.header("📥 Ingreso de Mediciones")
    arteria_sel = st.selectbox("Seleccione Arteria:", list(REFERENCIAS.keys()))
    vps = st.number_input("VPS (cm/s)", min_value=0.0, step=1.0)
    vfd = st.number_input("VFD (cm/s)", min_value=0.0, step=1.0)
    
    vm_aci_ref = 1.0
    if "ACM" in arteria_sel:
        vm_aci_ref = st.number_input("Vm ACI (para Lindegaard)", min_value=1.0, value=30.0)

    if st.button("💾 Calcular y Guardar"):
        # Cálculos
        vm = vps + (vfd * (2/3))
        ip = (vps - vfd) / vm if vm > 0 else 0
        ir = (vps - vfd) / vps if vps > 0 else 0
        lind = vm / vm_aci_ref if "ACM" in arteria_sel else 0
        
        # Validación de estado
        ref = REFERENCIAS[arteria_sel]
        estado = "Normal"
        if vps > ref["vps"] * 1.3: estado = "Velocidad Elevada"
        elif vps < ref["vps"] * 0.7 and vps > 0: estado = "Velocidad Baja"
        if ip > NORMAL_IP[1]: estado += " / IP Alto"
        if "ACM" in arteria_sel and lind > 3: estado = "Sugiere Vasoespasmo"

        nueva_fila = {
            "Arteria": arteria_sel, "VPS": vps, "VFD": vfd, 
            "Vm": round(vm, 2), "IP": round(ip, 2), 
            "IR": round(ir, 2), "Lindegaard": round(lind, 2) if lind > 0 else "N/A",
            "Estado": estado
        }
        
        st.session_state.df_resultados = st.session_state.df_resultados[st.session_state.df_resultados.Arteria != arteria_sel]
        st.session_state.df_resultados = pd.concat([st.session_state.df_resultados, pd.DataFrame([nueva_fila])], ignore_index=True)

# --- Disposición de la Pantalla Principal ---
col_tabla, col_grafico = st.columns([2, 1])

with col_tabla:
    st.subheader("📋 Reporte Actual")
    if not st.session_state.df_resultados.empty:
        st.table(st.session_state.df_resultados)
    else:
        st.info("Ingrese datos en el panel izquierdo para comenzar.")

with col_grafico:
    st.subheader("📊 Comparativa Vm")
    if not st.session_state.df_resultados.empty:
        st.bar_chart(data=st.session_state.df_resultados, x="Arteria", y="Vm")

# --- Sección de Referencias ---
with st.expander("📚 Ver Valores de Referencia y Normalidad"):
    st.write("**Valores Promedio (cm/s):**")
    ref_df = pd.DataFrame.from_dict(REFERENCIAS, orient='index')
    st.dataframe(ref_df)
    st.markdown(f"""
    **Índices de Normalidad:**
    * **IP (Pulsatilidad):** {NORMAL_IP[0]} - {NORMAL_IP[1]}
    * **IR (Resistencia):** {NORMAL_IR[0]} - {NORMAL_IR[1]}
    * **Lindegaard:** < 3.0 (Normal), 3-6 (Vasoespasmo leve/moderado), > 6 (Vasoespasmo severo).
    """)

# --- Exportación ---
if not st.session_state.df_resultados.empty:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state.df_resultados.to_excel(writer, index=False, sheet_name='Doppler')
    
    st.download_button(
        label="📥 Descargar Reporte en Excel",
        data=output.getvalue(),
        file_name='reporte_doppler.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )