
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# Título
st.title("Previsão com IA - Exemplo Simples")

# Gerando dados fictícios
np.random.seed(42)
X = np.random.rand(100, 1) * 10  # variável independente
y = 2.5 * X + np.random.randn(100, 1) * 2  # variável dependente

# Treinando modelo
model = LinearRegression()
model.fit(X, y)

# Mostrando dados
st.subheader("Dados de Treinamento")
data = pd.DataFrame({"X": X.flatten(), "y": y.flatten()})
st.write(data.head())

# Entrada do usuário
st.subheader("Faça uma previsão")
valor = st.number_input("Digite um valor para X:", min_value=0.0, max_value=10.0, value=5.0)

# Previsão
pred = model.predict([[valor]])[0][0]
st.write(f"Previsão para X={valor}: **{pred:.2f}**")

# Gráfico
st.subheader("Visualização")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.scatter(X, y, label="Dados")
ax.plot(X, model.predict(X), color="red", label="Modelo")
ax.scatter(valor, pred, color="green", s=100, label="Sua previsão")
ax.legend()
st.pyplot(fig)
