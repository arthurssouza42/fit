import streamlit as st
import pandas as pd
from difflib import get_close_matches

# Carregar a tabela TACO
taco = pd.read_csv("alimentos.csv")

# Corrigir nomes de colunas se houver espaços ou caracteres invisíveis
taco.columns = taco.columns.str.strip()

# Interface do app
st.set_page_config(page_title="Registro Alimentar", layout="centered")
st.title("🍽️ Registro Alimentar")

# Campo de busca
busca = st.text_input("Digite o nome de um alimento:")

if busca:
    nomes_alimentos = taco["Descrição dos alimentos"].dropna().astype(str).tolist()
    correspondencias = get_close_matches(busca, nomes_alimentos, n=5, cutoff=0.3)

    if not correspondencias:
        st.warning("Nenhum alimento encontrado.")
    else:
        alimento_escolhido = st.selectbox("Selecione o alimento encontrado:", correspondencias)

        if alimento_escolhido:
            dados = taco[taco["Descrição dos alimentos"] == alimento_escolhido].iloc[0]

            st.subheader("📊 Informações Nutricionais por 100g")

            # Mostrar os dados de forma estilizada
            st.markdown("---")

            def show_row(label, valor, unidade="g"):
                if pd.isna(valor): return
                st.markdown(f"""
                <div style='display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #444;'>
                    <span style='font-weight: bold;'>{label}</span>
                    <span>{valor} {unidade}</span>
                </div>
                """, unsafe_allow_html=True)

            # Exibição estilo rótulo
            show_row("Calorias", dados["Energia..kcal."], "kcal")
            show_row("Carboidratos", dados["Carboidrato..g."], "g")
            show_row("Açúcares", "-", "g")  # Não disponível na TACO
            show_row("Proteínas", dados["Proteína..g."], "g")
            show_row("Gorduras Totais", dados["Lipídeos..g."], "g")
            show_row("Colesterol", dados["Colesterol..mg."], "mg")
            show_row("Fibras", dados["Fibra.Alimentar..g."], "g")
            show_row("Sódio", dados["Sódio..mg."], "mg")
            show_row("Potássio", dados["Potássio..mg."], "mg")
