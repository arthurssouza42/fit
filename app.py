
import streamlit as st
import pandas as pd
from datetime import date
from unidecode import unidecode

ARQUIVO_TACO = "alimentos.csv"
ARQUIVO_REGISTRO = "registros.csv"

st.set_page_config(page_title="Registro Alimentar", layout="wide")

# Funções auxiliares
@st.cache_data
def carregar_taco():
    df = pd.read_csv(ARQUIVO_TACO)
    df["Descrição dos alimentos"] = df["Descrição dos alimentos"].astype(str).str.strip()
    return df

def salvar_taco(df):
    df.to_csv(ARQUIVO_REGISTRO, index=False)

def carregar_registros():
    if Path(ARQUIVO_REGISTRO).exists():
        return pd.read_csv(ARQUIVO_REGISTRO)
    return pd.DataFrame(columns=["Data", "Descrição dos alimentos", "Quantidade (g)", "Kcal", "Proteína (g)", "Carboidrato (g)", "Gordura (g)"])

def buscar_alimento(descricao, df_taco):
    descricao = unidecode(descricao.lower())
    return df_taco[df_taco["Descrição dos alimentos"].apply(lambda x: descricao in unidecode(x.lower()))]

# Interface
st.title("Registro Alimentar Diário")

df_taco = carregar_taco()
df = carregar_registros()

# Entrada
st.subheader("Buscar e registrar alimento")
col1, col2 = st.columns([3, 1])

with col1:
    termo_busca = st.text_input("Buscar alimento (ex: arroz integral, feijão, banana)", "")

with col2:
    quantidade = st.number_input("Quantidade (g)", min_value=0.0, step=1.0)

resultado_busca = buscar_alimento(termo_busca, df_taco) if termo_busca else pd.DataFrame()

if not resultado_busca.empty:
    st.dataframe(resultado_busca[["Descrição dos alimentos", "Kcal (100g)", "Proteína (g)", "Carboidrato (g)", "Lipídeos (g)"]].reset_index(drop=True))

    alimento_selecionado = st.selectbox("Selecione o alimento:", resultado_busca["Descrição dos alimentos"].unique())

    if st.button("Adicionar alimento ao dia"):
        alimento_info = resultado_busca[resultado_busca["Descrição dos alimentos"] == alimento_selecionado].iloc[0]

        nova_entrada = {
            "Data": str(date.today()),
            "Descrição dos alimentos": alimento_info["Descrição dos alimentos"],
            "Quantidade (g)": quantidade,
            "Kcal": round(alimento_info["Kcal (100g)"] * quantidade / 100, 2),
            "Proteína (g)": round(alimento_info["Proteína (g)"] * quantidade / 100, 2),
            "Carboidrato (g)": round(alimento_info["Carboidrato (g)"] * quantidade / 100, 2),
            "Gordura (g)": round(alimento_info["Lipídeos (g)"] * quantidade / 100, 2)
        }

        df = pd.concat([df, pd.DataFrame([nova_entrada])], ignore_index=True)
        salvar_taco(df)
        st.success("Alimento registrado com sucesso.")
        st.rerun()

# Exibição dos registros do dia
st.subheader("Alimentos registrados no dia")
hoje = str(date.today())
df_dia = df[df["Data"] == hoje]

if df_dia.empty:
    st.info("Nenhum alimento registrado para hoje.")
else:
    st.dataframe(df_dia)

    # Exclusão por nome
    st.markdown("### Selecionar alimentos para excluir:")
    alimentos_disponiveis = df_dia["Descrição dos alimentos"].unique().tolist()
    alimentos_para_excluir = st.multiselect("Selecione os alimentos para excluir:", alimentos_disponiveis)

    if st.button("Excluir selecionados") and alimentos_para_excluir:
        df = df[~((df["Data"] == hoje) & (df["Descrição dos alimentos"].isin(alimentos_para_excluir)))]
        salvar_taco(df)
        st.success("Itens excluídos.")
        st.rerun()

# Exportar registros
st.subheader("Exportar registros")
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Baixar registros como CSV", data=csv, file_name="registros.csv", mime='text/csv')
