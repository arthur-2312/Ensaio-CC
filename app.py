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

    "Preencha os dados do ensaio de curto e/ou dos TC's."

)

# -------------------------

# FORMULÁRIO DE ENTRADA - ENSAIO DE CURTO

# -------------------------

with st.form("inputs"):

    c1, c2 = st.columns(2)

    with c1:

        Z_percent = st.number_input("Impedância percentual Z%:", min_value=0.1, max_value=100.0, value=5.0, step=0.01)

        S_MVA     = st.number_input("Potência nominal S [MVA]:", min_value=0.1, max_value=1000.0, value=10.0, step=0.1)

        Vtest_V   = st.number_input("Tensão aplicada no ensaio de curto [V]:", min_value=1.0, max_value=50000.0, value=1000.0, step=10.0)

    with c2:

        VBT  = st.number_input("Tensão nominal do lado de Baixa [kV]:", min_value=0.1, max_value=50000.0, value=0.38, step=0.01)

        VAT  = st.number_input("Tensão nominal do lado de Alta [kV]:", min_value=0.1, max_value=50000.0, value=13.8, step=0.1)

        lado_ensaio = st.radio("Selecione o lado do ensaio:", ["AT", "BT"])

    btn = st.form_submit_button("Calcular corrente")

# -------------------------

# FUNÇÕES AUXILIARES

# -------------------------

SQRT3 = np.sqrt(3.0)

def phasor_xy(mag, ang_deg):

    """Converte módulo e ângulo (graus) em coordenadas x,y."""

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

# -------------------------

# CÁLCULO ENSAIO DE CURTO

# -------------------------

I_fase_A = None  # vamos tentar calcular; se não der, usamos 1.0 A no diagrama

if btn:

    # ---- Ensaio de curto

    Z_pu    = Z_percent / 100.0

    S_VA    = S_MVA * 1e6

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

    # Corrente do ensaio (linha)

    I_cc_A = I_pu * I_base_A

    # Corrente de fase

    if lado_ensaio == "AT":  # AT é delta

        I_fase_A = I_cc_A / SQRT3

    else:  # BT é estrela

        I_fase_A = I_cc_A

    st.subheader("Correntes do Ensaio de Curto")

    c1, c2 = st.columns(2)

    c1.metric("Corrente de Linha (Fase-Fase) [A]", f"{I_cc_A:,.2f}")

    c2.metric("Corrente de Fase (Fase-Terra) [A]", f"{I_fase_A:,.2f}")

# -------------------------

# VERIFICAÇÃO DE LIGAÇÃO DOS TC's + DIAGRAMA FASORIAL

# -------------------------

st.subheader("Verificação de Ligação dos TC's")

st.markdown("Informe os ângulos medidos no **primário** (em graus) e como as fases do **secundário** apareceram:")

with st.form("tc_check"):

    # ÂNGULOS DO PRIMÁRIO

    col1, col2, col3 = st.columns(3)

    ang_IA = col1.number_input("Ângulo IA (°):", min_value=-180.0, max_value=180.0, step=1.0, value=0.0)

    ang_IB = col2.number_input("Ângulo IB (°):", min_value=-180.0, max_value=180.0, step=1.0, value=-120.0)

    ang_IC = col3.number_input("Ângulo IC (°):", min_value=-180.0, max_value=180.0, step=1.0, value=120.0)

    st.markdown("---")

    st.markdown("**Como as fases apareceram no secundário (no relé / medidor)**")

    st.markdown("Ex.: se no lugar de *Ia* você enxergou a fase *Ib*, escolha **Ib** no primeiro campo.")

    col4, col5, col6 = st.columns(3)

    sec_pos_Ia = col4.selectbox("No lugar de Ia apareceu:", ["Ia", "Ib", "Ic"], index=0)

    sec_pos_Ib = col5.selectbox("No lugar de Ib apareceu:", ["Ia", "Ib", "Ic"], index=1)

    sec_pos_Ic = col6.selectbox("No lugar de Ic apareceu:", ["Ia", "Ib", "Ic"], index=2)

    btn_tc = st.form_submit_button("Verificar e plotar diagrama")

if btn_tc:

    # -------------------------

    # ÂNGULOS TEÓRICOS PRIMÁRIO x SECUNDÁRIO (Dyn1)

    # -------------------------

    prim_angles = np.array([ang_IA, ang_IB, ang_IC])

    # Esperado no secundário (Dyn1 = desloca -30°)

    sec_angles = prim_angles - 30.0

    sec_angles = (sec_angles + 180) % 360 - 180  # normaliza para [-180,180]

    # Tabela de ângulos esperados

    rows = []

    fases_prim = ["IA", "IB", "IC"]

    fases_sec  = ["Ia", "Ib", "Ic"]

    for f1, f2, a1, a2 in zip(fases_prim, fases_sec, prim_angles, sec_angles):

        rows.append({

            "Fase Primário": f1,

            "Ângulo Primário (°)": round(a1, 1),

            "Fase Secundário (esperada)": f2,

            "Ângulo Esperado (°)": round(a2, 1)

        })

    df_tc = pd.DataFrame(rows)

    st.markdown("**Tabela de Ângulos Teóricos dos TC's (Dyn1)**")

    st.dataframe(df_tc, hide_index=True)

    # -------------------------

    # VERIFICAÇÃO DA SEQUÊNCIA DE FASES NO SECUNDÁRIO

    # -------------------------

    st.markdown("---")

    st.markdown("### Análise da sequência de fases no secundário")

    expected_order = ["Ia", "Ib", "Ic"]

    measured_order = [sec_pos_Ia, sec_pos_Ib, sec_pos_Ic]

    if measured_order == expected_order:

        st.success(

            "✅ A ligação dos TC's está **correta**.\n\n"

            "A sequência de fases no secundário está **Ia – Ib – Ic**, "

            "e a defasagem teórica é de **-30°** entre primário e secundário (ligação Dyn1)."

        )

    else:

        st.error("⚠️ A ligação dos TC's **NÃO está correta**.")

        # Tabela mostrando posição esperada x fase medida

        map_rows = []

        for pos, meas in zip(expected_order, measured_order):

            map_rows.append({

                "Posição no relé (esperado)": pos,

                "Fase que apareceu": meas

            })

        df_map = pd.DataFrame(map_rows)

        st.markdown("**Comparação entre posição esperada e fase medida:**")

        st.table(df_map)

        # Resumo das trocas necessárias

        trocas = []

        for pos, meas in zip(expected_order, measured_order):

            if pos != meas:

                trocas.append(f"No lugar de **{pos}** está chegando a fase **{meas}**.")

        if trocas:

            st.markdown("**Resumo das inconsistências encontradas:**")

            for t in trocas:

                st.markdown(f"- {t}")

            st.markdown(

                "\nPara a ligação ficar correta (Dyn1), as fases do secundário devem ser vistas na ordem:\n"

                "**Ia – Ib – Ic** e defasadas de **-30°** em relação às correntes do primário."

            )

    # -------------------------

    # DIAGRAMA FASORIAL PRIMÁRIO x SECUNDÁRIO

    # -------------------------

    st.markdown("---")

    st.markdown("### Diagrama Fasorial das Correntes (Primário x Secundário)")

    # Se não foi possível calcular corrente de fase, usa 1 A como referência

    if I_fase_A is None:

        I_fase_mag = 1.0

        st.info("Corrente de fase não calculada a partir do ensaio. Usando magnitude **1,0 A** apenas para efeito de diagrama.")

    else:

        I_fase_mag = I_fase_A

    # Magnitudes (assumimos mesmas magnitudes primário/secundário para o diagrama)

    prim_mags = np.array([I_fase_mag, I_fase_mag, I_fase_mag])

    sec_mags  = np.array([I_fase_mag, I_fase_mag, I_fase_mag])

    # Coordenadas x,y

    prim_xy = [phasor_xy(m, ang) for m, ang in zip(prim_mags, prim_angles)]

    sec_xy  = [phasor_xy(m, ang) for m, ang in zip(sec_mags, sec_angles)]

    # Plot

    fig, ax = plt.subplots()

    # Eixos

    ax.axhline(0, linewidth=0.8)

    ax.axvline(0, linewidth=0.8)

    # Plota primário (azul)

    for (x, y), label, mag in zip(prim_xy, fases_prim, prim_mags):

        ax.arrow(0, 0, x, y,

                 head_width=0.05*I_fase_mag, head_length=0.1*I_fase_mag,

                 length_includes_head=True,

                 color="blue")

        ax.text(1.1*x, 1.1*y, f"{label}\n{mag:.2f} A",

                ha="center", va="center", fontsize=8, color="blue")

    # Plota secundário (vermelho)

    for (x, y), label, mag in zip(sec_xy, fases_sec, sec_mags):

        ax.arrow(0, 0, x, y,

                 head_width=0.05*I_fase_mag, head_length=0.1*I_fase_mag,

                 length_includes_head=True,

                 color="red")

        ax.text(1.1*x, 1.1*y, f"{label}\n{mag:.2f} A",

                ha="center", va="center", fontsize=8, color="red")

    # Ajustes do gráfico

    max_mag = 1.4 * I_fase_mag

    ax.set_xlim(-max_mag, max_mag)

    ax.set_ylim(-max_mag, max_mag)

    ax.set_aspect("equal", "box")

    ax.set_xlabel("Eixo Real")

    ax.set_ylabel("Eixo Imaginário")

    ax.grid(True, linestyle="--", linewidth=0.5)

    st.pyplot(fig)
