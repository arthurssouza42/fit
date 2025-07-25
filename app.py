
import streamlit as st
import pandas as pd

# Carregando os dados da TACO
@st.cache_data
def carregar_dados():
    return pd.read_csv("alimentos.csv", sep=";")

taco = carregar_dados()

# Metas diárias iniciais (editáveis)
st.sidebar.title("Metas Diárias")
kcal_meta = st.sidebar.number_input("Calorias (kcal)", value=2670)
prot_meta = st.sidebar.number_input("Proteínas (g)", value=210)
carb_meta = st.sidebar.number_input("Carboidratos (g)", value=300)
gord_meta = st.sidebar.number_input("Gorduras (g)", value=70)

st.title("Registro Alimentar")

# Escolher alimento
alimento = st.selectbox("Escolha o alimento:", taco["Alimento"])
quantidade = st.number_input("Quantidade (g)", min_value=0.0, step=10.0)

if st.button("Adicionar alimento"):
    if "refeicao" not in st.session_state:
        st.session_state.refeicao = []
    info = taco[taco["Alimento"] == alimento].iloc[0]
    fator = quantidade / 100
    entrada = {
        "Alimento": alimento,
        "Quantidade (g)": quantidade,
        "Kcal": round(info["Energia (kcal)"] * fator, 2),
        "Proteína (g)": round(info["Proteína (g)"] * fator, 2),
        "Carboidrato (g)": round(info["Carboidrato (g)"] * fator, 2),
        "Lipídeo (g)": round(info["Lipídeo (g)"] * fator, 2),
    }
    st.session_state.refeicao.append(entrada)

# Mostrar refeições
if "refeicao" in st.session_state and st.session_state.refeicao:
    st.subheader("Consumo Diário")
    df_refeicao = pd.DataFrame(st.session_state.refeicao)
    st.dataframe(df_refeicao)

    totais = df_refeicao[["Kcal", "Proteína (g)", "Carboidrato (g)", "Lipídeo (g)"]].sum()
    st.markdown(f"**Totais**")
    st.write(totais)

    st.markdown("**Comparação com a Meta:**")
    st.progress(min(totais["Kcal"] / kcal_meta, 1.0))
    st.progress(min(totais["Proteína (g)"] / prot_meta, 1.0))
    st.progress(min(totais["Carboidrato (g)"] / carb_meta, 1.0))
    st.progress(min(totais["Lipídeo (g)"] / gord_meta, 1.0))

st.sidebar.title("Registro de Treino")
atividade = st.sidebar.text_input("Descrição da atividade")
tempo = st.sidebar.number_input("Duração (min)", min_value=0)

if st.sidebar.button("Adicionar treino"):
    if "treinos" not in st.session_state:
        st.session_state.treinos = []
    st.session_state.treinos.append({"Atividade": atividade, "Tempo (min)": tempo})

if "treinos" in st.session_state and st.session_state.treinos:
    st.sidebar.subheader("Treinos do dia")
    st.sidebar.dataframe(pd.DataFrame(st.session_state.treinos))
