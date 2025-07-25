
import streamlit as st
import pandas as pd
import unicodedata
from datetime import datetime
import os

@st.cache_data
def carregar_tabela_alimentos():
    df = pd.read_csv("alimentos.csv", sep=",", quotechar='"')
    df["Descrição dos alimentos"] = df["Descrição dos alimentos"].astype(str).str.strip()
    return df

def normalizar(texto):
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').lower()

# Inicialização da sessão
if "registros" not in st.session_state:
    st.session_state.registros = []

st.title("🍽️ Registro Alimentar")

df_alimentos = carregar_tabela_alimentos()

# Entrada do alimento
nome_alimento = st.text_input("Digite o nome de um alimento:", "")

# Filtro inteligente
if nome_alimento:
    nome_proc = normalizar(nome_alimento)
    opcoes = df_alimentos[df_alimentos["Descrição dos alimentos"].apply(lambda x: nome_proc in normalizar(x))]
    lista_alimentos = opcoes["Descrição dos alimentos"].tolist()
else:
    lista_alimentos = []

# Dropdown
alimento_selecionado = st.selectbox("Selecione o alimento encontrado:", lista_alimentos) if lista_alimentos else None

# Quantidade
quantidade = st.number_input("Quantidade consumida (em gramas):", min_value=1, step=1)

# Botão de adicionar
if st.button("Registrar alimento") and alimento_selecionado:
    dados = df_alimentos[df_alimentos["Descrição dos alimentos"] == alimento_selecionado].iloc[0]
    fator = quantidade / 100
    registro = {
        "Data": datetime.now().strftime("%Y-%m-%d"),
        "Alimento": alimento_selecionado,
        "Quantidade (g)": quantidade,
        "Kcal": round(dados["Energia..kcal."] * fator, 2),
        "Proteína (g)": round(dados["Proteína..g."] * fator, 2),
        "Carboidrato (g)": round(dados["Carboidrato..g."] * fator, 2),
        "Gordura (g)": round(dados["Lipídeos..g."] * fator, 2),
    }
    st.session_state.registros.append(registro)
    st.success(f"{alimento_selecionado} registrado com sucesso!")

# Mostrar registros
st.subheader("Alimentos registrados no dia")
df_registros = pd.DataFrame(st.session_state.registros)

if not df_registros.empty:
    st.dataframe(df_registros)

    # Exclusão
    indices_para_remover = st.multiselect("Selecione as linhas para excluir:", df_registros.index.tolist())
    if st.button("Excluir selecionados"):
        st.session_state.registros = [reg for i, reg in enumerate(st.session_state.registros) if i not in indices_para_remover]
        st.success("Itens excluídos.")
        st.experimental_rerun()

    # Exportar CSV
    csv = df_registros.to_csv(index=False).encode('utf-8')
    st.download_button("📤 Exportar CSV", data=csv, file_name="registro_alimentar.csv", mime="text/csv")

    # Totais
    st.markdown("### Totais do dia")
    totais = df_registros[["Kcal", "Proteína (g)", "Carboidrato (g)", "Gordura (g)"]].sum().round(2)
    st.write(totais)
else:
    st.info("Nenhum alimento registrado ainda.")
