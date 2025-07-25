
import streamlit as st
import pandas as pd
import difflib
from unidecode import unidecode

st.set_page_config(page_title="Registro Alimentar", layout="wide")

# Função utilitária
def normalizar(texto):
    return unidecode(str(texto)).lower().strip()

# Carrega a base
@st.cache_data
def carregar_taco():
    df = pd.read_csv("alimentos.csv", sep=";")
    df.columns = df.columns.str.strip()
    df["Descrição dos alimentos"] = df["Descrição dos alimentos"].astype(str).str.strip()
    df["normalizado"] = df["Descrição dos alimentos"].apply(normalizar)
    return df

taco = carregar_taco()

# Estado inicial
if "registro_alimentos" not in st.session_state:
    st.session_state["registro_alimentos"] = []

st.title("🍽️ Registro Alimentar")

# Campo de busca
busca = st.text_input("Digite o nome de um alimento:", "")
resultados = []

if busca:
    busca_norm = normalizar(busca)
    similares = difflib.get_close_matches(busca_norm, taco["normalizado"], n=10, cutoff=0.3)
    resultados = taco[taco["normalizado"].isin(similares)]

    if not resultados.empty:
        nomes = resultados["Descrição dos alimentos"].tolist()
        alimento_selecionado = st.selectbox("Selecione o alimento encontrado:", nomes)

        if alimento_selecionado:
            quantidade = st.number_input("Informe a quantidade consumida (em gramas):", min_value=1, value=100)
            if st.button("Registrar alimento"):
                registro = {
                    "alimento": alimento_selecionado,
                    "quantidade": quantidade
                }
                st.session_state["registro_alimentos"].append(registro)
                st.success(f"{alimento_selecionado} registrado com sucesso!")

# Exibe alimentos registrados com botão de exclusão
st.subheader("🍽️ Alimentos registrados no dia")
if st.session_state["registro_alimentos"]:
    for i, item in enumerate(st.session_state["registro_alimentos"]):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"**{item['alimento']}** – {item['quantidade']}g")
        with col2:
            if st.button("❌", key=f"excluir_{i}"):
                st.session_state["registro_alimentos"].pop(i)
                st.experimental_rerun()
else:
    st.info("Nenhum alimento registrado ainda.")

# Calcula totais
st.subheader("📊 Total Nutricional do Dia")

df_registros = pd.DataFrame(st.session_state["registro_alimentos"])
if not df_registros.empty:
    registros = pd.merge(df_registros, taco, left_on="alimento", right_on="Descrição dos alimentos", how="left")
    fatores = registros["quantidade"] / 100

    macros = ["Energia..kcal.", "Proteína..g.", "Carboidrato..g.", "Lipídeos..g."]
    totais = {col: (registros[col] * fatores).sum() for col in macros}

    st.metric("Calorias totais (kcal)", round(totais["Energia..kcal."], 2))
    st.metric("Proteína total (g)", round(totais["Proteína..g."], 2))
    st.metric("Carboidratos totais (g)", round(totais["Carboidrato..g."], 2))
    st.metric("Gorduras totais (g)", round(totais["Lipídeos..g."], 2))

    # Exportação
    csv = registros.to_csv(index=False, sep=";")
    st.download_button("📁 Exportar para CSV", csv, "registro_alimentar.csv", "text/csv")
