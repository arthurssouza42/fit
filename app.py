import pandas as pd
import streamlit as st
from datetime import datetime

@st.cache_data
def carregar_tabela_alimentos():
    df = pd.read_csv("alimentos.csv", sep=";")

    # Padronizar colunas: minúsculas, sem espaços e sem acentos
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

    # Renomear para nomes-padrão usados no sistema
    df = df.rename(
        columns={
            "alimento": "Alimento",
            "energiakcal": "kcal",
            "proteina": "Proteína",
            "lipideos": "Gordura",
            "carboidrato": "Carboidrato",
        }
    )

    # Retornar só as colunas esperadas
    df = df[["Alimento", "kcal", "Proteína", "Gordura", "Carboidrato"]]

    return df

df_alimentos = carregar_tabela_alimentos()

# Inicializar sessões
if "refeicoes" not in st.session_state:
    st.session_state.refeicoes = {}

if "data_selecionada" not in st.session_state:
    st.session_state.data_selecionada = datetime.now().strftime("%d/%m/%Y")

st.title("📒 Registro Alimentar Diário")

# Seleção de data
data_input = st.date_input("Selecione o dia", datetime.strptime(st.session_state.data_selecionada, "%d/%m/%Y"))
data_formatada = data_input.strftime("%d/%m/%Y")
st.session_state.data_selecionada = data_formatada

if data_formatada not in st.session_state.refeicoes:
    st.session_state.refeicoes[data_formatada] = {}

# Formulário para adicionar alimentos
with st.form(key="form_alimento"):
    col1, col2 = st.columns(2)
    with col1:
        refeicao = st.text_input("Refeição", value="Almoço")
    with col2:
        alimento_nome = st.selectbox("Alimento", options=df_alimentos["Alimento"].unique())

    quantidade = st.number_input("Quantidade (g ou ml)", min_value=0.0, step=10.0)
    botao_adicionar = st.form_submit_button("Adicionar alimento")

    if botao_adicionar and quantidade > 0:
        alimento_info = df_alimentos[df_alimentos["Alimento"] == alimento_nome].iloc[0]
        alimento_dict = {
            "nome": alimento_info["Alimento"],
            "quantidade": quantidade,
            "kcal": alimento_info["kcal"] * quantidade / 100,
            "Proteína": alimento_info["Proteína"] * quantidade / 100,
            "Gordura": alimento_info["Gordura"] * quantidade / 100,
            "Carboidrato": alimento_info["Carboidrato"] * quantidade / 100
        }
        if refeicao not in st.session_state.refeicoes[data_formatada]:
            st.session_state.refeicoes[data_formatada][refeicao] = []
        st.session_state.refeicoes[data_formatada][refeicao].append(alimento_dict)

# Mostrar dados do dia
st.markdown(f"### 🍽️ Resumo de {data_formatada}")

total_dia = {"kcal": 0, "Proteína": 0, "Gordura": 0, "Carboidrato": 0}

for refeicao, itens in st.session_state.refeicoes[data_formatada].items():
    total_refeicao = {"kcal": 0, "Proteína": 0, "Gordura": 0, "Carboidrato": 0}
    for item in itens:
        total_refeicao["kcal"] += item["kcal"]
        total_refeicao["Proteína"] += item["Proteína"]
        total_refeicao["Gordura"] += item["Gordura"]
        total_refeicao["Carboidrato"] += item["Carboidrato"]

    # Título da refeição com subtotais
    st.markdown(
        f"#### 🍽️ {refeicao} &nbsp;&nbsp;&nbsp;&nbsp;"
        f"<span style='font-size: 0.9em;'>"
        f"**Subtotal:** {round(total_refeicao['kcal'])} kcal | "
        f"Prot: {round(total_refeicao['Proteína'],1)} g | "
        f"Gord: {round(total_refeicao['Gordura'],1)} g | "
        f"Carb: {round(total_refeicao['Carboidrato'],1)} g"
        f"</span>",
        unsafe_allow_html=True
    )

    for i, item in enumerate(itens):
        col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 0.3])
        col1.write(item["nome"])
        col2.write(f"{item['quantidade']:.0f}")
        col3.write(f"{item['kcal']:.2f}")
        col4.write(f"{item['Proteína']:.2f}")
        col5.write(f"{item['Gordura']:.2f}")
        col6.write(f"{item['Carboidrato']:.2f}")
        if col6.button("❌", key=f"del_{refeicao}_{i}_{data_formatada}"):
            st.session_state.refeicoes[data_formatada][refeicao].pop(i)
            st.experimental_rerun()

    # Atualizar totais do dia
    total_dia["kcal"] += total_refeicao["kcal"]
    total_dia["Proteína"] += total_refeicao["Proteína"]
    total_dia["Gordura"] += total_refeicao["Gordura"]
    total_dia["Carboidrato"] += total_refeicao["Carboidrato"]

# Totais do dia
st.markdown("## Totais do dia")
st.markdown(
    f"**Calorias:** {round(total_dia['kcal'])} kcal | "
    f"**Proteínas:** {round(total_dia['Proteína'], 1)} g | "
    f"**Gorduras:** {round(total_dia['Gordura'], 1)} g | "
    f"**Carboidratos:** {round(total_dia['Carboidrato'], 1)} g"
)
