import streamlit as st
import pandas as pd
import unicodedata
from datetime import datetime

# Função para carregar e processar a tabela de alimentos
@st.cache_data
def carregar_tabela_alimentos():
    df = pd.read_csv("alimentos.csv")
    df["Alimento"] = df["Descrição dos alimentos"].apply(lambda x: unicodedata.normalize("NFKD", str(x)).encode("ASCII", "ignore").decode("utf-8").lower())
    df = df[["Alimento", "Energia..kcal.", "Proteína..g.", "Lipídeos..g.", "Carboidrato..g."]]
    df.columns = ["Alimento", "Kcal", "Proteina", "Gordura", "Carboidrato"]
    return df

# Função para somar os nutrientes
def somar_nutrientes(df):
    return df[["Kcal", "Proteina", "Gordura", "Carboidrato"]].sum()

st.title("📒 Registro Alimentar Diário")

# Inicializar estado
if "dias" not in st.session_state:
    st.session_state.dias = {}

df_alimentos = carregar_tabela_alimentos()

# Escolha da data
data_ref = st.date_input("Selecione o dia", value=datetime.today()).strftime("%Y-%m-%d")

if data_ref not in st.session_state.dias:
    st.session_state.dias[data_ref] = {}

refeicao = st.selectbox("Selecione a refeição", ["Café da manhã", "Almoço", "Jantar", "Lanche"])
entrada = st.text_input("Digite o nome do alimento:").strip().lower()

# Buscar alimentos semelhantes
resultado = df_alimentos[df_alimentos["Alimento"].str.contains(entrada, case=False, na=False)]

if not resultado.empty:
    opcoes = resultado["Alimento"].unique().tolist()
    alimento_selecionado = st.selectbox("Selecione o alimento desejado:", opcoes)
    alimento_escolhido = resultado[resultado["Alimento"] == alimento_selecionado].iloc[0]

    quantidade = st.number_input("Quantidade consumida (g)", min_value=0.0, value=100.0, step=10.0)

    if st.button("Adicionar alimento"):
        dados = alimento_escolhido.copy()
        fator = quantidade / 100.0
        dados[["Kcal", "Proteina", "Gordura", "Carboidrato"]] *= fator
        dados["Quantidade (g)"] = quantidade
        dados["Data"] = data_ref

        if refeicao not in st.session_state.dias[data_ref]:
            st.session_state.dias[data_ref][refeicao] = pd.DataFrame()

        st.session_state.dias[data_ref][refeicao] = pd.concat(
            [st.session_state.dias[data_ref][refeicao], pd.DataFrame([dados])],
            ignore_index=True
        )

# Mostrar dados do dia selecionado
st.subheader(f"🍽️ Resumo de {data_ref}")
total_df = pd.DataFrame()

if data_ref in st.session_state.dias:
    for refeicao, df in st.session_state.dias[data_ref].items():
        if df.empty:
            continue

        st.markdown(f"**{refeicao}**")

        df = df.reset_index(drop=True)
        for i, row in df.iterrows():
            col1, col2 = st.columns([8, 1])
            with col1:
                st.write(f"**{row['Alimento']}** - {row['Quantidade (g)']:.0f}g | {row['Kcal']:.1f} kcal | {row['Proteina']:.1f}g P | {row['Gordura']:.1f}g G | {row['Carboidrato']:.1f}g C")
            with col2:
                if st.button("❌", key=f"{data_ref}_{refeicao}_{i}"):
                    st.session_state.dias[data_ref][refeicao] = df.drop(index=i).reset_index(drop=True)
                    st.rerun()

        total_df = pd.concat([total_df, df], ignore_index=True)

# Totais do dia
if not total_df.empty:
    st.markdown("### Totais do dia")
    totais = somar_nutrientes(total_df)
    st.write(f"**Calorias:** {totais['Kcal']:.0f} kcal | **Proteínas:** {totais['Proteina']:.1f} g | **Gorduras:** {totais['Gordura']:.1f} g | **Carboidratos:** {totais['Carboidrato']:.1f} g")

# Exportar todos os dias como CSV
st.subheader("📁 Exportar registros")
dados_export = pd.DataFrame()
for data, refeicoes in st.session_state.dias.items():
    for ref, df in refeicoes.items():
        df_copy = df.copy()
        df_copy["Refeição"] = ref
        df_copy["Data"] = data
        dados_export = pd.concat([dados_export, df_copy], ignore_index=True)

if not dados_export.empty:
    st.download_button("📦 Baixar CSV com todos os dias", dados_export.to_csv(index=False).encode("utf-8"), file_name="registro_alimentar_completo.csv")
else:
    st.info("Nenhum dado para exportar ainda.")
