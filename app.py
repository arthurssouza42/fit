
import streamlit as st
import pandas as pd
from unidecode import unidecode
from difflib import get_close_matches
from io import StringIO

st.set_page_config(page_title="Registro Alimentar", layout="wide")

# === Funções auxiliares ===

@st.cache_data
def carregar_dados():
    df = pd.read_csv("alimentos.csv")
    df.columns = df.columns.str.strip()
    df["DescriçãoFormatada"] = df["Descrição dos alimentos"].apply(lambda x: unidecode(str(x)).lower())
    return df

def buscar_alimentos(query, df):
    query = unidecode(query.lower())
    resultados = df[df["DescriçãoFormatada"].str.contains(query)]
    if resultados.empty:
        similares = get_close_matches(query, df["DescriçãoFormatada"], n=5, cutoff=0.4)
        resultados = df[df["DescriçãoFormatada"].isin(similares)]
    return resultados

def calcular_nutrientes(info_nutricional, quantidade):
    fator = quantidade / 100
    return info_nutricional * fator

# === App ===

st.title("🍽️ Registro Alimentar")
df = carregar_dados()

if "refeicoes" not in st.session_state:
    st.session_state.refeicoes = {"Café da manhã": [], "Almoço": [], "Jantar": [], "Lanches": []}

nome_busca = st.text_input("Digite o nome de um alimento:")
resultados = buscar_alimentos(nome_busca, df) if nome_busca else pd.DataFrame()

if not resultados.empty:
    selecionado = st.selectbox("Selecione o alimento encontrado:", resultados["Descrição dos alimentos"].tolist())
    quantidade = st.number_input("Quantidade (em gramas):", min_value=1, max_value=1000, step=10, value=100)
    refeicao = st.selectbox("Em qual refeição deseja registrar?", list(st.session_state.refeicoes.keys()))

    if st.button("Registrar alimento"):
        linha = df[df["Descrição dos alimentos"] == selecionado].iloc[0]
        info_nutricional = linha[["Energia..kcal.", "Proteína..g.", "Lipídeos..g.", "Carboidrato..g.", "Fibra.Alimentar..g."]].astype(float)
        valores = calcular_nutrientes(info_nutricional, quantidade)
        registro = {
            "Alimento": selecionado,
            "Quantidade (g)": quantidade,
            "Calorias (kcal)": valores["Energia..kcal."],
            "Proteína (g)": valores["Proteína..g."],
            "Lipídeos (g)": valores["Lipídeos..g."],
            "Carboidrato (g)": valores["Carboidrato..g."],
            "Fibra (g)": valores["Fibra.Alimentar..g."]
        }
        st.session_state.refeicoes[refeicao].append(registro)
        st.success(f"{quantidade}g de {selecionado} adicionado à refeição: {refeicao}")

# === Mostrar Tabelas ===

st.subheader("📊 Consumo Diário")
tudo = []
for nome, itens in st.session_state.refeicoes.items():
    if itens:
        st.markdown(f"### 🍴 {nome}")
        tabela = pd.DataFrame(itens)
        st.dataframe(tabela, use_container_width=True)
        tudo.extend(itens)

if tudo:
    df_total = pd.DataFrame(tudo)
    st.markdown("## ✅ Totais do Dia")
    totais = df_total.drop(columns=["Alimento", "Quantidade (g)"]).sum().round(2)
    st.write(totais.to_frame("Total"))

    # Exportar CSV
    csv = df_total.to_csv(index=False)
    st.download_button("📥 Exportar registro do dia (CSV)", csv, file_name="registro_alimentar.csv", mime="text/csv")
