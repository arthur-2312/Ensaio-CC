# app.py
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------
# CONFIG & TÍTULO
# -------------------------
st.set_page_config(page_title="ENSAIO DE CURTO ", layout="wide")
st.title("senta pro treeeeeeeeeem")

st.markdown(
    "Preencha os dados e clique em em **Calcular**. "
)

# -------------------------
# FORMULÁRIO DE ENTRADA
# -------------------------
with st.form("inputs"):
    c1, c2 = st.columns(2)
    with c1:
        Z_percent = st.number_input("Impedância percentual Z%:", min_value=0.1, max_value=100.0, value=None, step=0.01)
        S_MVA     = st.number_input("Potência nominal S [MVA]:", min_value=0.1, max_value=1000.0, value=None, step=0.1)
    with c2:
        Vbase_kV  = st.number_input("Tensão base (Tensão nominal do trafo no lado do ensaio) [kV]:", min_value=0.1, max_value=50000.0, value=None, step=0.1)
        Vtest_V   = st.number_input("Tensão aplicada no ensaio de curto [V]:", min_value=1.0, max_value=50000.0, value=None, step=10.0)


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

if Z_percent and S_MVA and Vbase_kV and Vtest_V:
# -------------------------
# CÁLCULO + PLOT + TABELA
# -------------------------
    if btn:
        # ---- Ensaio de curto
        Z_pu    = Z_percent / 100.0
        S_VA    = S_MVA * 1e6
        Vbase_V = Vbase_kV * 1000.0

        # Tensão em pu referida à base informada
        V_pu = Vtest_V / Vbase_V
        I_pu = V_pu / Z_pu

        # Corrente base (trifásica, linha)
        I_base_A = S_VA / (SQRT3 * Vbase_V)

        # Corrente do ensaio
        I_cc_A = I_pu * I_base_A

        st.subheader("Resultados do Ensaio de Curto")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Z (pu)", f"{Z_pu:.4f}")
        c2.metric("V (pu)", f"{V_pu:.4f}")
        c3.metric("I base [A]", f"{I_base_A:,.2f}")
        c4.metric("Icc (ensaio) [A]", f"{I_cc_A:,.2f}")

        st.divider()

        # ---- Diagrama fasorial Dyn1
        st.subheader("Diagrama Fasorial Dyn1")
        st.caption("AT (vermelho) e BT (azul). Linhas tracejadas tensões de linha")

        # Magnitudes para o desenho (pu). Aqui deixamos normalizado (=1.0).
        mag_HV = 1.0
        mag_LV = 1.0

        # Fases HV (0°, -120°, +120°); LV (Dyn1) = HV - 30°
        ang_HV = np.array([0.0, -120.0, 120.0])
        ang_LV = ang_HV - 30.0

        xH, yH = phasor_xy(mag_HV, ang_HV)   # VA, VB, VC (pu)
        xL, yL = phasor_xy(mag_LV, ang_LV)   # Va, Vb, Vc (pu)

        # Linha-linha (complexos)
        VLL_H = line_to_line_from_phases(xH, yH)  # VAB, VBC, VCA
        VLL_L = line_to_line_from_phases(xL, yL)  # vab, vbc, vca

        col_plot, col_table = st.columns([3, 2])

        with col_plot:
            fig, ax = plt.subplots(figsize=(7,7))

            # HV (vermelho)
            for xi, yi, lab in zip(xH, yH, ["VA","VB","VC"]):
                ax.plot([0, xi], [0, yi], marker="o", linewidth=2, color="red")
                ax.text(xi*1.06, yi*1.06, lab, color="red", fontsize=10)

            # LV (azul)
            for xi, yi, lab in zip(xL, yL, ["Va","Vb","Vc"]):
                ax.plot([0, xi], [0, yi], marker="o", linewidth=2, color="blue")
                ax.text(xi*1.06, yi*1.06, lab, color="blue", fontsize=10)

            # LL tracejados
            for comp, name in zip(VLL_H, ["VAB","VBC","VCA"]):
                ax.plot([0, comp.real], [0, comp.imag], linestyle="--", linewidth=1.8, color="red")
                ax.text(comp.real*1.06, comp.imag*1.06, name, color="red", fontsize=9)
            for comp, name in zip(VLL_L, ["vab","vbc","vca"]):
                ax.plot([0, comp.real], [0, comp.imag], linestyle="--", linewidth=1.8, color="blue")
                ax.text(comp.real*1.06, comp.imag*1.06, name, color="blue", fontsize=9)

            # Eixos e grid
            ax.axhline(0, color="black", linewidth=1)
            ax.axvline(0, color="black", linewidth=1)
            ax.set_aspect("equal", adjustable="box")
            ax.set_xlabel("Real")
            ax.set_ylabel("Imag")
            ax.grid(True, linestyle=":")


            st.pyplot(fig)

        with col_table:
            # Monta a tabela com todas as grandezas
            phasors = {
                "VA":  xH[0]+1j*yH[0], "VB": xH[1]+1j*yH[1], "VC": xH[2]+1j*yH[2],
                "Va":  xL[0]+1j*yL[0], "Vb": xL[1]+1j*yL[1], "Vc": xL[2]+1j*yL[2],
                "VAB": VLL_H[0], "VBC": VLL_H[1], "VCA": VLL_H[2],
                "vab": VLL_L[0], "vbc": VLL_L[1], "vca": VLL_L[2],
            }
            rows = []
            for name, z in phasors.items():
                m, a = mag_ang(z)
                rows.append({"Fasor": name, "Ângulo (°)": round(a, 1)})

            df = pd.DataFrame(rows)
            st.markdown("**Ângulos e Magnitudes (pu)**")
            st.dataframe(df, hide_index=True)

