
import streamlit as st
import pandas as pd
from pathlib import Path
from unidecode import unidecode

# Caminhos dos arquivos
ARQUIVO_ALIMENTOS = "alimentos.csv"
ARQUIVO_REGISTRO = "registros.csv"

# ---------------- FUNÇÕES AUXILIARES ----------------

@st.cache_data
def carregar_tabela_alimentos():
    df = pd.read_csv(ARQUIVO_ALIMENTOS)
    df['Alimento'] = df['Descrição'].apply(lambda x: unidecode(x).lower())
    return df

def carregar_registros():
    if Path(ARQUIVO_REGISTRO).exists():
        return pd.read_csv(ARQUIVO_REGISTRO)
    return pd.DataFrame(columns=["Data", "Alimento", "Quantidade (g)", "Kcal", "Proteína (g)", "Carboidrato (g)", "Gordura (g)"])

def salvar_registros(df):
    df.to_csv(ARQUIVO_REGISTRO, index=False)

def buscar_alimentos(texto, df_alimentos):
    texto = unidecode(texto).lower()
    return df_alimentos[df_alimentos['Alimento'].str.contains(texto)]

# ---------------- INTERFACE STREAMLIT ----------------

st.set_page_config(page_title="Registro Alimentar", layout="wide")
st.title("📋 Registro Alimentar Diário")

# Entrada do alimento
df_alimentos = carregar_tabela_alimentos()
df_registro = carregar_registros()

with st.form("form_alimento"):
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        nome_input = st.text_input("Buscar alimento", "")
    resultados = buscar_alimentos(nome_input, df_alimentos)
    alimento_selecionado = None
    if not resultados.empty:
        alimento_selecionado = st.selectbox("Selecione o alimento:", resultados["Descrição"].values)
    with col2:
        quantidade = st.number_input("Quantidade (g)", min_value=0.0, step=10.0)
    with col3:
        data = st.date_input("Data", pd.Timestamp.today())

    submitted = st.form_submit_button("Adicionar alimento")

if submitted and alimento_selecionado:
    info = df_alimentos[df_alimentos["Descrição"] == alimento_selecionado].iloc[0]
    fator = quantidade / 100
    nova_linha = {
        "Data": data.strftime("%Y-%m-%d"),
        "Alimento": alimento_selecionado,
        "Quantidade (g)": quantidade,
        "Kcal": round(info["Energia (kcal)"] * fator, 1),
        "Proteína (g)": round(info["Proteína (g)"] * fator, 2),
        "Carboidrato (g)": round(info["Carboidrato (g)"] * fator, 2),
        "Gordura (g)": round(info["Lipídeos (g)"] * fator, 2)
    }
    df_registro = pd.concat([df_registro, pd.DataFrame([nova_linha])], ignore_index=True)
    salvar_registros(df_registro)
    st.success("Alimento registrado com sucesso!")
    st.rerun()

# ---------------- REGISTROS EXISTENTES ----------------

st.subheader("📆 Alimentos registrados no dia")
df_registro_filtrado = df_registro[df_registro["Data"] == pd.Timestamp.today().strftime("%Y-%m-%d")]
st.dataframe(df_registro_filtrado)

# Exclusão
st.subheader("🗑️ Remover alimento registrado")
nomes_unicos = df_registro_filtrado["Alimento"].unique().tolist()
selecionado = st.multiselect("Selecione os alimentos para excluir:", nomes_unicos)

if st.button("Excluir selecionados") and selecionado:
    df_registro = df_registro[~((df_registro["Data"] == pd.Timestamp.today().strftime("%Y-%m-%d")) &
                                (df_registro["Alimento"].isin(selecionado)))]
    salvar_registros(df_registro)
    st.success("Itens excluídos.")
    st.rerun()

# Exportar
st.download_button(
    label="📥 Exportar todos os registros para CSV",
    data=df_registro.to_csv(index=False).encode("utf-8"),
    file_name="registros.csv",
    mime="text/csv"
)
