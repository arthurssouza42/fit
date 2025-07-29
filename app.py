import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

@st.cache_data
def carregar_tabela_alimentos():
    df = pd.read_csv("alimentos.csv", sep=";")

    # Padronizar nomes de colunas
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace("á", "a")
        .str.replace("ã", "a")
        .str.replace("â", "a")
        .str.replace("é", "e")
        .str.replace("ê", "e")
        .str.replace("í", "i")
        .str.replace("ó", "o")
        .str.replace("ô", "o")
        .str.replace("ú", "u")
        .str.replace("ç", "c")
        .str.replace(".", "")
        .str.replace(" ", "")
    )

    # Renomear para nomes-padrão usados no app
    df = df.rename(
        columns={
            "alimento": "Alimento",
            "energiakcal": "kcal",
            "proteina": "Proteína",
            "lipideos": "Gordura",
            "carboidrato": "Carboidrato",
        }
    )

    return df[["Alimento", "kcal", "Proteína", "Gordura", "Carboidrato"]]

df_alimentos = carregar_tabela_alimentos()

st.title("📊 Registro de refeições")
data = st.date_input("Escolha a data", value=datetime.today())

if "refeicoes" not in st.session_state:
    st.session_state.refeicoes = {}

refeicoes_disponiveis = ["Café da manhã", "Almoço", "Lanche", "Jantar"]
refeicao = st.selectbox("Escolha a refeição", refeicoes_disponiveis)
alimento = st.selectbox("Escolha o alimento", df_alimentos["Alimento"].unique())
quantidade = st.number_input("Quantidade (g)", min_value=1)

if st.button("Adicionar alimento"):
    dia = str(data)
    if dia not in st.session_state.refeicoes:
        st.session_state.refeicoes[dia] = {}
    if refeicao not in st.session_state.refeicoes[dia]:
        st.session_state.refeicoes[dia][refeicao] = []
    st.session_state.refeicoes[dia][refeicao].append((alimento, quantidade))

def calcular_totais(lista):
    totais = {"kcal": 0, "Proteína": 0, "Gordura": 0, "Carboidrato": 0}
    for nome, qtd in lista:
        linha = df_alimentos[df_alimentos["Alimento"] == nome].iloc[0]
        totais["kcal"] += linha["kcal"] * qtd / 100
        totais["Proteína"] += linha["Proteína"] * qtd / 100
        totais["Gordura"] += linha["Gordura"] * qtd / 100
        totais["Carboidrato"] += linha["Carboidrato"] * qtd / 100
    return totais

st.markdown("---")
dia = str(data)
if dia in st.session_state.refeicoes:
    total_dia = {"kcal": 0, "Proteína": 0, "Gordura": 0, "Carboidrato": 0}
    for nome_refeicao, itens in st.session_state.refeicoes[dia].items():
        st.markdown(f"### 🍽️ {nome_refeicao}")
        if itens:
            totais = calcular_totais(itens)
            st.markdown(
                f"<span style='color:gray'>"
                f"Parciais — Calorias: {totais['kcal']:.0f} kcal | Proteínas: {totais['Proteína']:.1f} g | "
                f"Gorduras: {totais['Gordura']:.1f} g | Carboidratos: {totais['Carboidrato']:.1f} g"
                f"</span>",
                unsafe_allow_html=True,
            )

            for i, (nome, qtd) in enumerate(itens):
                linha = df_alimentos[df_alimentos["Alimento"] == nome].iloc[0]
                kcal = linha["kcal"] * qtd / 100
                prot = linha["Proteína"] * qtd / 100
                gord = linha["Gordura"] * qtd / 100
                carb = linha["Carboidrato"] * qtd / 100
                cols = st.columns([3, 1, 1, 1, 1, 1])
                cols[0].write(nome)
                cols[1].write(qtd)
                cols[2].write(f"{kcal:.2f}")
                cols[3].write(f"{prot:.2f}")
                cols[4].write(f"{gord:.2f}")
                cols[5].write(f"{carb:.2f}")
                if cols[5].button("❌", key=f"{nome_refeicao}_{i}"):
                    st.session_state.refeicoes[dia][nome_refeicao].pop(i)
                    st.experimental_rerun()

            for chave in total_dia:
                total_dia[chave] += totais[chave]

    st.markdown("## Totais do dia")
    st.markdown(
        f"**Calorias:** {total_dia['kcal']:.0f} kcal | "
        f"**Proteínas:** {total_dia['Proteína']:.1f} g | "
        f"**Gorduras:** {total_dia['Gordura']:.1f} g | "
        f"**Carboidratos:** {total_dia['Carboidrato']:.1f} g"
    )
else:
    st.warning("Nenhum alimento registrado para essa data.")
