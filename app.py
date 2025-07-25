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

# Função para somar os nutrientes de um DataFrame
def somar_nutrientes(df):
    return df[["Kcal", "Proteina", "Gordura", "Carboidrato"]].sum()

# Início da aplicação Streamlit
st.title("📒 Registro Alimentar Diário")

# Carregar base de dados dos alimentos
df_alimentos = carregar_tabela_alimentos()

# Sessão de estado para armazenar o consumo do dia
if "refeicoes" not in st.session_state:
    st.session_state.refeicoes = {}

refeicao = st.selectbox("Selecione a refeição", ["Café da manhã", "Almoço", "Jantar", "Lanche"])

# Entrada de alimento
entrada = st.text_input("Digite o nome do alimento (ex: arroz, feijao, frango):").strip().lower()

# Buscar alimentos contendo o termo digitado
resultado = df_alimentos[df_alimentos["Alimento"].str.contains(entrada, case=False, na=False)]

if not resultado.empty:
    opcoes = resultado["Alimento"].unique().tolist()
    alimento_selecionado = st.selectbox("Selecione o alimento desejado:", opcoes)
    alimento_escolhido = resultado[resultado["Alimento"] == alimento_selecionado].iloc[0]
    
    quantidade = st.number_input("Quantidade consumida (em gramas)", min_value=0.0, value=100.0, step=10.0)

    if st.button("Adicionar alimento"):
        dados = alimento_escolhido.copy()
        fator = quantidade / 100.0
        dados[["Kcal", "Proteina", "Gordura", "Carboidrato"]] *= fator
        dados["Quantidade (g)"] = quantidade
        dados["Horário"] = datetime.now().strftime("%H:%M")

        if refeicao not in st.session_state.refeicoes:
            st.session_state.refeicoes[refeicao] = pd.DataFrame()

        st.session_state.refeicoes[refeicao] = pd.concat(
            [st.session_state.refeicoes[refeicao], pd.DataFrame([dados])],
            ignore_index=True
        )

# Mostrar resumo do dia
st.subheader("Resumo do dia")

total_df = pd.DataFrame()
for refeicao, df in st.session_state.refeicoes.items():
    if df.empty:
        continue

    st.markdown(f"🍽️ **{refeicao}**")

    colunas_desejadas = ["Alimento", "Quantidade (g)", "Kcal", "Proteina", "Gordura", "Carboidrato"]
    colunas_existentes = [col for col in colunas_desejadas if col in df.columns]
    df_exibir = df[colunas_existentes].copy().reset_index(drop=True)

    for i, row in df_exibir.iterrows():
        cols = st.columns([5, 2, 2, 2, 2, 2, 1])
        cols[0].write(row["Alimento"])
        cols[1].write(f"{row['Quantidade (g)']:.0f}")
        cols[2].write(f"{row['Kcal']:.2f}")
        cols[3].write(f"{row['Proteina']:.2f}")
        cols[4].write(f"{row['Gordura']:.2f}")
        cols[5].write(f"{row['Carboidrato']:.2f}")
        if cols[6].button("❌", key=f"{refeicao}_{i}"):
            st.session_state.refeicoes[refeicao] = df.drop(index=i).reset_index(drop=True)
            st.rerun()

    total_df = pd.concat([total_df, df], ignore_index=True)

# Somatório geral
if not total_df.empty:
    st.markdown("### Totais do dia")
    totais = somar_nutrientes(total_df)
    st.write(f"**Calorias:** {totais['Kcal']:.0f} kcal | **Proteínas:** {totais['Proteina']:.1f} g | **Gorduras:** {totais['Gordura']:.1f} g | **Carboidratos:** {totais['Carboidrato']:.1f} g")

    # Exportar como CSV
    if st.download_button("📁 Baixar CSV do dia", total_df.to_csv(index=False).encode("utf-8"), file_name="registro_alimentar.csv"):
        st.success("Exportado com sucesso!")
else:
    st.info("Nenhum alimento registrado ainda.")
