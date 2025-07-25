import streamlit as st
import pandas as pd

st.set_page_config(page_title="Registro Alimentar", layout="wide")

@st.cache_data
def carregar_dados():
    return pd.read_csv("alimentos.csv", sep=";")

taco = carregar_dados()

# Detectar o nome da coluna de descrição
coluna_desc = [col for col in taco.columns if "descrição" in col.lower()][0]

st.title("🍽️ Registro Alimentar")

busca = st.text_input("🔎 Digite o nome do alimento:")

if busca:
    resultados = taco[taco[coluna_desc].str.contains(busca, case=False, na=False)]

    if not resultados.empty:
        alimento = st.selectbox("Selecione o alimento encontrado:", resultados[coluna_desc].tolist())

        dados = resultados[resultados[coluna_desc] == alimento]

        st.subheader("📊 Informações Nutricionais por 100g")
        st.dataframe(dados.reset_index(drop=True), use_container_width=True)
    else:
        st.warning("Nenhum alimento encontrado com esse nome.")
else:
    st.info("Digite o nome de um alimento para buscar.")
