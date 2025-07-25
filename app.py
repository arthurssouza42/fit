import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Registro Alimentar Diário", page_icon="📒", layout="wide")

st.title("📒 Registro Alimentar Diário")

# Função para formatar a data como DD/MM/AAAA
def formatar_data(data):
    return data.strftime("%d/%m/%Y")

# Selecionar data
data_selecionada = st.date_input("Selecione o dia", value=datetime.today())

# Garantir chave para o dia selecionado
data_str = data_selecionada.strftime("%Y-%m-%d")
if "registros" not in st.session_state:
    st.session_state.registros = {}

if data_str not in st.session_state.registros:
    st.session_state.registros[data_str] = {}

# Adicionar alimento
with st.form(key="formulario"):
    refeicao = st.selectbox("Refeição", ["Café da manhã", "Almoço", "Jantar", "Lanche"])
    alimento = st.text_input("Alimento")
    quantidade = st.number_input("Quantidade (g)", min_value=0.0, step=1.0)
    kcal = st.number_input("Kcal", min_value=0.0, step=0.1)
    proteina = st.number_input("Proteína", min_value=0.0, step=0.1)
    gordura = st.number_input("Gordura", min_value=0.0, step=0.1)
    carbo = st.number_input("Carboidrato", min_value=0.0, step=0.1)
    submit = st.form_submit_button("Adicionar alimento")

    if submit:
        entrada = {
            "Alimento": alimento,
            "Quantidade (g)": quantidade,
            "Kcal": kcal,
            "Proteína": proteina,
            "Gordura": gordura,
            "Carboidrato": carbo,
        }
        if refeicao not in st.session_state.registros[data_str]:
            st.session_state.registros[data_str][refeicao] = []
        st.session_state.registros[data_str][refeicao].append(entrada)
        st.success(f"{alimento} adicionado à refeição {refeicao}")

# Mostrar resumo
st.subheader(f"📅 Resumo de {formatar_data(data_selecionada)}")

dados_dia = st.session_state.registros[data_str]
for refeicao, alimentos in dados_dia.items():
    st.markdown(f"### 🍽️ {refeicao}")
    for i, item in enumerate(alimentos):
        col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1, 1, 1, 1, 1, 0.5])
        col1.write(item["Alimento"])
        col2.write(item["Quantidade (g)"])
        col3.write(item["Kcal"])
        col4.write(item["Proteína"])
        col5.write(item["Gordura"])
        col6.write(item["Carboidrato"])
        if col7.button("❌", key=f"{data_str}-{refeicao}-{i}"):
            st.session_state.registros[data_str][refeicao].pop(i)
            st.experimental_rerun()

# Exportar para CSV
if st.button("📤 Exportar tudo para CSV"):
    todos_registros = []
    for data, refeicoes in st.session_state.registros.items():
        for refeicao, itens in refeicoes.items():
            for item in itens:
                entrada = item.copy()
                entrada["Data"] = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
                entrada["Refeição"] = refeicao
                todos_registros.append(entrada)
    df = pd.DataFrame(todos_registros)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Baixar CSV",
        data=csv,
        file_name="registro_alimentar.csv",
        mime="text/csv",
    )
