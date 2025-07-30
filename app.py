import streamlit as st
import pandas as pd
import unicodedata
from datetime import datetime
import os

# Função para carregar e processar a tabela de alimentos
@st.cache_data(ttl=3600)
def carregar_tabela_alimentos(csv_path: str = "alimentos.csv", file_mtime: float | None = None):
    """Carrega a tabela de alimentos.

    Parameters
    ----------
    csv_path: str
        Caminho para o arquivo CSV.
    file_mtime: float | None
        Momento de modificação do arquivo. Usado para invalidar o cache
        caso o arquivo seja atualizado.
    """
    if file_mtime is None:
        file_mtime = os.path.getmtime(csv_path)

    df = pd.read_csv(csv_path)
    df["Alimento"] = df["Descrição dos alimentos"].apply(
        lambda x: unicodedata.normalize("NFKD", str(x))
        .encode("ASCII", "ignore")
        .decode("utf-8")
        .lower()
    )
    df = df[
        [
            "Alimento",
            "Energia..kcal.",
            "Proteína..g.",
            "Lipídeos..g.",
            "Carboidrato..g.",
            "gramas_por_porcao",
        ]
    ]
    df.columns = [
        "Alimento",
        "Kcal",
        "Proteina",
        "Gordura",
        "Carboidrato",
        "GramasPorPorcao",
    ]
    return df

# Função para somar os nutrientes de um DataFrame
def somar_nutrientes(df):
    return df[["Kcal", "Proteina", "Gordura", "Carboidrato"]].sum()

# Caminho para armazenar os registros permanentemente
REGISTRO_PATH = "registros.csv"


def carregar_registros(path: str = REGISTRO_PATH) -> dict:
    """Carrega registros salvos em disco para o formato usado em sessao."""
    if not os.path.exists(path):
        return {}

    df = pd.read_csv(path)
    registros: dict[str, dict[str, pd.DataFrame]] = {}
    for (dia, refeicao), grupo in df.groupby(["Data", "Refeicao"]):
        grupo = grupo.drop(columns=["Data", "Refeicao"]).reset_index(drop=True)
        registros.setdefault(dia, {})[refeicao] = grupo
    return registros


def salvar_registros(registros: dict[str, dict[str, pd.DataFrame]], path: str = REGISTRO_PATH) -> None:
    """Salva todos os registros da sessao em disco."""
    df_export = pd.DataFrame()
    for dia, dados_refeicoes in registros.items():
        for refeicao, df in dados_refeicoes.items():
            if df.empty:
                continue
            df_temp = df.copy()
            df_temp["Data"] = dia
            df_temp["Refeicao"] = refeicao
            df_export = pd.concat([df_export, df_temp], ignore_index=True)

    if df_export.empty:
        if os.path.exists(path):
            os.remove(path)
    else:
        df_export.to_csv(path, index=False)
        
# Início do app
st.title("📒 Registro Alimentar Diário")

# Data no formato DD/MM/AAAA em um campo mais compacto
col_data, _ = st.columns([1, 5])
with col_data:
    data_input = st.date_input("Data", format="DD/MM/YYYY")
data_str = data_input.strftime("%d/%m/%Y")

# Inicializar sessão por data
if "refeicoes_por_dia" not in st.session_state:
    st.session_state.refeicoes_por_dia = carregar_registros()

if data_str not in st.session_state.refeicoes_por_dia:
    st.session_state.refeicoes_por_dia[data_str] = {}

refeicoes = st.session_state.refeicoes_por_dia[data_str]

# Carregar base de dados
csv_path = "alimentos.csv"
df_alimentos = carregar_tabela_alimentos(csv_path, os.path.getmtime(csv_path))

refeicao = st.selectbox("Selecione a refeição", ["Café da manhã", "Almoço", "Jantar", "Lanche"])
entrada = st.text_input("Digite o nome do alimento (ex: arroz, feijao, frango):").strip().lower()

# Usar pesquisa literal para evitar erro ao digitar caracteres especiais
resultado = df_alimentos[df_alimentos["Alimento"].str.contains(entrada, case=False, na=False, regex=False)]

if not resultado.empty:
    opcoes = resultado["Alimento"].unique().tolist()
    alimento_selecionado = st.selectbox("Selecione o alimento desejado:", opcoes)
    alimento_escolhido = resultado[resultado["Alimento"] == alimento_selecionado].iloc[0]

    gramas_por_porcao = alimento_escolhido.get("GramasPorPorcao")
    porcoes = None
    if pd.notna(gramas_por_porcao):
        unidade = st.radio(
            "Escolha a unidade",
            ["gramas", "porções"],
            horizontal=True,
        )
        if unidade == "gramas":
            quantidade = st.number_input(
                "Quantidade consumida (g)",
                min_value=0.0,
                value=float(gramas_por_porcao),
                step=10.0,
            )
            porcoes = quantidade / gramas_por_porcao if gramas_por_porcao else None
        else:
            porcoes = st.number_input(
                "Quantidade consumida (porções)",
                min_value=0.0,
                value=1.0,
                step=0.5,
            )
            quantidade = porcoes * gramas_por_porcao
    else:
        quantidade = st.number_input(
            "Quantidade consumida (g)",
            min_value=0.0,
            value=100.0,
            step=10.0,
        )

    if st.button("Adicionar alimento"):
        dados = alimento_escolhido.copy()
        fator = quantidade / 100.0
        dados[["Kcal", "Proteina", "Gordura", "Carboidrato"]] *= fator
        dados["Quantidade (g)"] = quantidade
        dados["Porcoes"] = porcoes
        dados["Horário"] = datetime.now().strftime("%H:%M")
        dados["Data"] = data_str
        dados["Refeicao"] = refeicao

        if refeicao not in refeicoes:
            refeicoes[refeicao] = pd.DataFrame()

        refeicoes[refeicao] = pd.concat(
            [refeicoes[refeicao], pd.DataFrame([dados])],
            ignore_index=True
        )
        salvar_registros(st.session_state.refeicoes_por_dia)
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

    colunas = [
        "Alimento",
        "Quantidade (g)",
        "Porcoes",
        "Kcal",
        "Proteina",
        "Gordura",
        "Carboidrato",
    ]
    if "Porcoes" not in df:
        df["Porcoes"] = pd.NA
    df_exibir = df[colunas].copy().reset_index(drop=True)

    for i, row in df_exibir.iterrows():
        cols = st.columns([5, 2, 2, 2, 2, 2, 2, 0.5])
        cols[0].write(row["Alimento"])
        cols[1].write(f"{row['Quantidade (g)']:.0f}")
        cols[2].write("" if pd.isna(row["Porcoes"]) else f"{row['Porcoes']:.2f}")
        cols[3].write(f"{row['Kcal']:.2f}")
        cols[4].write(f"{row['Proteina']:.2f}")
        cols[5].write(f"{row['Gordura']:.2f}")
        cols[6].write(f"{row['Carboidrato']:.2f}")
        if cols[7].button("x", key=f"del_{data_str}_{refeicao}_{i}", type="secondary"):
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
