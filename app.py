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

# Início do app
st.title("📒 Registro Alimentar Diário")

# Data no formato DD/MM/AAAA
data_input = st.date_input("Selecione a data:", format="DD/MM/YYYY")
data_str = data_input.strftime("%d/%m/%Y")

# Inicializar sessão por data
if "refeicoes_por_dia" not in st.session_state:
    st.session_state.refeicoes_por_dia = {}

if data_str not in st.session_state.refeicoes_por_dia:
    st.session_state.refeicoes_por_dia[data_str] = {}

refeicoes = st.session_state.refeicoes_por_dia[data_str]

# Carregar base de dados
df_alimentos = carregar_tabela_alimentos()

refeicao = st.selectbox("Selecione a refeição", ["Café da manhã", "Almoço", "Jantar", "Lanche"])
entrada = st.text_input("Digite o nome do alimento (ex: arroz, feijao, frango):").strip().lower()

# Usar pesquisa literal para evitar erro ao digitar caracteres especiais
resultado = df_alimentos[df_alimentos["Alimento"].str.contains(entrada, case=False, na=False, regex=False)]

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
        dados["Data"] = data_str
        dados["Refeicao"] = refeicao

        if refeicao not in refeicoes:
            refeicoes[refeicao] = pd.DataFrame()

        refeicoes[refeicao] = pd.concat(
            [refeicoes[refeicao], pd.DataFrame([dados])],
            ignore_index=True
        )
        st.rerun()

# Mostrar resumo
st.subheader(f"Resumo do dia ({data_str})")

total_df = pd.DataFrame()
for refeicao, df in refeicoes.items():
    if df.empty:
        continue

    # Calcular totais parciais
    totais_parciais = somar_nutrientes(df)
    resumo_macros = (
        f"**Calorias:** {totais_parciais['Kcal']:.0f} kcal | "
        f"**Proteínas:** {totais_parciais['Proteina']:.1f} g | "
        f"**Gorduras:** {totais_parciais['Gordura']:.1f} g | "
        f"**Carboidratos:** {totais_parciais['Carboidrato']:.1f} g"
    )

    # Título da refeição + resumo parcial
    st.markdown(f"🍽️ **{refeicao}**\n\n{resumo_macros}")

    colunas = ["Alimento", "Quantidade (g)", "Kcal", "Proteina", "Gordura", "Carboidrato"]
    df_exibir = df[colunas].copy().reset_index(drop=True)

    for i, row in df_exibir.iterrows():
        cols = st.columns([5, 2, 2, 2, 2, 2, 1])
        cols[0].write(row["Alimento"])
        cols[1].write(f"{row['Quantidade (g)']:.0f}")
        cols[2].write(f"{row['Kcal']:.2f}")
        cols[3].write(f"{row['Proteina']:.2f}")
        cols[4].write(f"{row['Gordura']:.2f}")
        cols[5].write(f"{row['Carboidrato']:.2f}")
        if cols[6].button("❌", key=f"{data_str}_{refeicao}_{i}"):
            refeicoes[refeicao] = df.drop(index=i).reset_index(drop=True)
            st.rerun()

    total_df = pd.concat([total_df, df], ignore_index=True)

# Totais do dia
if not total_df.empty:
    st.markdown("### Totais do dia")
    totais = somar_nutrientes(total_df)
    st.write(f"**Calorias:** {totais['Kcal']:.0f} kcal | **Proteínas:** {totais['Proteina']:.1f} g | **Gorduras:** {totais['Gordura']:.1f} g | **Carboidratos:** {totais['Carboidrato']:.1f} g")

# Exportar todos os dados
st.subheader("📦 Exportar todos os registros")

df_export = pd.DataFrame()
for dia, dados_refeicoes in st.session_state.refeicoes_por_dia.items():
    for refeicao, df in dados_refeicoes.items():
        if not df.empty:
            df_temp = df.copy()
            df_temp["Data"] = dia
            df_temp["Refeicao"] = refeicao
            df_export = pd.concat([df_export, df_temp], ignore_index=True)

if not df_export.empty:
    st.download_button(
        label="📁 Baixar CSV completo",
        data=df_export.to_csv(index=False).encode("utf-8"),
        file_name="registro_alimentar_completo.csv"
    )
