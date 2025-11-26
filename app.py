
import streamlit as st
import pandas as pd
import numpy as np

# Título do app
st.title("Dashboard Interativo com Streamlit")

# Slider para escolher número de pontos
num_points = st.slider("Escolha o número de pontos", min_value=10, max_value=500, value=100)

# Gerando dados aleatórios
x = np.linspace(0, 10, num_points)
y = np.sin(x) + np.random.normal(0, 0.1, num_points)

# Criando DataFrame
data = pd.DataFrame({"x": x, "y": y})

# Mostrando tabela
st.write("Dados gerados:")
st.dataframe(data)

# Gráfico interativo
st.line_chart(data.set_index("x"))

# Checkbox para mostrar estatísticas
if st.checkbox("Mostrar estatísticas"):
    st.write(data.describe())
