import streamlit as st
import pandas as pd

st.set_page_config(page_title="Registro Alimentar", layout="wide")

@st.cache_data
def carregar_dados():
    return pd.read_csv("alimentos.csv", sep=";")

taco = carregar_dados()

# Tentativa robusta de localizar a coluna de descrição dos alimentos
coluna_desc = [col for col in taco.columns if "descrição" in col.lower()][0]

st.title("🍽️ Registro Alimentar")

alimento = st.selectbox("Escolha o alimento:", taco[coluna_desc])

info_alimento = taco[taco[coluna_desc] == alimento]

if not info_alimento.empty:
    st.subheader("🔍 Informações Nutricionais por 100g")
    st.dataframe(info_alimento.transpose(), use_container_width=True)
else:
    st.error("Alimento não encontrado.")
