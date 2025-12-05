
# app.py
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import io
from datetime import datetime

# Para gerar PDF
import fitz  # PyMuPDF

# -------------------------
# CONFIG & TÍTULO
# -------------------------
st.set_page_config(page_title="ENSAIO DE CURTO", layout="wide")
st.title("Ensaio de Curto")

st.markdown("Preencha os dados e clique em **Calcular**.")

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
    VA, VB, VC = x[0] + 1j*y[0], x[1] + 1j*y[1], x[2] + 1j*y[2]
    return np.array([VA - VB, VB - VC, VC - VA], dtype=complex)

def mag_ang(z):
    mag = np.abs(z)
    ang = np.degrees(np.angle(z))
    ang = (ang + 180) % 360 - 180
    return mag, ang

def fig_to_png_bytes(fig):
    """Converte um figure do Matplotlib para PNG em bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0)
    return buf.read()

def make_pdf(ensaio_data: dict, df_tc: pd.DataFrame = None, fasorial_png: bytes = None) -> bytes:
    """Gera um PDF com os dados do ensaio, tabela dos TC's e imagem do fasorial (se disponível)."""
    # A4 em pontos (72 dpi): 595 x 842
    W, H = 595, 842
    MARG_L, MARG_T = 40, 40
    LINE_H = 16

    doc = fitz.open()
    page = doc.new_page(width=W, height=H)

    # Helpers
    def write_line(page, x, y, text, size=11, bold=False):
        fontname = "helv" if not bold else "helv"  # PyMuPDF não troca peso facilmente sem fontes externas
        page.insert_text((x, y), text, fontsize=size, fontname=fontname)

    y = MARG_T

    # Cabeçalho
    write_line(page, MARG_L, y, "Relatório do Ensaio de Curto de Transformador", size=16, bold=True); y += LINE_H*1.8
    write_line(page, MARG_L, y, f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}", size=10); y += LINE_H
    write_line(page, MARG_L, y, f"Responsável: {st.session_state.get('user_name', 'Equipe')}", size=10); y += LINE_H*1.5

    # Dados de entrada
    write_line(page, MARG_L, y, "Dados de Entrada", size=13, bold=True); y += LINE_H*1.3
    entradas = [
        f"Impedância percentual (Z%): {ensaio_data.get('Z_percent', '')}",
        f"Potência nominal (S_MVA): {ensaio_data.get('S_MVA', '')} MVA",
        f"Tensão aplicada no ensaio (Vtest): {ensaio_data.get('Vtest_V', '')} V",
        f"Tensão base do lado ensaiado (Vbase_kV): {ensaio_data.get('Vbase_kV', '')} kV",
        f"Lado do ensaio: {ensaio_data.get('lado_ensaio', '')}",
    ]
    for t in entradas:
        write_line(page, MARG_L, y, f"• {t}", size=11); y += LINE_H

    y += LINE_H*0.7
    # Resultados principais
    write_line(page, MARG_L, y, "Resultados", size=13, bold=True); y += LINE_H*1.3
    resultados = [
        f"Corrente de linha (F-F): {ensaio_data.get('I_cc_A',''):,.2f} A",
        f"Corrente de fase (F-T): {ensaio_data.get('I_fase_A',''):,.2f} A",
        f"Potência aparente do ensaio: {ensaio_data.get('S_ensaio_kVA',''):,.2f} kVA",
    ]
    for t in resultados:
        write_line(page, MARG_L, y, f"• {t}", size=11); y += LINE_H

    # Observação
    y += LINE_H*0.7
    write_line(page, MARG_L, y, "Observações", size=13, bold=True); y += LINE_H*1.3
    obs = (
        "Se Vtest foi ajustada para que I_cc iguale a corrente nominal, a potência ativa medida no wattímetro representa as "
        "perdas no cobre em plena carga. Para calcular P (kW) e Q (kVAr) sem suposição, informe R% e X% ou meça potência no ensaio."
    )
    page.insert_textbox(fitz.Rect(MARG_L, y, W - MARG_L, y + LINE_H*3.5), obs, fontsize=11)
    y += LINE_H*3.8

    # Tabela dos TC's (se fornecida)
    if df_tc is not None and len(df_tc) > 0:
        write_line(page, MARG_L, y, "Tabela de Verificação dos TC's", size=13, bold=True); y += LINE_H*1.3
        # Cabeçalhos
        headers = list(df_tc.columns)
        col_x = [MARG_L, MARG_L + 180, MARG_L + 360, MARG_L + 490]  # ajuste conforme largura
        for i, h in enumerate(headers[:4]):  # limita a 4 colunas
            write_line(page, col_x[i], y, h, size=11, bold=True)
        y += LINE_H

        # Linhas
        for _, row in df_tc.iterrows():
            vals = [str(row.get(h, "")) for h in headers[:4]]
            for i, v in enumerate(vals):
                write_line(page, col_x[i], y, v, size=11)
            y += LINE_H
            # Quebra de página se necessário
            if y > H - MARG_T - LINE_H*8:
                page = doc.new_page(width=W, height=H)
                y = MARG_T

    # Imagem do diagrama fasorial (se fornecida)
    if fasorial_png is not None:
        # Se não couber na página, cria nova
        needed_h = 300
        if y + needed_h > H - MARG_T:
            page = doc.new_page(width=W, height=H)
            y = MARG_T
        write_line(page, MARG_L, y, "Diagrama Fasorial das Correntes", size=13, bold=True); y += LINE_H*0.8
        img_rect = fitz.Rect(MARG_L, y, W - MARG_L, y + 280)  # altura da imagem ~280 pt
        page.insert_image(img_rect, stream=fasorial_png)
        y += 300

    # Exporta PDF em memória
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

# -------------------------
# CÁLCULO + PLOT + TABELA
# -------------------------
if Z_percent and S_MVA and VAT and VBT and lado_ensaio and Vtest_V:
    if btn:
        Z_pu    = Z_percent / 100.0
        S_VA    = S_MVA * 1e6

        Vbase_kV = VAT if lado_ensaio == "AT" else VBT
        Vbase_V  = Vbase_kV * 1000.0

        V_pu = Vtest_V / Vbase_V
        I_pu = V_pu / Z_pu

        I_base_A = S_VA / (SQRT3 * Vbase_V)
        I_cc_A = I_pu * I_base_A

        # Potência aparente
        S_ensaio_VA  = SQRT3 * Vtest_V * I_cc_A
        S_ensaio_kVA = S_ensaio_VA / 1000.0

        st.subheader("Resultados do Ensaio de Curto-Circuito")

        c1, c2, c3 = st.columns(3)
        c1.metric("Corrente de Linha (F-F) [A]", f"{I_cc_A:,.2f}")
        if lado_ensaio == "AT":  # AT (delta) → Ifase = Ilinha/√3
            I_fase_A = I_cc_A / SQRT3
        else:  # BT (estrela) → Ifase = Ilinha
            I_fase_A = I_cc_A
        c2.metric("Corrente de Fase (F-T) [A]", f"{I_fase_A:,.2f}")
        c3.metric("Tensão aplicada [V]", f"{Vtest_V:,.2f}")

        p1, p2, p3 = st.columns(3)
        p1.metric("Potência Aparente do Ensaio [kVA]", f"{S_ensaio_kVA:,.2f}")

        st.caption(
            "📌 Se você ajustar Vtest para que I_cc = corrente nominal, então P_ensaio representa as perdas no cobre em plena carga."
        )

        # Guarda resultados para PDF
        st.session_state["ensaio_data"] = {
            "Z_percent": Z_percent,
            "S_MVA": S_MVA,
            "Vtest_V": Vtest_V,
            "Vbase_kV": Vbase_kV,
            "lado_ensaio": lado_ensaio,
            "I_cc_A": I_cc_A,
            "I_fase_A": I_fase_A,
            "S_ensaio_kVA": S_ensaio_kVA,
        }

# -------------------------
# FORMULÁRIO PARA ÂNGULOS DE CORRENTE
# -------------------------
st.subheader("Verificação de Ligação dos TC's")
st.markdown("Informe os ângulos medidos no **primário** (em graus):")

with st.form("tc_check"):
    col1, col2, col3 = st.columns(3)
    ang_IA = col1.number_input("Ângulo IA (°):", min_value=-180.0, max_value=180.0, step=1.0)
    ang_IB = col2.number_input("Ângulo IB (°):", min_value=-180.0, max_value=180.0, step=1.0)
    ang_IC = col3.number_input("Ângulo IC (°):", min_value=-180.0, max_value=180.0, step=1.0)

    btn_tc = st.form_submit_button("Verificar")

if 'btn_tc' in locals() and btn_tc:
    prim_angles = np.array([ang_IA, ang_IB, ang_IC])
    sec_angles = prim_angles - 30.0 + 180.0
    sec_angles = (sec_angles + 180) % 360 - 180

    rows = []
    fases = ["IA", "IB", "IC"]
    fases_sec = ["Ia", "Ib", "Ic"]
    for f1, f2, a1, a2 in zip(fases, fases_sec, prim_angles, sec_angles):
        rows.append({
            "Fase Primário": f1,
            "Ângulo Primário (°)": round(a1, 1),
            "Fase Secundário": f2,
            "Ângulo Esperado (°)": round(a2, 1)
        })

    df_tc = pd.DataFrame(rows)
    st.markdown("**Tabela de Verificação dos TC's**")
    st.dataframe(df_tc, hide_index=True)

    # -------------------------
    # DIAGRAMA FASORIAL DAS CORRENTES
    # -------------------------
    st.subheader("Diagrama Fasorial das Correntes")
    st.caption("Primário (vermelho) e Secundário (azul)")

    mag = 1.0
    xP, yP = phasor_xy(mag, prim_angles)
    xS, yS = phasor_xy(mag, sec_angles)

    fig, ax = plt.subplots(figsize=(7,7))
    for xi, yi, lab in zip(xP, yP, fases):
        ax.plot([0, xi], [0, yi], marker="o", linewidth=2, color="red")
        ax.text(xi*1.06, yi*1.06, lab, color="red", fontsize=10)

    for xi, yi, lab in zip(xS, yS, fases_sec):
        ax.plot([0, xi], [0, yi], marker="o", linewidth=2, color="blue")
        ax.text(xi*1.06, yi*1.06, lab, color="blue", fontsize=10)

    ax.axhline(0, color="black", linewidth=1)
    ax.axvline(0, color="black", linewidth=1)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Real")
    ax.set_ylabel("Imag")
    ax.grid(True, linestyle=":")

    st.pyplot(fig)

    # Guarda a tabela e o gráfico para o PDF
    st.session_state["df_tc"] = df_tc
    try:
        st.session_state["fasorial_png"] = fig_to_png_bytes(fig)
    except Exception as e:
        st.session_state["fasorial_png"] = None
    finally:
        plt.close(fig)

# -------------------------
# GERAR RELATÓRIO (PDF)
# -------------------------
st.markdown("---")
st.subheader("Relatório")
colA, colB = st.columns([3, 1])
with colA:
    st.caption("Gere um PDF com os dados do ensaio, tabela dos TC's e o diagrama fasorial (se disponível).")

with colB:
    ensaio_data = st.session_state.get("ensaio_data", None)
    df_tc = st.session_state.get("df_tc", None)
    fasorial_png = st.session_state.get("fasorial_png", None)

    if ensaio_data is None:
        st.button("Gerar Relatório (PDF)", disabled=True)
        st.info("Calcule o ensaio primeiro para habilitar o relatório.")
    else:
        if st.button("Gerar Relatório (PDF)"):
            pdf_bytes = make_pdf(ensaio_data, df_tc=df_tc, fasorial_png=fasorial_png)
            st.download_button(
                label="⬇️ Baixar PDF do Ensaio",
                data=pdf_bytes,
                file_name=f"Relatorio_Ensaio_Curto_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
