# app.py
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------
# CONFIG & TÍTULO
# -------------------------
st.set_page_config(page_title="ENSAIO DE CURTO ", layout="wide")
st.title("Ensaio de Curto")

st.markdown(
    "Preencha os dados e clique em **Calcular**. "
)

# -------------------------
# FORMULÁRIO DE ENTRADA
# -------------------------
with st.form("inputs"):
    c1, c2 = st.columns(2)
    with c1:
        Z_percent = st.number_input("Impedância percentual Z%:", min_value=0.1, max_value=100.0, value=None, step=0.01)
        S_MVA     = st.number_input("Potência nominal S [MVA]:", min_value=0.1, max_value=1000.0, value=None, step=0.1)
        Vtest_V   = st.number_input("Tensão aplicada no ensaio de curto [V]:", min_value=1.0, max_value=50000.0, value=None, step=10.0)
    with c2:
        VBT  = st.number_input("Tensão nominal do lado de Baixa [kV]:", min_value=0.1, max_value=50000.0, value=None, step=0.1)
        VAT  = st.number_input("Tensão nominal do lado de Alta [kV]:", min_value=0.1, max_value=50000.0, value=None, step=0.1)
        lado_ensaio = st.radio("Selecione o lado do ensaio:", ["AT", "BT"])
    

    btn = st.form_submit_button("Calcular")

# -------------------------
# FUNÇÕES AUXILIARES
# -------------------------
SQRT3 = np.sqrt(3.0)

def phasor_xy(mag, ang_deg):
    ang = np.deg2rad(ang_deg)
    return mag*np.cos(ang), mag*np.sin(ang)

def line_to_line_from_phases(x, y):
    """
    Recebe arrays x,y (VA,VB,VC) como tensões de fase (pu) e retorna complexos VAB,VBC,VCA.
    """
    VA, VB, VC = x[0] + 1j*y[0], x[1] + 1j*y[1], x[2] + 1j*y[2]
    return np.array([VA - VB, VB - VC, VC - VA], dtype=complex)

def mag_ang(z):
    mag = np.abs(z)
    ang = np.degrees(np.angle(z))
    ang = (ang + 180) % 360 - 180  # normaliza para [-180,180]
    return mag, ang

if Z_percent and S_MVA and VAT and VBT and lado_ensaio and Vtest_V:
# -------------------------
# CÁLCULO + PLOT + TABELA
# -------------------------
    if btn:
        # ---- Ensaio de curto
        Z_pu    = Z_percent / 100.0
        S_VA    = S_MVA * 1e6
        Vbase_kV = 0

        if lado_ensaio == "AT":
            Vbase_kV = VAT
        else:
            Vbase_kV = VBT

        Vbase_V = Vbase_kV * 1000.0


        # Tensão em pu referida à base informada
        V_pu = Vtest_V / Vbase_V
        I_pu = V_pu / Z_pu

        # Corrente base (trifásica, linha)
        I_base_A = S_VA / (SQRT3 * Vbase_V)

        # Corrente do ensaio
        I_cc_A = I_pu * I_base_A

        st.subheader("Corrente de Curto-Circuito")
        
        # Calcula corrente de fase
        if lado_ensaio == "AT":  # AT é delta
            I_fase_A = I_cc_A / SQRT3
        else:  # BT é estrela
            I_fase_A = I_cc_A
        
        c1, c2 = st.columns(2)
        c1.metric("Corrente de Linha (Fase-Fase) [A]", f"{I_cc_A:,.2f}")
        c2.metric("Corrente de Fase (Fase-Terra) [A]", f"{I_fase_A:,.2f}")

# -------------------------
# NOVO FORMULÁRIO PARA ÂNGULOS DE CORRENTE
# -------------------------
    st.subheader("Verificação de Ligação dos TC's")
    st.markdown("Informe os ângulos medidos no **primário** (em graus):")
    
    with st.form("tc_check"):
        col1, col2, col3 = st.columns(3)
        ang_IA = col1.number_input("Ângulo IA (°):", min_value=-180.0, max_value=180.0, step=1.0)
        ang_IB = col2.number_input("Ângulo IB (°):", min_value=-180.0, max_value=180.0, step=1.0)
        ang_IC = col3.number_input("Ângulo IC (°):", min_value=-180.0, max_value=180.0, step=1.0)
    
        btn_tc = st.form_submit_button("Verificar")
    
    if btn_tc:
        # Ângulos primário
        prim_angles = np.array([ang_IA, ang_IB, ang_IC])
    
        # Esperado no secundário (Dyn1 = desloca -30°)
        sec_angles = prim_angles - 30.0 + 180.0
        sec_angles = (sec_angles + 180) % 360 - 180  # normaliza para [-180,180]
    
        # Monta tabela
        rows = []
        fases = ["IA", "IB", "IC"]
        fases_sec = ["Ia", "Ib", "Ic"]
        for f1, f2, a1, a2 in zip(fases, fases_sec, prim_angles, sec_angles):
            rows.append({"Fase Primário": f1, "Ângulo Primário (°)": round(a1, 1),
                         "Fase Secundário": f2, "Ângulo Esperado (°)": round(a2, 1)})
    
        df_tc = pd.DataFrame(rows)
        st.markdown("**Tabela de Verificação dos TC's**")
        st.dataframe(df_tc, hide_index=True)

    # -------------------------
    # DIAGRAMA FASORIAL DAS CORRENTES
    # -------------------------
    st.subheader("Diagrama Fasorial das Correntes")
    st.caption("Primário (vermelho) e Secundário (azul)")

    # Magnitude normalizada (1.0)
    mag = 1.0
    xP, yP = phasor_xy(mag, prim_angles)
    xS, yS = phasor_xy(mag, sec_angles)

    fig, ax = plt.subplots(figsize=(7,7))

    # Primário
    for xi, yi, lab in zip(xP, yP, fases):
        ax.plot([0, xi], [0, yi], marker="o", linewidth=2, color="red")
        ax.text(xi*1.06, yi*1.06, lab, color="red", fontsize=10)

    # Secundário
    for xi, yi, lab in zip(xS, yS, fases_sec):
        ax.plot([0, xi], [0, yi], marker="o", linewidth=2, color="blue")
        ax.text(xi*1.06, yi*1.06, lab, color="blue", fontsize=10)

    # Eixos
    ax.axhline(0, color="black", linewidth=1)
    ax.axvline(0, color="black", linewidth=1)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Real")
    ax.set_ylabel("Imag")
    ax.grid(True, linestyle=":")

    st.pyplot(fig)
