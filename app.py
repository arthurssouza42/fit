import streamlit as st
import pandas as pd
import unicodedata
from datetime import datetime
import os
import uuid
from typing import Dict, Optional, Tuple

# Configurações globais
CONFIG = {
    'CACHE_TTL': 3600,
    'DEFAULT_QUANTITY': 100.0,
    'QUANTITY_STEP': 10.0,
    'PORTION_STEP': 0.5,
    'MAX_QUANTITY': 10000.0,
    'MIN_QUANTITY': 0.1
}

# Função para carregar e processar a tabela de alimentos
@st.cache_data(ttl=CONFIG['CACHE_TTL'])
def carregar_tabela_alimentos(csv_path: str = "alimentos.csv") -> pd.DataFrame:
    """Carrega a tabela de alimentos com tratamento de erros."""
    # Validação de segurança para path traversal
    if not os.path.basename(csv_path) == csv_path or '..' in csv_path:
        raise ValueError("Caminho de arquivo inválido")
    
    try:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Arquivo {csv_path} não encontrado")
            
        df = pd.read_csv(csv_path)
        
        # Verificar se as colunas essenciais existem
        required_columns = ["Descrição dos alimentos", "Energia..kcal.", "Proteína..g.", 
                          "Lipídeos..g.", "Carboidrato..g."]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colunas obrigatórias ausentes: {missing_columns}")
        
        # Processar normalização de texto
        df["Alimento"] = df["Descrição dos alimentos"].apply(
            lambda x: unicodedata.normalize("NFKD", str(x))
            .encode("ASCII", "ignore")
            .decode("utf-8")
            .lower()
        )
        
        # Selecionar colunas
        columns_to_select = [
            "Alimento",
            "Energia..kcal.",
            "Proteína..g.",
            "Lipídeos..g.",
            "Carboidrato..g.",
        ]
        
        if "gramas_por_porcao" in df.columns:
            columns_to_select.append("gramas_por_porcao")
            
        df = df[columns_to_select]
        
        # Renomear colunas
        column_mapping = {
            "Alimento": "Alimento",
            "Energia..kcal.": "Kcal",
            "Proteína..g.": "Proteina",
            "Lipídeos..g.": "Gordura",
            "Carboidrato..g.": "Carboidrato",
        }
        
        if "gramas_por_porcao" in df.columns:
            column_mapping["gramas_por_porcao"] = "GramasPorPorcao"
            
        df = df.rename(columns=column_mapping)
        
        # Limpar dados numéricos
        numeric_columns = ["Kcal", "Proteina", "Gordura", "Carboidrato"]
        if "GramasPorPorcao" in df.columns:
            numeric_columns.append("GramasPorPorcao")
            
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(0)
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar arquivo de alimentos: {str(e)}")
        return pd.DataFrame()

# Função para validar entrada numérica
def validar_quantidade(quantidade: float) -> Tuple[bool, str]:
    """Valida se a quantidade está dentro dos limites aceitáveis."""
    if quantidade < CONFIG['MIN_QUANTITY']:
        return False, f"Quantidade deve ser maior que {CONFIG['MIN_QUANTITY']}g"
    if quantidade > CONFIG['MAX_QUANTITY']:
        return False, f"Quantidade deve ser menor que {CONFIG['MAX_QUANTITY']}g"
    return True, ""

# Função para somar os nutrientes de um DataFrame
def somar_nutrientes(df: pd.DataFrame) -> pd.Series:
    """Soma os nutrientes de um DataFrame com tratamento de erros."""
    if df.empty:
        return pd.Series({"Kcal": 0, "Proteina": 0, "Gordura": 0, "Carboidrato": 0})
    
    nutrient_columns = ["Kcal", "Proteina", "Gordura", "Carboidrato"]
    available_columns = [col for col in nutrient_columns if col in df.columns]
    
    if not available_columns:
        return pd.Series({"Kcal": 0, "Proteina": 0, "Gordura": 0, "Carboidrato": 0})
    
    return df[available_columns].sum()

# Caminho para armazenar os registros permanentemente
REGISTRO_PATH = "registros.csv"

def preparar_dados_para_export(registros: Dict[str, Dict[str, pd.DataFrame]]) -> pd.DataFrame:
    """Função unificada para preparar dados para exportação."""
    df_export = pd.DataFrame()
    
    for dia, dados_refeicoes in registros.items():
        for refeicao, df in dados_refeicoes.items():
            if df.empty:
                continue
            df_temp = df.copy()
            df_temp["Data"] = dia
            df_temp["Refeicao"] = refeicao
            df_export = pd.concat([df_export, df_temp], ignore_index=True)
    
    return df_export

def carregar_registros(path: str = REGISTRO_PATH) -> Dict[str, Dict[str, pd.DataFrame]]:
    """Carrega registros salvos em disco para o formato usado em sessão."""
    if not os.path.exists(path):
        return {}

    try:
        df = pd.read_csv(path)
        registros: Dict[str, Dict[str, pd.DataFrame]] = {}
        
        for (dia, refeicao), grupo in df.groupby(["Data", "Refeicao"]):
            grupo = grupo.drop(columns=["Data", "Refeicao"]).reset_index(drop=True)
            registros.setdefault(dia, {})[refeicao] = grupo
            
        return registros
        
    except Exception as e:
        st.error(f"Erro ao carregar registros: {str(e)}")
        return {}

def salvar_registros(registros: Dict[str, Dict[str, pd.DataFrame]], path: str = REGISTRO_PATH) -> bool:
    """Salva todos os registros da sessão em disco."""
    try:
        df_export = preparar_dados_para_export(registros)
        
        if df_export.empty:
            if os.path.exists(path):
                os.remove(path)
        else:
            df_export.to_csv(path, index=False)
        return True
        
    except Exception as e:
        st.error(f"Erro ao salvar registros: {str(e)}")
        return False

# Função para gerar ID único para cada item
def gerar_id_unico() -> str:
    """Gera um ID único para cada item de alimento."""
    return str(uuid.uuid4())[:8]

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
df_alimentos = carregar_tabela_alimentos(csv_path)

if df_alimentos.empty:
    st.error("Não foi possível carregar a base de dados de alimentos.")
    st.stop()

# MUDANÇA: Lista de refeições na ordem específica solicitada
opcoes_refeicoes = ["Café da manhã", "Almoço", "Lanche da tarde", "Jantar", "Lanche noturno"]

refeicao = st.selectbox("Selecione a refeição", opcoes_refeicoes)

# Input com validação
entrada = st.text_input("Digite o nome do alimento (ex: arroz, feijao, frango):").strip().lower()

# Sanitizar entrada para evitar problemas
entrada_sanitizada = ''.join(c for c in entrada if c.isalnum() or c.isspace())

if entrada_sanitizada:
    try:
        resultado = df_alimentos[df_alimentos["Alimento"].str.contains(
            entrada_sanitizada, case=False, na=False, regex=False)]
    except Exception as e:
        st.error(f"Erro na busca: {str(e)}")
        resultado = pd.DataFrame()
else:
    resultado = pd.DataFrame()

if not resultado.empty:
    opcoes = resultado["Alimento"].unique().tolist()
    alimento_selecionado = st.selectbox("Selecione o alimento desejado:", opcoes)
    alimento_escolhido = resultado[resultado["Alimento"] == alimento_selecionado].iloc[0]

    # Verificar se tem informação de porções
    tem_porcoes = "GramasPorPorcao" in alimento_escolhido and pd.notna(alimento_escolhido.get("GramasPorPorcao"))
    gramas_por_porcao = alimento_escolhido.get("GramasPorPorcao", None) if tem_porcoes else None
    
    porcoes = None
    quantidade = CONFIG['DEFAULT_QUANTITY']
    
    if tem_porcoes and gramas_por_porcao > 0:
        unidade = st.radio(
            "Escolha a unidade",
            ["gramas", "porções"],
            horizontal=True,
        )
        if unidade == "gramas":
            quantidade = st.number_input(
                "Quantidade consumida (g)",
                min_value=CONFIG['MIN_QUANTITY'],
                max_value=CONFIG['MAX_QUANTITY'],
                value=float(gramas_por_porcao),
                step=CONFIG['QUANTITY_STEP'],
            )
            porcoes = quantidade / gramas_por_porcao if gramas_por_porcao else None
        else:
            porcoes = st.number_input(
                f"Porções ({gramas_por_porcao:g} g)",
                min_value=CONFIG['MIN_QUANTITY'] / gramas_por_porcao,
                max_value=CONFIG['MAX_QUANTITY'] / gramas_por_porcao,
                value=1.0,
                step=CONFIG['PORTION_STEP'],
            )
            quantidade = porcoes * gramas_por_porcao
    else:
        quantidade = st.number_input(
            "Quantidade consumida (g)",
            min_value=CONFIG['MIN_QUANTITY'],
            max_value=CONFIG['MAX_QUANTITY'],
            value=CONFIG['DEFAULT_QUANTITY'],
            step=CONFIG['QUANTITY_STEP'],
        )

    # Validar quantidade
    quantidade_valida, mensagem_erro = validar_quantidade(quantidade)
    if not quantidade_valida:
        st.error(mensagem_erro)
    else:
        if st.button("Adicionar alimento"):
            try:
                dados = alimento_escolhido.copy()
                fator = quantidade / 100.0
                dados[["Kcal", "Proteina", "Gordura", "Carboidrato"]] *= fator
                dados["Quantidade (g)"] = quantidade
                dados["Porcoes"] = porcoes
                dados["Horário"] = datetime.now().strftime("%H:%M")
                dados["Data"] = data_str
                dados["Refeicao"] = refeicao
                dados["ID"] = gerar_id_unico()

                if refeicao not in refeicoes:
                    refeicoes[refeicao] = pd.DataFrame()

                novo_item_df = pd.DataFrame([dados])
                refeicoes[refeicao] = pd.concat([refeicoes[refeicao], novo_item_df], ignore_index=True)
                
                if salvar_registros(st.session_state.refeicoes_por_dia):
                    st.success("Alimento adicionado com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao salvar. Tente novamente.")
                    
            except Exception as e:
                st.error(f"Erro ao adicionar alimento: {str(e)}")

# MUDANÇA PRINCIPAL: Mostrar resumo na ordem específica
st.subheader(f"Resumo do dia ({data_str})")

# Definir ordem específica das refeições
ordem_refeicoes = ["Café da manhã", "Almoço", "Lanche da tarde", "Jantar", "Lanche noturno"]

# Mapear emojis para cada refeição
emojis_refeicoes = {
    "Café da manhã": "☕",
    "Almoço": "🍽️", 
    "Lanche da tarde": "🍎",
    "Jantar": "🌙",
    "Lanche noturno": "🌃"
}

total_df = pd.DataFrame()

# Iterar na ordem específica
for refeicao_nome in ordem_refeicoes:
    if refeicao_nome not in refeicoes or refeicoes[refeicao_nome].empty:
        continue
        
    df = refeicoes[refeicao_nome]

    # Calcular totais parciais
    totais_parciais = somar_nutrientes(df)
    resumo_macros = (
        f"**Calorias:** {totais_parciais['Kcal']:.0f} kcal | "
        f"**Proteínas:** {totais_parciais['Proteina']:.1f} g | "
        f"**Gorduras:** {totais_parciais['Gordura']:.1f} g | "
        f"**Carboidratos:** {totais_parciais['Carboidrato']:.1f} g"
    )

    # Título da refeição + resumo parcial com emoji específico
    emoji = emojis_refeicoes.get(refeicao_nome, "🍽️")
    st.markdown(f"{emoji} **{refeicao_nome}**\n\n{resumo_macros}")

    colunas = [
        "Alimento",
        "Quantidade (g)",
        "Porcoes",
        "Kcal",
        "Proteina",
        "Gordura",
        "Carboidrato",
    ]
    
    # Garantir que as colunas existem
    if "Porcoes" not in df.columns:
        df["Porcoes"] = pd.NA
    if "ID" not in df.columns:
        df["ID"] = [gerar_id_unico() for _ in range(len(df))]
        
    df_exibir = df[colunas + ["ID"]].copy().reset_index(drop=True)

    for i, row in df_exibir.iterrows():
        cols = st.columns([5, 2, 2, 2, 2, 2, 2, 1])
        cols[0].write(row["Alimento"])
        cols[1].write(f"{row['Quantidade (g)']:.0f}")
        cols[2].write("" if pd.isna(row["Porcoes"]) else f"{row['Porcoes']:.2f}")
        cols[3].write(f"{row['Kcal']:.1f}")
        cols[4].write(f"{row['Proteina']:.1f}")
        cols[5].write(f"{row['Gordura']:.1f}")
        cols[6].write(f"{row['Carboidrato']:.1f}")
        
        # Usar ID único para o botão de deleção
        item_id = row.get("ID", f"{data_str}_{refeicao_nome}_{i}")
        if cols[7].button("🗑️", key=f"del_{item_id}", type="secondary", help="Deletar item"):
            # Confirmar deleção
            if f"confirm_delete_{item_id}" not in st.session_state:
                st.session_state[f"confirm_delete_{item_id}"] = True
                st.warning("Clique novamente para confirmar a exclusão")
                st.rerun()
            else:
                try:
                    refeicoes[refeicao_nome] = df.drop(index=i).reset_index(drop=True)
                    salvar_registros(st.session_state.refeicoes_por_dia)
                    del st.session_state[f"confirm_delete_{item_id}"]
                    st.success("Item removido!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao remover item: {str(e)}")

    total_df = pd.concat([total_df, df], ignore_index=True)

# Totais do dia
if not total_df.empty:
    st.markdown("### 📊 Totais do dia")
    totais = somar_nutrientes(total_df)
    
    # Mostrar em formato mais visual
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Calorias", f"{totais['Kcal']:.0f} kcal")
    with col2:
        st.metric("Proteínas", f"{totais['Proteina']:.1f} g")
    with col3:
        st.metric("Gorduras", f"{totais['Gordura']:.1f} g")
    with col4:
        st.metric("Carboidratos", f"{totais['Carboidrato']:.1f} g")

# Exportar todos os dados
st.subheader("📦 Exportar todos os registros")

df_export = preparar_dados_para_export(st.session_state.refeicoes_por_dia)

if not df_export.empty:
    st.download_button(
        label="📁 Baixar CSV completo",
        data=df_export.to_csv(index=False).encode("utf-8"),
        file_name=f"registro_alimentar_completo_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
    st.info(f"Total de {len(df_export)} registros disponíveis para download")
else:
    st.info("Nenhum registro encontrado para exportar")
